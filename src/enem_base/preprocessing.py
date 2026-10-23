"""Fábrica de transformações não ajustadas, para futuro Pipeline por dobra.

Estratégias são exemplos técnicos; nenhuma foi escolhida para os microdados.
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from enem_base.features import validate_features


def normalize_missing(frame: pd.DataFrame) -> pd.DataFrame:
    """Adaptar pd.NA para np.nan sem aprender valores nem alterar o original."""
    return frame.astype(object).where(frame.notna(), np.nan)


def build_preprocessor(
    numeric: list[str],
    categorical: list[str],
    *,
    identifier: str,
    target: str | None = None,
    numeric_strategy: str = "median",
) -> ColumnTransformer:
    validate_features(numeric + categorical, identifier=identifier, target=target)
    if numeric_strategy not in {"mean", "median", "most_frequent"}:
        raise ValueError("Estratégia numérica deve ser mean, median ou most_frequent.")
    transformers = []
    if numeric:
        transformers.append(
            (
                "numeric",
                Pipeline(
                    [
                        (
                            "missing_adapter",
                            FunctionTransformer(normalize_missing, feature_names_out="one-to-one"),
                        ),
                        (
                            "imputer",
                            SimpleImputer(
                                strategy=numeric_strategy,
                                add_indicator=True,
                                keep_empty_features=True,
                            ),
                        ),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric,
            )
        )
    if categorical:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        (
                            "missing_adapter",
                            FunctionTransformer(normalize_missing, feature_names_out="one-to-one"),
                        ),
                        (
                            "imputer",
                            SimpleImputer(
                                strategy="constant",
                                fill_value="__MISSING__",
                                keep_empty_features=True,
                            ),
                        ),
                        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
                    ]
                ),
                categorical,
            )
        )
    return ColumnTransformer(transformers, remainder="drop", sparse_threshold=1.0)
