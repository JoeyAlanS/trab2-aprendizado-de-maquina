"""Representações ajustadas no treino de cada dobra, sem usar o conjunto de teste."""

from dataclasses import replace

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, TransformerMixin, clone
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectPercentile, f_regression
from sklearn.pipeline import Pipeline
from sklearn.utils.validation import check_is_fitted

from enem_base.study import StudyConfig

DERIVED = ("COMPUTADORES_POR_MORADOR", "ACESSO_DIGITAL", "ESCOLARIDADE_PAIS_MAX")
VARIANTS = ("original", "engineered", "selected", "pca", "weighted", "without_socio", "without_uf")


class ProfileFeatures(TransformerMixin, BaseEstimator):
    """Três atributos determinísticos; desconhecimento não recebe nível escolar fictício.

    Q024=E é uma contagem limitada: quatro representa o mínimo declarado.
    Escolaridade máxima exige as duas respostas conhecidas; ausência será tratada
    pelo imputador/indicador ajustado dentro da dobra.
    """

    def fit(self, X, y=None):
        required = {"Q001", "Q002", "Q005", "Q024", "Q025"}
        if not required.issubset(X.columns):
            raise ValueError("A engenharia exige Q001, Q002, Q005, Q024 e Q025.")
        self.feature_names_in_ = np.asarray(X.columns, dtype=object)
        return self

    def transform(self, X):
        check_is_fitted(self)
        result = X.copy()
        people = pd.to_numeric(X.Q005, errors="raise").astype(float)
        people = people.where(people.between(1, 20))
        computers = X.Q024.map(dict(zip("ABCDE", range(5), strict=True))).astype(float)
        internet = X.Q025.map({"A": 0.0, "B": 1.0}).astype(float)
        father = X.Q001.map(dict(zip("ABCDEFG", range(7), strict=True))).astype(float)
        mother = X.Q002.map(dict(zip("ABCDEFG", range(7), strict=True))).astype(float)
        result[DERIVED[0]] = computers / people
        result[DERIVED[1]] = computers.gt(0).astype(float).where(computers.notna()) + internet
        result[DERIVED[2]] = np.maximum(father, mother)
        return result

    def get_feature_names_out(self, input_features=None):
        check_is_fitted(self)
        return np.r_[self.feature_names_in_, DERIVED]


class VariancePCA(TransformerMixin, BaseEstimator):
    """PCA centrado por covariância, mantendo a fração aprendida no treino.

    Aceita one-hot esparso; evita densificar a entrada inteira. A saída é densa,
    float32, construída em lotes com limite de memória explícito.
    Q005 já é padronizada; indicadores one-hot mantêm sua variância natural.
    """

    def __init__(self, variance=0.8, batch_size=25000, max_output_bytes=2 * 1024**3):
        self.variance = variance
        self.batch_size = batch_size
        self.max_output_bytes = max_output_bytes

    def fit(self, X, y=None):
        if not 0 < self.variance <= 1 or self.batch_size < 1:
            raise ValueError("Fração de variância e tamanho de lote inválidos.")
        self.pca_ = PCA(svd_solver="covariance_eigh", random_state=42).fit(X)
        self.explained_variance_ratio_ = self.pca_.explained_variance_ratio_
        if not np.isfinite(self.explained_variance_ratio_).all():
            raise ValueError("PCA sem variância finita no treino.")
        self.n_components_ = min(
            int(np.searchsorted(np.cumsum(self.explained_variance_ratio_), self.variance)) + 1,
            len(self.explained_variance_ratio_),
        )
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X):
        check_is_fitted(self)
        required = X.shape[0] * self.n_components_ * 4
        if required > self.max_output_bytes:
            raise MemoryError(
                f"Saída PCA exige {required} bytes; limite={self.max_output_bytes}. "
                "Disponibilize memória e ajuste o limite; não substitua a base por amostra."
            )
        result = np.empty((X.shape[0], self.n_components_), dtype=np.float32)
        components = self.pca_.components_[: self.n_components_]
        offset = self.pca_.mean_ @ components.T
        for start in range(0, X.shape[0], self.batch_size):
            stop = min(start + self.batch_size, X.shape[0])
            result[start:stop] = X[start:stop] @ components.T - offset
        return result

    def get_feature_names_out(self, input_features=None):
        check_is_fitted(self)
        return np.asarray([f"pca{i + 1}" for i in range(self.n_components_)], dtype=object)


class TrainingWeightedRegressor(RegressorMixin, BaseEstimator):
    """Aprende faixas de largura igual e pesos inversos exclusivamente no treino."""

    def __init__(self, estimator, n_bins=10):
        self.estimator = estimator
        self.n_bins = n_bins

    def fit(self, X, y):
        y = np.asarray(y, dtype=float)
        if self.n_bins < 2 or not np.isfinite(y).all() or np.ptp(y) == 0:
            raise ValueError("Ponderação exige pelo menos duas faixas e alvo variável finito.")
        self.bin_edges_ = np.linspace(y.min(), y.max(), self.n_bins + 1)
        labels = np.clip(np.searchsorted(self.bin_edges_, y, side="right") - 1, 0, self.n_bins - 1)
        self.bin_counts_ = np.bincount(labels, minlength=self.n_bins)
        weights = len(y) / (np.count_nonzero(self.bin_counts_) * self.bin_counts_[labels])
        self.estimator_ = clone(self.estimator).fit(X, y, regressor__sample_weight=weights)
        return self

    def predict(self, X):
        check_is_fitted(self)
        return self.estimator_.predict(X)


def variant_catalog(config: StudyConfig, variant: str) -> tuple[dict, list[str]]:
    from enem_base.modeling import model_catalog

    if variant not in VARIANTS:
        raise ValueError(f"Representação desconhecida: {variant}")
    if variant == "without_socio":
        config = replace(
            config,
            numeric=tuple(n for n in config.numeric if not n.startswith("Q")),
            categorical=tuple(n for n in config.categorical if not n.startswith("Q")),
        )
    elif variant == "without_uf":
        config = replace(
            config, categorical=tuple(n for n in config.categorical if n != "SG_UF_PROVA")
        )
    engineered = variant in {"engineered", "selected"}
    if engineered:
        config = replace(config, numeric=(*config.numeric, *DERIVED))
    catalog = model_catalog(config)
    for name, estimator in list(catalog.items()):
        if name == "baseline":
            continue
        if variant in {"engineered", "selected", "pca", "weighted"} and name == "stacking":
            # O stacking original continua disponível; não aplicar seleção/PCA antes de suas CVs.
            del catalog[name]
            continue
        if engineered:
            estimator.steps.insert(0, ("features", ProfileFeatures()))
        if variant == "selected":
            estimator.steps.insert(-1, ("selection", SelectPercentile(f_regression, percentile=75)))
        if variant == "pca":
            estimator.steps.insert(-1, ("pca", VariancePCA()))
        if variant == "weighted":
            if name != "ridge":
                del catalog[name]
                continue
            catalog[name] = TrainingWeightedRegressor(estimator)
    if variant == "weighted":
        catalog.pop("baseline", None)
    return catalog, config.features


def fitted_diagnostics(estimator) -> dict:
    """Somente estatísticas realmente aprendidas pelo estimador ajustado."""
    if isinstance(estimator, TrainingWeightedRegressor):
        return {
            "weight_bin_edges": estimator.bin_edges_.tolist(),
            "weight_bin_counts": estimator.bin_counts_.tolist(),
        }
    result = {}
    if isinstance(estimator, Pipeline):
        regressor = estimator.named_steps.get("regressor")
        if getattr(regressor, "binary_backend_", False):
            result.update(
                knn_backend=regressor.backend_name_,
                knn_numeric_groups=regressor.n_numeric_groups_,
                knn_input_dimensions=regressor.n_features_in_,
            )
        if "pca" in estimator.named_steps:
            pca = estimator["pca"]
            result.update(
                pca_components=pca.n_components_,
                pca_input_dimensions=pca.n_features_in_,
                pca_explained_variance_ratio=pca.explained_variance_ratio_.tolist(),
            )
        if "selection" in estimator.named_steps:
            names = estimator["preparation"].get_feature_names_out()
            result["selected_features"] = names[estimator["selection"].get_support()].tolist()
    return result
