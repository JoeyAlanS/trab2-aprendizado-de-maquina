"""Resultados publicados, independentes do snapshot histórico de exploração.

Lê apenas tabelas agregadas seladas. Não abre previsões individuais, não treina
modelos e não muda a trava de avaliação do teste.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from enem_base.dashboard import read_json
from enem_base.provenance import verify_sha256

RESULT_ASSETS = ("experimentos.csv", "comparacao_modelos.csv")
INITIAL_MODELS = {
    "baseline",
    "linear",
    "ridge",
    "arvore",
    "svm",
    "knn",
    "bagging",
    "pasting",
    "random_forest",
    "boosting",
    "stacking",
}
FINAL_MODELS = {"baseline", "linear_reference", "svm", "random_forest", "stacking"}


@dataclass(frozen=True)
class ModelResults:
    cv: pd.DataFrame
    folds: pd.DataFrame
    test: pd.DataFrame
    experiments: pd.DataFrame
    provenance: dict

    @property
    def selected_model(self) -> str:
        """Seleção pelo desenvolvimento, sem consultar as métricas de teste."""
        return self.cv.sort_values("rmse_mean").iloc[0].model


def load_model_results(path: Path, expected: dict) -> ModelResults:
    manifest = read_json(path / "manifesto_entrega.json")
    if manifest.get("status") != "passed":
        raise ValueError("Entrega de resultados não validada.")
    for name in RESULT_ASSETS:
        digest = manifest.get("outputs", {}).get(f"resultados/{name}")
        if not digest:
            raise ValueError(f"Entrega sem hash de {name}.")
        verify_sha256(path / name, digest, "Integridade dos resultados reprovada")
    experiments = pd.read_csv(path / "experimentos.csv")
    if len(experiments) != manifest["experiment_rows"]:
        raise ValueError("Número de experimentos inconsistente com a entrega.")
    folds = experiments.loc[
        experiments.stage.eq("comparacao_inicial") & experiments.row_type.eq("fold")
    ].copy()
    summaries = experiments.loc[
        experiments.stage.eq("comparacao_inicial") & experiments.row_type.eq("summary")
    ].copy()
    test = experiments.loc[experiments.stage.eq("teste_final")].copy()
    if (
        set(folds.model) != INITIAL_MODELS
        or len(folds) != 33
        or set(summaries.model) != INITIAL_MODELS
        or len(summaries) != 11
        or set(test.model) != FINAL_MODELS
        or len(test) != 5
        or not folds.evaluated_set.eq("development_cv").all()
        or not test.evaluated_set.eq("test").all()
        or not test.row_type.eq("test_final").all()
        or not folds.test_evaluated.eq(False).all()  # noqa: E712
        or not test.test_evaluated.eq(True).all()  # noqa: E712
    ):
        raise ValueError("Catálogo incompleto ou mistura entre validação e teste.")
    # O snapshot de exploração antecede a recuperação dos arquivos de partições
    # e dicionário, com outra serialização. Seus hashes não são reescritos nem
    # tratados como iguais aos da entrega. Os painéis não unem linhas individuais.
    for key in ("source_sha256", "study_sha256", "target", "n_development"):
        required = (
            pd.concat([folds, summaries])[key]
            if key == "n_development"
            else pd.concat([folds, summaries, test])[key]
        )
        if required.isna().any() or not required.eq(expected[key]).all():
            raise ValueError(f"Resultados incompatíveis com o painel: {key}.")
    n_dev = expected["n_development"]
    n_test = expected["population"]["test"]
    if (
        not test.n_evaluated.eq(n_test).all()
        or not test.n_train.eq(n_dev).all()
        or manifest["test_rows"] != n_test
    ):
        raise ValueError("População do teste final incompatível.")
    for _, group in folds.groupby("model"):
        if (
            set(group.fold) != {0, 1, 2}
            or group.n_evaluated.sum() != n_dev
            or not (group.n_train + group.n_evaluated).eq(n_dev).all()
        ):
            raise ValueError("Dobras incompletas ou participantes inconsistentes.")
    cv = pd.read_csv(path / "comparacao_modelos.csv").rename(
        columns={metric: f"{metric}_mean" for metric in ("rmse", "mae", "r2")}
    )
    if len(cv) != 11 or set(cv.model) != INITIAL_MODELS:
        raise ValueError("Resumo do catálogo incompleto.")
    metrics = ["rmse", "mae", "r2"]
    for frame in (folds, summaries, test):
        if not np.isfinite(frame[metrics].to_numpy(dtype=float)).all():
            raise ValueError("Métricas ausentes ou não finitas.")
    for metric in metrics:
        grouped = folds.groupby("model")[metric]
        indexed = cv.set_index("model").reindex(sorted(INITIAL_MODELS))
        summary = summaries.set_index("model").reindex(indexed.index)
        for column, calculated in (
            (f"{metric}_mean", grouped.mean()),
            (f"{metric}_std", grouped.std(ddof=0)),
        ):
            values = calculated.reindex(indexed.index).to_numpy()
            summary_column = metric if column.endswith("_mean") else column
            if not (
                np.allclose(indexed[column], values, atol=1e-10, rtol=0)
                and np.allclose(summary[summary_column], values, atol=1e-10, rtol=0)
            ):
                raise ValueError("Resumo difere das métricas por dobra.")
    provenance = {
        key: test[key].iloc[0]
        for key in ("source_sha256", "splits_sha256", "study_sha256", "dictionary_sha256", "target")
    }
    return ModelResults(cv, folds, test.sort_values("rmse"), experiments, provenance)
