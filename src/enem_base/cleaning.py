"""Transformações determinísticas sem aprender estatísticas da população."""

import numpy as np
import pandas as pd

from enem_base.config import DataConfig


def normalize_chunk(frame: pd.DataFrame, config: DataConfig) -> tuple[pd.DataFrame, dict]:
    cleaned = frame.copy()
    changes = {"trimmed_cells": 0, "missing_tokens_replaced": 0, "invalid_numeric": {}}
    for name in cleaned.columns:
        original = cleaned[name]
        trimmed = original.str.strip()
        changes["trimmed_cells"] += int(original.ne(trimmed).fillna(False).sum())
        mask = trimmed.isin(config.missing_tokens)
        changes["missing_tokens_replaced"] += int(mask.sum())
        cleaned[name] = trimmed.mask(mask, pd.NA)
    for name in config.numeric_columns:
        values = cleaned[name]
        if config.decimal == ",":
            values = values.str.replace(",", ".", regex=False)
        converted = pd.to_numeric(values, errors="coerce").astype("Float64")
        invalid = (values.notna() & converted.isna()) | (
            converted.notna() & ~np.isfinite(converted.fillna(0).to_numpy(dtype=float))
        )
        changes["invalid_numeric"][name] = int(invalid.sum())
        cleaned[name] = converted.mask(invalid, pd.NA)
    return cleaned, changes
