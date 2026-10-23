from dataclasses import replace
from pathlib import Path

import pytest

from enem_base.config import load_config

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def example_config(tmp_path):
    return replace(load_config(ROOT / "configs/exemplo.toml"), output=tmp_path / "dataset")


@pytest.fixture
def csv_config(example_config, tmp_path):
    def factory(text, **overrides):
        source = tmp_path / "input.csv"
        source.write_text(text, encoding="utf-8")
        return replace(
            example_config,
            source=source,
            expected_rows=None,
            expected_columns=None,
            required_columns=("registro_id",),
            numeric_columns=("medida_a",),
            chunksize=2,
            **overrides,
        )

    return factory
