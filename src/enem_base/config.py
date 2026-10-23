"""Configuração explícita; caminhos relativos à raiz declarada no TOML."""

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataConfig:
    source: Path
    output: Path
    kind: str
    identifier: str
    separator: str
    encoding: str
    decimal: str
    chunksize: int
    missing_tokens: tuple[str, ...]
    numeric_columns: tuple[str, ...]
    required_columns: tuple[str, ...]
    expected_rows: int | None
    expected_columns: int | None
    year_column: str | None
    expected_year: int | None
    config_path: Path


def load_config(path: Path) -> DataConfig:
    path = path.resolve()
    with path.open("rb") as stream:
        content = tomllib.load(stream)
    if set(content) != {"project", "data"}:
        raise ValueError("O TOML deve conter somente as seções project e data.")
    if set(content["project"]) != {"root"}:
        raise ValueError("project deve declarar somente root.")
    root = (path.parent / content["project"]["root"]).resolve()
    values = dict(content["data"])
    for key in ("source", "output"):
        values[key] = (root / values[key]).resolve()
    for key in ("missing_tokens", "numeric_columns", "required_columns"):
        values[key] = tuple(values[key])
        if len(values[key]) != len(set(values[key])):
            raise ValueError(f"Itens repetidos em {key}.")
    for key in ("expected_rows", "expected_columns", "year_column", "expected_year"):
        values.setdefault(key, None)
    config = DataConfig(**values, config_path=path)
    if config.kind not in {"synthetic", "enem2023"}:
        raise ValueError("kind deve ser synthetic ou enem2023.")
    if type(config.chunksize) is not int or config.chunksize < 1:
        raise ValueError("chunksize deve ser um inteiro positivo.")
    for key in ("expected_rows", "expected_columns", "expected_year"):
        value = getattr(config, key)
        if value is not None and (type(value) is not int or value < 1):
            raise ValueError(f"{key} deve ser um inteiro positivo quando declarado.")
    if len(config.separator) != 1 or config.decimal not in {".", ","}:
        raise ValueError("Separador deve ter um caractere e decimal deve ser '.' ou ','.")
    if config.identifier not in config.required_columns:
        raise ValueError("O identificador deve constar em required_columns.")
    if config.identifier in config.numeric_columns:
        raise ValueError("Identificadores devem permanecer textuais.")
    if config.source == config.output or config.output in config.source.parents:
        raise ValueError("A saída não pode conter ou substituir a fonte.")
    if (config.year_column is None) != (config.expected_year is None):
        raise ValueError("year_column e expected_year devem ser declarados juntos.")
    if config.kind == "enem2023" and (
        config.identifier != "NU_INSCRICAO"
        or config.expected_rows != 3_933_955
        or config.expected_columns != 76
        or config.year_column != "NU_ANO"
        or config.expected_year != 2023
    ):
        raise ValueError("O contrato ENEM 2023 exige a edição e a base completa do enunciado.")
    return config
