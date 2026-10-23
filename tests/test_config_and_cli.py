import json
from dataclasses import replace

import pytest
from conftest import ROOT

from enem_base.cli import main
from enem_base.config import load_config


def test_official_contract_has_no_selected_target():
    config = load_config(ROOT / "configs/enem2023.toml")
    assert config.expected_rows == 3933955 and config.expected_columns == 76
    assert config.expected_year == 2023
    assert config.source == ROOT / "dados/raw/MICRODADOS_ENEM_2023.csv"
    assert not hasattr(config, "target")


@pytest.mark.parametrize(
    "old,new",
    [
        ("chunksize = 4", "chunksize = 0"),
        ('kind = "synthetic"', 'kind = "enem2023"'),
        ('numeric_columns = ["medida_a", "medida_b"]', 'numeric_columns = ["registro_id"]'),
        ('separator = ";"', 'separator = "xx"'),
    ],
)
def test_invalid_config_rejected(tmp_path, old, new):
    text = (ROOT / "configs/exemplo.toml").read_text(encoding="utf-8")
    config = tmp_path / "config.toml"
    config.write_text(text.replace(old, new), encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(config)


def test_cli_processes_config_with_explicit_relative_root(tmp_path, capsys):
    # Criar contrato fora da raiz comprova que a origem não depende do cwd.
    text = (ROOT / "configs/exemplo.toml").read_text(encoding="utf-8")
    text = text.replace('root = ".."', 'root = "' + ROOT.as_posix() + '"')
    text = text.replace(
        'output = "dados/processed/exemplo-v1"',
        'output = "' + (tmp_path / "output").as_posix() + '"',
    )
    path = tmp_path / "example.toml"
    path.write_text(text, encoding="utf-8")
    assert main(["prepare", "--config", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["target"] is None
    assert main(["prepare", "--config", str(path)]) == 2
    assert "já existe" in capsys.readouterr().err


def test_cli_quality_failure_is_machine_readable(example_config, tmp_path, monkeypatch, capsys):
    from enem_base import cli

    config = replace(example_config, expected_rows=999)
    monkeypatch.setattr(cli, "load_config", lambda _: config)
    assert main(["prepare", "--config", str(tmp_path / "unused.toml")]) == 2
    report = json.loads(capsys.readouterr().err)
    assert report["status"] == "failed" and report["rows"] == 12
