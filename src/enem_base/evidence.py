"""Leitura estrita de execuções e métricas por grupo calculadas de previsões reais."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from enem_base.provenance import sha256_file, verify_sha256, write_json

PROVENANCE_KEYS = ("source_sha256", "splits_sha256", "study_sha256", "dictionary_sha256", "target")
SCORE_EDGES = [0, 400, 500, 600, 700, float("inf")]
SCORE_LABELS = ["[0,400)", "[400,500)", "[500,600)", "[600,700)", "[700,+inf)"]
GROUP_FIELDS = ("TP_ESCOLA", "SG_UF_PROVA", "Q006")


def group_errors(frame, predicted, target, model, fold=None) -> list[dict]:
    from enem_base.modeling import regression_metrics

    observed = frame[target].to_numpy(dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    if len(observed) != len(predicted):
        raise ValueError("Previsões e grupos não têm o mesmo número de participantes.")
    fields = {
        "faixa_nota": pd.Series(pd.cut(observed, SCORE_EDGES, labels=SCORE_LABELS, right=False))
    }
    fields.update(
        {
            name: frame[name].reset_index(drop=True).astype("string").fillna("__MISSING__")
            for name in GROUP_FIELDS
            if name in frame
        }
    )
    result = []
    for field, labels in fields.items():
        for label in labels.unique():
            mask = labels.eq(label).to_numpy(dtype=bool)
            if not mask.any():
                continue
            result.append(
                {
                    "model": model,
                    "fold": fold,
                    "group": field,
                    "category": str(label),
                    "n": int(mask.sum()),
                    **regression_metrics(observed[mask], predicted[mask]),
                    "mean_residual": float(np.mean(observed[mask] - predicted[mask])),
                }
            )
    return result


def seal_run(output: Path, manifest: dict) -> None:
    manifest["assets"] = {
        path.name: sha256_file(path)
        for path in sorted(output.iterdir())
        if path.is_file() and path.name != "manifesto.json"
    }
    write_json(output / "manifesto.json", manifest)


def read_run(path: Path, expected: dict | None = None, *, development=True) -> dict:
    manifest = json.loads((path / "manifesto.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "completed":
        raise ValueError(f"Execução incompleta: {path}")
    if development and (
        manifest.get("test_evaluated") is not False
        or manifest.get("evaluated_set") != "development_cv"
    ):
        raise ValueError("Seleção exige somente resultados do desenvolvimento.")
    if expected is not None and any(manifest.get(k) != expected.get(k) for k in PROVENANCE_KEYS):
        raise ValueError(f"Proveniência incompatível: {path}")
    if not manifest.get("assets"):
        raise ValueError(
            f"Execução sem hashes dos resultados: {path}. "
            "Preserve o histórico e execute novamente com a versão atual."
        )
    for name, digest in manifest["assets"].items():
        asset = path / name
        if asset.parent != path or Path(name).name != name:
            raise ValueError("Caminho inválido no manifesto.")
        verify_sha256(asset, digest, "Resultado alterado")
    return manifest


def comparison_rows(path: Path, expected: dict) -> tuple[pd.DataFrame, dict]:
    manifest = read_run(path, expected)
    if manifest.get("experiment_kind") != "comparison":
        raise ValueError("A entrada deve ser uma comparação por dobra.")
    rows = pd.read_csv(path / "experimentos.csv")
    if not rows.evaluated_set.eq("development_cv").all() or not rows.row_type.eq("fold").all():
        raise ValueError("O arquivo precisa conter avaliações reais por dobra.")
    for _, group in rows.groupby("model"):
        if len(group) != 3 or set(group.fold) != {0, 1, 2}:
            raise ValueError("Cada modelo precisa das três dobras distintas.")
        if group.n_evaluated.sum() != manifest["n_development"]:
            raise ValueError("Comparação não cobre todo o desenvolvimento.")
        if not (group.n_train + group.n_evaluated).eq(manifest["n_development"]).all():
            raise ValueError("Tamanhos de treino/validação inconsistentes.")
    if set(rows.model) != set(manifest["models"]):
        raise ValueError("Modelos do CSV diferem do manifesto.")
    return rows, manifest
