import json
from dataclasses import replace

import pandas as pd
import pytest

from enem_base.ingestion import prepare
from enem_base.provenance import sha256_file
from enem_base.quality import DataQualityError


def test_end_to_end_preserves_rows_zero_codes_and_source(example_config):
    before = sha256_file(example_config.source)
    manifest = prepare(example_config)
    parts = sorted(example_config.output.glob("*.parquet"))
    data = pd.concat([pd.read_parquet(part) for part in parts], ignore_index=True)
    report = json.loads((example_config.output / "qualidade.json").read_text(encoding="utf-8"))
    assert len(data) == 12
    assert len(parts) == 3
    assert data.loc[0, "codigo_local"] == "001"
    assert data.loc[0, "categoria"] == "A"
    assert data.loc[3, "medida_a"] == 0
    assert pd.isna(data.loc[2, "medida_a"])
    assert report["missing"]["medida_b"] == 2
    assert report["numeric"]["medida_a"]["zeros"] == 1
    assert report["rows_removed"] == 0
    assert report["status"] == "passed"
    assert manifest["source_sha256"] == before == sha256_file(example_config.source)
    assert manifest["target"] is None and not manifest["models_trained"]
    assert all(
        sha256_file(example_config.output / p["file"]) == p["sha256"] for p in manifest["parts"]
    )


def test_repeated_runs_require_new_output(example_config):
    prepare(example_config)
    original = sha256_file(example_config.output / "manifesto.json")
    with pytest.raises(FileExistsError):
        prepare(example_config)
    assert sha256_file(example_config.output / "manifesto.json") == original


def test_numeric_error_does_not_publish_partial_output(csv_config):
    config = csv_config("registro_id;medida_a\na;1\nb;2\nc;inválido\n")
    with pytest.raises(DataQualityError) as caught:
        prepare(config)
    assert caught.value.report["rows"] == 3
    assert caught.value.report["invalid_numeric"]["medida_a"] == 1
    assert not config.output.exists()
    assert not list(config.output.parent.glob(".preparacao-*"))


def test_duplicates_across_chunks_are_counted_and_never_silently_removed(csv_config):
    config = csv_config("registro_id;medida_a\na;1\nb;2\na;1\n")
    with pytest.raises(DataQualityError) as caught:
        prepare(config)
    report = caught.value.report
    assert report["duplicate_identifiers"] == 1
    assert report["duplicate_rows"] == 1
    assert report["rows_removed"] == 0
    assert not config.output.exists()


@pytest.mark.parametrize(
    "text",
    [
        "registro_id;medida_a\na;1;extra\n",
        "registro_id;medida_a\na\n",
        "registro_id;medida_a\na;1\n\n",
        "registro_id;medida_a;medida_a\na;1;2\n",
        "registro_id;medida_a;\na;1;2\n",
        "registro_id; medida_a\na;1\n",
    ],
)
def test_malformed_csv_is_rejected(csv_config, text):
    config = csv_config(text)
    with pytest.raises(ValueError):
        prepare(config)
    assert not config.output.exists()


@pytest.mark.parametrize("value", ["inf", "-inf", "NaN", "texto"])
def test_nonfinite_and_invalid_numbers_are_errors(csv_config, value):
    with pytest.raises(DataQualityError):
        prepare(csv_config(f"registro_id;medida_a\na;{value}\n"))


def test_missing_id_and_row_count_fail(csv_config):
    config = replace(csv_config("registro_id;medida_a\n;1\n"), expected_rows=2)
    with pytest.raises(DataQualityError) as caught:
        prepare(config)
    assert caught.value.report["missing_identifiers"] == 1
    assert len(caught.value.report["errors"]) == 2


def test_year_validation_and_decimal_comma(csv_config):
    config = csv_config(
        "registro_id;medida_a;ano\na;1,5;2023\nb;0;2022\n",
        decimal=",",
        year_column="ano",
        expected_year=2023,
    )
    with pytest.raises(DataQualityError) as caught:
        prepare(config)
    assert caught.value.report["invalid_year"] == 1
    assert caught.value.report["numeric"]["medida_a"]["max"] == 1.5


def test_header_only_fails(csv_config):
    with pytest.raises(DataQualityError):
        prepare(csv_config("registro_id;medida_a\n"))


def test_missing_required_column(csv_config):
    with pytest.raises(ValueError, match="Colunas obrigatórias"):
        prepare(csv_config("outra;medida_a\na;1\n"))


def test_blank_identifier_is_rejected_even_without_missing_markers(csv_config):
    config = csv_config("registro_id;medida_a\n ;1\n", missing_tokens=())
    with pytest.raises(DataQualityError) as caught:
        prepare(config)
    assert caught.value.report["missing_identifiers"] == 1
