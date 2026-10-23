"""Varredura descritiva de todas as entradas e de todos os pares, sem tocar no teste."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from enem_base.dashboard import MISSING, read_json
from enem_base.provenance import sha256_file, write_json
from enem_base.study import StudyConfig, load_development

logger = logging.getLogger(__name__)
RELATION_ASSETS = ("alvo.csv", "pares.csv", "perfis.parquet", "cruzamentos.parquet")
LABELS = {
    "Q005": "Pessoas na residência",
    "TP_FAIXA_ETARIA": "Faixa etária",
    "TP_SEXO": "Sexo informado",
    "TP_ESTADO_CIVIL": "Estado civil",
    "TP_COR_RACA": "Cor/raça autodeclarada",
    "TP_NACIONALIDADE": "Nacionalidade",
    "TP_ST_CONCLUSAO": "Situação do ensino médio",
    "TP_ANO_CONCLUIU": "Ano de conclusão",
    "TP_ESCOLA": "Tipo de escola",
    "TP_ENSINO": "Modalidade de ensino",
    "IN_TREINEIRO": "Treineiro",
    "TP_DEPENDENCIA_ADM_ESC": "Dependência administrativa",
    "TP_LOCALIZACAO_ESC": "Localização da escola",
    "TP_SIT_FUNC_ESC": "Funcionamento da escola",
    "SG_UF_PROVA": "UF de aplicação da prova",
    "TP_LINGUA": "Língua estrangeira",
    "Q001": "Escolaridade do pai/responsável",
    "Q002": "Escolaridade da mãe/responsável",
    "Q003": "Ocupação do pai/responsável",
    "Q004": "Ocupação da mãe/responsável",
    "Q006": "Renda familiar",
    "Q007": "Empregado doméstico",
    "Q008": "Banheiros",
    "Q009": "Quartos",
    "Q010": "Carros",
    "Q011": "Motocicletas",
    "Q012": "Geladeiras",
    "Q013": "Freezer",
    "Q014": "Máquina de lavar roupa",
    "Q015": "Secadora de roupa",
    "Q016": "Micro-ondas",
    "Q017": "Máquina de lavar louça",
    "Q018": "Aspirador de pó",
    "Q019": "Televisores",
    "Q020": "DVD",
    "Q021": "TV por assinatura",
    "Q022": "Celulares",
    "Q023": "Telefone fixo",
    "Q024": "Computadores",
    "Q025": "Internet",
}


@dataclass(frozen=True)
class RelationData:
    manifest: dict
    target: pd.DataFrame
    pairs: pd.DataFrame
    profiles: pd.DataFrame
    cells: pd.DataFrame


def cramers_v(counts: np.ndarray) -> float | None:
    """V de Cramér sem correção de continuidade, margens vazias removidas."""
    counts = np.asarray(counts, dtype=float)
    counts = counts[counts.sum(axis=1) > 0][:, counts.sum(axis=0) > 0]
    if min(counts.shape, default=0) < 2:
        return None
    total = counts.sum()
    expected = np.outer(counts.sum(axis=1), counts.sum(axis=0)) / total
    chi_squared = ((counts - expected) ** 2 / expected).sum()
    return float(np.clip(np.sqrt(chi_squared / (total * (min(counts.shape) - 1))), 0, 1))


def eta_squared(counts: np.ndarray, sums: np.ndarray, squares: np.ndarray) -> float | None:
    """SS entre grupos / SS total; não é desempenho de previsão em validação."""
    present = counts > 0
    counts, sums, squares = counts[present], sums[present], squares[present]
    if len(counts) < 2:
        return None
    correction = sums.sum() ** 2 / counts.sum()
    total = squares.sum() - correction
    if total <= 1e-10:
        return None
    between = (sums**2 / counts).sum() - correction
    return float(np.clip(between / total, 0, 1))


def _moments(codes: np.ndarray, y: np.ndarray, size: int) -> dict[str, np.ndarray]:
    count = np.bincount(codes, minlength=size)
    sums = np.bincount(codes, weights=y, minlength=size)
    squares = np.bincount(codes, weights=y**2, minlength=size)
    means = np.divide(sums, count, out=np.full(size, np.nan), where=count > 0)
    deviations = np.maximum(0, squares - np.nan_to_num(means) ** 2 * count)
    variance = np.divide(deviations, count - 1, out=np.full(size, np.nan), where=count > 1)
    return {
        "count": count,
        "sum": sums,
        "squares": squares,
        "mean": means,
        "std": np.sqrt(variance),
        "zeros": np.bincount(codes[y == 0], minlength=size),
    }


def _numeric_eta(table: np.ndarray, values: np.ndarray, valid_group: np.ndarray) -> float | None:
    valid_number = np.isfinite(values)
    table = table[np.ix_(valid_number, valid_group)]
    numbers = values[valid_number]
    return eta_squared(table.sum(axis=0), numbers @ table, numbers**2 @ table)


def analyze_frame(frame: pd.DataFrame, config: StudyConfig, dictionary: dict) -> RelationData:
    if frame.empty or not frame.partition.eq("development").all():
        raise ValueError("Relações exigem exclusivamente linhas de desenvolvimento.")
    y = frame[config.target].to_numpy(dtype=float)
    if not np.isfinite(y).all():
        raise ValueError("Alvo ausente ou não finito na análise de relações.")
    encoded, levels, observed, numeric_levels = {}, {}, {}, {}
    target_rows, profile_frames, pair_rows, cell_frames = [], [], [], []
    for name in config.features:
        codes, unique = pd.factorize(frame[name], sort=True, use_na_sentinel=False)
        encoded[name] = codes.astype("int32")
        observed[name] = ~pd.isna(unique)
        levels[name] = [
            MISSING
            if pd.isna(value)
            else f"{float(value):g}"
            if name in config.numeric
            else str(value)
            for value in unique
        ]
        stats = _moments(encoded[name], y, len(unique))
        valid = observed[name]
        eta = eta_squared(stats["count"][valid], stats["sum"][valid], stats["squares"][valid])
        spec = dictionary.get("columns", {}).get(name, {})
        labels = spec.get("categories", {})
        profile_frames.append(
            pd.DataFrame(
                {
                    "variable": name,
                    "code": levels[name],
                    "label": [
                        "Ausente" if code == MISSING else labels.get(code, code)
                        for code in levels[name]
                    ],
                    "n": stats["count"],
                    "mean": stats["mean"],
                    "std": stats["std"],
                    "zeros": stats["zeros"],
                }
            )
        )
        row = {
            "variable": name,
            "label": LABELS.get(name, name),
            "description": spec.get("description", name),
            "kind": "numeric" if name in config.numeric else "categorical",
            "n": len(frame),
            "n_observed": int(stats["count"][valid].sum()),
            "missing": int(stats["count"][~valid].sum()),
            "groups_observed": int(valid.sum()),
            "eta_squared": eta,
            "eta_squared_all": eta_squared(stats["count"], stats["sum"], stats["squares"]),
            "pearson": None,
            "spearman": None,
        }
        if name in config.numeric:
            numeric_levels[name] = np.array(
                [float(v) if v != MISSING else np.nan for v in levels[name]]
            )
            x = frame[name].to_numpy(dtype=float, na_value=np.nan)
            complete = np.isfinite(x)
            if complete.sum() > 1 and np.ptp(x[complete]) > 0 and np.ptp(y[complete]) > 0:
                row["pearson"] = float(pearsonr(x[complete], y[complete]).statistic)
                row["spearman"] = float(spearmanr(x[complete], y[complete]).statistic)
        target_rows.append(row)

    for index, (a, b) in enumerate(combinations(config.features, 2), start=1):
        ka, kb = len(levels[a]), len(levels[b])
        joint = encoded[a] * kb + encoded[b]
        stats = _moments(joint, y, ka * kb)
        table = stats["count"].reshape(ka, kb)
        observed_table = table[np.ix_(observed[a], observed[b])]
        if a in config.numeric and b in config.numeric:
            raise ValueError("Pares numérico-numérico adicionais exigem método explícito.")
        if a in config.numeric or b in config.numeric:
            metric = "eta_squared"
            numeric = a if a in config.numeric else b
            group = b if numeric == a else a
            oriented = table if numeric == a else table.T
            value = _numeric_eta(oriented, numeric_levels[numeric], observed[group])
            value_all = _numeric_eta(
                oriented, numeric_levels[numeric], np.ones(len(levels[group]), bool)
            )
        else:
            metric = "cramers_v"
            value, value_all = cramers_v(observed_table), cramers_v(table)
        pair_rows.append(
            {
                "variable_a": a,
                "variable_b": b,
                "metric": metric,
                "value": value,
                "value_with_missing_category": value_all,
                "n": len(frame),
                "n_observed": int(observed_table.sum()),
                "missing_either": int(len(frame) - observed_table.sum()),
            }
        )
        indices = np.flatnonzero(stats["count"])
        cell_frames.append(
            pd.DataFrame(
                {
                    "variable_a": a,
                    "variable_b": b,
                    "code_a": [levels[a][i // kb] for i in indices],
                    "code_b": [levels[b][i % kb] for i in indices],
                    "n": stats["count"][indices],
                    "mean": stats["mean"][indices],
                    "std": stats["std"][indices],
                    "zeros": stats["zeros"][indices],
                }
            )
        )
        if index % 100 == 0:
            logger.info("%s pares de variáveis analisados", index)
    return RelationData(
        {},
        pd.DataFrame(target_rows),
        pd.DataFrame(pair_rows),
        pd.concat(profile_frames, ignore_index=True),
        pd.concat(cell_frames, ignore_index=True),
    )


def build_relations(config: StudyConfig, output: Path) -> dict:
    if output.exists():
        raise FileExistsError("Relações já geradas; preserve a execução usando outro diretório.")
    frame, provenance = load_development(config)
    dictionary = read_json(config.dictionary) if config.dictionary else {"columns": {}}
    result = analyze_frame(frame, config, dictionary)
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".relacoes-", dir=output.parent) as temp:
        staging = Path(temp) / "snapshot"
        staging.mkdir()
        result.target.to_csv(staging / "alvo.csv", index=False)
        result.pairs.to_csv(staging / "pares.csv", index=False)
        result.profiles.to_parquet(staging / "perfis.parquet", index=False, compression="zstd")
        result.cells.to_parquet(staging / "cruzamentos.parquet", index=False, compression="zstd")
        manifest = {
            "version": 1,
            "status": "completed",
            "created_at_utc": datetime.now(UTC).isoformat(),
            **provenance,
            "evaluated_set": "development",
            "features": config.features,
            "n_variables": len(result.target),
            "n_pairs": len(result.pairs),
            "n_profiles": len(result.profiles),
            "n_joint_cells": len(result.cells),
            "numeric_features": list(config.numeric),
            "methods": {
                "target": (
                    "eta squared for category groups; Pearson/Spearman only for numeric input"
                ),
                "categorical_pairs": "Cramers V, Pearson chi squared without continuity correction",
                "mixed_pairs": "eta squared of numeric input by categorical input",
                "missing": (
                    "primary effects use pairwise observed; "
                    "missing category retained in profiles and sensitivity"
                ),
                "inference": (
                    "descriptive effects only; no significance claims or causal conclusions"
                ),
            },
            "assets": {name: sha256_file(staging / name) for name in RELATION_ASSETS},
        }
        write_json(staging / "manifesto.json", manifest)
        load_relations(staging, provenance)
        staging.rename(output)
    return manifest


def load_relations(path: Path, expected: dict | None = None) -> RelationData:
    manifest = read_json(path / "manifesto.json")
    if (
        manifest.get("status") != "completed"
        or manifest.get("test_evaluated") is not False
        or manifest.get("evaluated_set") != "development"
        or manifest.get("version") != 1
        or set(manifest.get("assets", {})) != set(RELATION_ASSETS)
    ):
        raise ValueError("Manifesto de relações inválido ou fora do desenvolvimento.")
    for key in (
        "source_sha256",
        "splits_sha256",
        "study_sha256",
        "dictionary_sha256",
        "target",
        "n_development",
    ):
        if expected is not None and manifest[key] != expected[key]:
            raise ValueError("Relações e painel usam proveniências diferentes.")
    for name in RELATION_ASSETS:
        if sha256_file(path / name) != manifest["assets"][name]:
            raise ValueError(f"Integridade das relações reprovada: {name}")
    result = RelationData(
        manifest,
        pd.read_csv(path / "alvo.csv"),
        pd.read_csv(path / "pares.csv"),
        pd.read_parquet(path / "perfis.parquet"),
        pd.read_parquet(path / "cruzamentos.parquet"),
    )
    count = len(manifest["features"])
    if (
        len(result.target) != count
        or len(result.pairs) != count * (count - 1) // 2
        or not result.profiles.groupby("variable").n.sum().eq(manifest["n_development"]).all()
        or not result.cells.groupby(["variable_a", "variable_b"])
        .n.sum()
        .eq(manifest["n_development"])
        .all()
    ):
        raise ValueError("Cobertura incompleta das relações ou contagens inconsistentes.")
    return result


def pair_cells(data: RelationData, a: str, b: str) -> pd.DataFrame:
    if a == b:
        raise ValueError("Escolha duas variáveis distintas.")
    selected = data.cells.loc[data.cells.variable_a.eq(a) & data.cells.variable_b.eq(b)]
    if selected.empty:
        selected = data.cells.loc[data.cells.variable_a.eq(b) & data.cells.variable_b.eq(a)]
        selected = selected.rename(
            columns={
                "variable_a": "variable_b",
                "variable_b": "variable_a",
                "code_a": "code_b",
                "code_b": "code_a",
            }
        )
    if selected.empty:
        raise ValueError("Par de variáveis não encontrado nas relações.")
    return selected.copy()
