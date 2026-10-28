"""Snapshot agregado para o frontend, restrito ao desenvolvimento.

A geração confere fonte/partições via load_development. A interface lê somente
este snapshot pequeno e verificável; não abre microdados nem calcula métricas do teste.
"""

import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from enem_base.provenance import sha256_file, verify_sha256, write_json
from enem_base.study import StudyConfig, load_development

DIMENSIONS = ("SG_UF_PROVA", "TP_ESCOLA", "TP_SEXO", "IN_TREINEIRO", "Q006")
BIN_WIDTH = 25
MISSING = "__MISSING__"
ASSETS = (
    "agregados.parquet",
    "diagnostico.json",
    "qualidade.json",
    "dicionario.json",
    "resumo_cv.csv",
    "dobras.csv",
)


@dataclass(frozen=True)
class DashboardData:
    manifest: dict
    cube: pd.DataFrame
    eda: dict
    quality: dict
    dictionary: dict
    cv: pd.DataFrame
    folds: pd.DataFrame


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def aggregate_development(frame: pd.DataFrame, target: str) -> pd.DataFrame:
    """Estatísticas aditivas: médias ponderadas, desvio amostral e histograma.

    Os intervalos do histograma são [início, fim), de 25 pontos. Soma e soma
    dos quadrados usam notas originais, nunca centros dos intervalos.
    """
    if frame.empty or not frame.partition.eq("development").all():
        raise ValueError("O painel exige exclusivamente participantes do desenvolvimento.")
    scores = frame[target].to_numpy(dtype=float)
    if not np.isfinite(scores).all() or (scores < 0).any():
        raise ValueError("O alvo do desenvolvimento deve estar observado e ser não negativo.")
    work = frame.loc[:, list(DIMENSIONS)].fillna(MISSING).copy()
    work["score_bin"] = (scores // BIN_WIDTH).astype("int16")
    work["score"] = scores
    work["score_squared"] = scores**2
    work["zero"] = scores == 0
    return (
        work.groupby([*DIMENSIONS, "score_bin"], observed=True, dropna=False)
        .agg(
            count=("score", "size"),
            score_sum=("score", "sum"),
            score_sum_squared=("score_squared", "sum"),
            zeros=("zero", "sum"),
            minimum=("score", "min"),
            maximum=("score", "max"),
        )
        .reset_index()
    )


def filter_cube(cube: pd.DataFrame, filters: dict[str, list[str]]) -> pd.DataFrame:
    mask = pd.Series(True, index=cube.index)
    for name, values in filters.items():
        if name not in DIMENSIONS:
            raise ValueError(f"Filtro desconhecido: {name}")
        if values:
            mask &= cube[name].isin(values)
    return cube.loc[mask]


def statistics(cube: pd.DataFrame) -> dict:
    count = int(cube["count"].sum())
    if not count:
        return {"count": 0, "mean": None, "std": None, "zeros": 0, "min": None, "max": None}
    total = float(cube.score_sum.sum())
    variance = max(0.0, float(cube.score_sum_squared.sum()) - total**2 / count)
    return {
        "count": count,
        "mean": total / count,
        "std": (variance / (count - 1)) ** 0.5 if count > 1 else None,
        "zeros": int(cube.zeros.sum()),
        "min": float(cube.minimum.min()),
        "max": float(cube.maximum.max()),
    }


def grouped_statistics(cube: pd.DataFrame, dimension: str) -> pd.DataFrame:
    if dimension not in DIMENSIONS:
        raise ValueError("Dimensão desconhecida.")
    grouped = (
        cube.groupby(dimension, observed=True)
        .agg(participantes=("count", "sum"), soma=("score_sum", "sum"), zeros=("zeros", "sum"))
        .reset_index()
    )
    grouped["nota_media"] = grouped.soma / grouped.participantes
    return grouped.drop(columns="soma")


def build_dashboard(config: StudyConfig, output: Path, eda_dir: Path, cv_dir: Path) -> dict:
    """Publicar novo snapshot somente após conciliar EDA, CV e fonte verificada."""
    if output.exists():
        raise FileExistsError("Snapshot existente; use outro diretório para preservar a execução.")
    eda_path = eda_dir / "diagnostico_desenvolvimento.json"
    cv_path = cv_dir / "manifesto.json"
    eda, cv_manifest = read_json(eda_path), read_json(cv_path)
    if (
        eda.get("evaluated_set") != "development"
        or eda.get("test_evaluated") is not False
        or cv_manifest.get("evaluated_set") != "development_cv"
        or cv_manifest.get("test_evaluated") is not False
        or cv_manifest.get("status") != "completed"
    ):
        raise ValueError("EDA e CV devem corresponder ao desenvolvimento, com teste reservado.")
    frame, provenance = load_development(config)
    for report in (eda, cv_manifest):
        if any(report.get(key) != value for key, value in provenance.items()):
            raise ValueError("EDA/CV incompatíveis com a proveniência atual do estudo.")
    cube = aggregate_development(frame, config.target)
    summary = statistics(cube)
    if (
        summary["count"] != eda["rows"]
        or summary["zeros"] != eda["zeros"]
        or not np.isclose(summary["mean"], eda["target_summary"]["mean"], atol=1e-8, rtol=0)
    ):
        raise ValueError("Os agregados do painel não conciliam com a exploração existente.")
    splits = read_json(config.splits / "manifesto.json")
    quality = read_json(config.dataset / "qualidade.json")
    # Somente contagens de ingestão: nenhuma estatística das notas reservadas.
    quality_view = {
        key: quality[key]
        for key in (
            "status",
            "rows",
            "column_count",
            "duplicate_identifiers",
            "missing_identifiers",
            "rows_removed",
            "invalid_numeric",
            "errors",
        )
    }
    dictionary = read_json(config.dictionary) if config.dictionary else {"columns": {}}
    dictionary["columns"] = {
        name: dictionary["columns"][name] for name in [config.target, *config.features]
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".dashboard-", dir=output.parent) as temp:
        staging = Path(temp) / "snapshot"
        staging.mkdir()
        cube.to_parquet(staging / "agregados.parquet", index=False, compression="zstd")
        write_json(staging / "diagnostico.json", eda)
        write_json(staging / "qualidade.json", quality_view)
        write_json(staging / "dicionario.json", dictionary)
        shutil.copyfile(cv_dir / "resumo_cv.csv", staging / "resumo_cv.csv")
        folds = pd.read_csv(cv_dir / "experimentos.csv")
        # A tabela de dobras contém só métricas e tamanhos, sem linhas individuais.
        folds[
            ["model", "evaluated_set", "fold", "rmse", "mae", "r2", "n_train", "n_evaluated"]
        ].to_csv(staging / "dobras.csv", index=False, lineterminator="\n")
        manifest = {
            "version": 1,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "status": "completed",
            "evaluated_set": "development",
            **provenance,
            "theme": config.theme,
            "bin_width": BIN_WIDTH,
            "dimensions": list(DIMENSIONS),
            "aggregate_rows": len(cube),
            "features": config.features,
            "population": {
                key: splits[key]
                for key in (
                    "source_rows",
                    "eligible",
                    "missing_target",
                    "development",
                    "test",
                    "seed",
                    "test_size",
                    "n_splits",
                )
            },
            "reports_sha256": {"eda": sha256_file(eda_path), "cv": sha256_file(cv_path)},
            "assets": {name: sha256_file(staging / name) for name in ASSETS},
        }
        write_json(staging / "manifesto.json", manifest)
        load_dashboard(staging)  # Validar também o caminho de leitura usado pelo frontend.
        staging.rename(output)
    return manifest


def load_dashboard(path: Path) -> DashboardData:
    manifest = read_json(path / "manifesto.json")
    if (
        manifest.get("version") != 1
        or manifest.get("status") != "completed"
        or manifest.get("evaluated_set") != "development"
        or manifest.get("test_evaluated") is not False
        or set(manifest.get("assets", {})) != set(ASSETS)
    ):
        raise ValueError("Snapshot inválido ou fora do conjunto de desenvolvimento.")
    for name in ASSETS:
        verify_sha256(path / name, manifest["assets"][name], "Integridade do snapshot reprovada")
    cube = pd.read_parquet(path / "agregados.parquet")
    cv = pd.read_csv(path / "resumo_cv.csv")
    folds = pd.read_csv(path / "dobras.csv")
    if (
        statistics(cube)["count"] != manifest["n_development"]
        or not cv.evaluated_set.eq("development_cv").all()
        or not folds.evaluated_set.eq("development_cv").all()
    ):
        raise ValueError("Contagens ou conjunto das métricas inconsistentes.")
    return DashboardData(
        manifest,
        cube,
        read_json(path / "diagnostico.json"),
        read_json(path / "qualidade.json"),
        read_json(path / "dicionario.json"),
        cv,
        folds,
    )
