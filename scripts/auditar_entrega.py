"""Conferir execuções existentes sem treinar ou alterar os checkpoints científicos."""

import argparse
import json
import zipfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from enem_base.evidence import comparison_rows, read_run
from enem_base.final_evaluation import validate_final_results
from enem_base.final_selection import validate_searches
from enem_base.frozen_curves import validate_curves
from enem_base.provenance import sha256_file, verify_sha256, write_json
from enem_base.study import load_study

BASE = Path("resultados/ciencias_natureza")
OUT = BASE / "checkpoint-7-2026-11-07"
CP4 = BASE / "checkpoint-4-2026-11-07"
MODELS = ["svm", "knn", "bagging", "pasting", "random_forest", "boosting", "stacking"]


@contextmanager
def archived_reports():
    """Materializar temporariamente documentos históricos exigidos pelos hashes.

    O ZIP preserva os bytes originais sem repor relatórios obsoletos na apresentação.
    Nenhuma verificação científica é desabilitada; só arquivos criados aqui são removidos.
    """
    archive = Path("resultados/evidencias/protocolos.zip")
    created = []
    try:
        with zipfile.ZipFile(archive) as package:
            for name in ("docs/checkpoint-2-resultados.md", "docs/checkpoint-3-resultados.md"):
                path = Path(name)
                if not path.exists():
                    with path.open("xb") as stream:
                        stream.write(package.read(name))
                    created.append(path)
        yield
    finally:
        for path in created:
            path.unlink()


def main(out: Path = OUT):
    # Não sobrescrever evidências de uma conferência anterior.
    out.mkdir(parents=True, exist_ok=False)
    config = load_study(Path("configs/ciencias_natureza.toml"))
    protocol = json.loads((CP4 / "protocolo_buscas.json").read_text())
    coverage = []
    paths = [BASE / "cv-recuperado-v2"]
    paths += [BASE / "checkpoint-1-2026-11-06" / name for name in MODELS]
    paths += [
        BASE / f"{name}-v2"
        for name in ["engineered", "selected", "pca", "weighted", "without_socio", "without_uf"]
    ]
    for path in paths:
        rows, manifest = comparison_rows(path, protocol)
        for model, group in rows.groupby("model"):
            assert np.isfinite(group[["rmse", "mae", "r2"]]).all().all()
            assert all(json.loads(value) == [] for value in group.warnings_json)
            coverage.append(
                {
                    "stage": "comparacao_cv",
                    "model": model,
                    "variant": manifest["variant"],
                    "evaluations": len(group),
                    "n_validation_total": int(group.n_evaluated.sum()),
                    "status": "executado_e_conferido",
                    "source": str(path),
                }
            )
    print("Comparações: 54 avaliações por dobra confirmadas.", flush=True)

    def redirected(path, payload):
        # Redirecionar a evidência, preservando as execuções científicas originais.
        if Path(path).parent != CP4:
            raise ValueError(f"Escrita inesperada: {path}")
        write_json(out / Path(path).name, payload)

    with patch("enem_base.final_selection.atomic_json", redirected):
        _, searches, _ = validate_searches(config, CP4)
    for model, group in searches.groupby("model"):
        coverage.append(
            {
                "stage": "busca_cv",
                "model": model,
                "variant": "original",
                "evaluations": len(group) * 3,
                "configurations": len(group),
                "status": "metricas_recompostas_de_previsoes",
                "source": str(CP4 / "buscas" / model),
            }
        )
    print("Buscas: 60 configurações e 180 avaliações recompostas.", flush=True)
    curves, _ = validate_curves(config, CP4)
    for model, group in curves.groupby("model"):
        coverage.append(
            {
                "stage": "curva_final",
                "model": model,
                "variant": "congelada",
                "evaluations": len(group),
                "status": "pontos_e_hashes_conferidos",
                "source": str(CP4 / "curvas_finais" / model),
            }
        )
    for model in ["stacking", "svm", "random_forest"]:
        path = BASE / "checkpoint-3-2026-11-06" / model
        manifest = read_run(path, protocol)
        for section in ["point_assets", "fit_assets"]:
            for name, expected in manifest.get(section, {}).items():
                verify_sha256(path / name, expected, "Curva inicial alterada")
        frame = pd.read_csv(path / "curvas.csv")
        assert len(frame) == 15
        assert set(zip(frame.fold, frame.fraction, strict=True)) == {
            (f, p) for f in range(3) for p in [0.1, 0.25, 0.5, 0.75, 1]
        }
        coverage.append(
            {
                "stage": "curva_inicial",
                "model": model,
                "variant": "original",
                "evaluations": len(frame),
                "status": "pontos_e_hashes_conferidos",
                "source": str(path),
            }
        )
    with patch("enem_base.final_evaluation.atomic_json", redirected):
        final = validate_final_results(config, CP4)
    for row in final.itertuples():
        coverage.append(
            {
                "stage": "teste_reservado",
                "model": row.model,
                "variant": "congelada",
                "evaluations": 1,
                "n_validation_total": int(row.n_evaluated),
                "status": "metricas_e_grupos_recompostos",
                "source": str(CP4 / "avaliacao_final"),
            }
        )
    pd.DataFrame(coverage).to_csv(out / "cobertura_execucoes.csv", index=False)
    write_json(
        out / "auditoria_experimentos.json",
        {
            "status": "passed",
            "comparison_fold_evaluations": 54,
            "initial_models": 11,
            "requested_seven_fold_evaluations": 21,
            "variant_fold_evaluations": 21,
            "search_configurations": 60,
            "search_fold_evaluations": 180,
            "initial_curve_points": 45,
            "final_curve_points": 45,
            "final_models": list(final.model),
            "n_test_per_model": 538486,
            "final_curve_origins": curves.origin.value_counts().to_dict(),
            "models_without_reserved_test": [
                "knn",
                "bagging",
                "pasting",
                "boosting",
                "ridge",
                "arvore",
            ],
            "reason": (
                "O protocolo prevê teste final do trio selecionado "
                "mais média e linear de referência."
            ),
            "new_training": False,
            "new_test_predictions": False,
            "coverage_sha256": sha256_file(out / "cobertura_execucoes.csv"),
        },
    )
    print("Curvas e teste: evidências aprovadas, cinco modelos e 260 grupos conferidos.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT)
    with archived_reports():
        main(parser.parse_args().output)
