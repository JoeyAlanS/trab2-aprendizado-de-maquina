"""Contrato do estudo e acesso verificado aos dados preparados."""

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

from enem_base.features import require_target, validate_features
from enem_base.provenance import sha256_file
from enem_base.splits import save_splits


@dataclass(frozen=True)
class StudyConfig:
    config_path: Path
    theme: str
    target: str
    identifier: str
    kind: str
    dataset: Path
    splits: Path
    results: Path
    numeric: tuple[str, ...]
    categorical: tuple[str, ...]
    dictionary: Path | None = None

    @property
    def features(self) -> list[str]:
        return list(self.numeric + self.categorical)


def load_study(path: Path) -> StudyConfig:
    path = path.resolve()
    content = tomllib.loads(path.read_text(encoding="utf-8"))
    if set(content) != {"project", "study", "paths", "protocol", "features"}:
        raise ValueError("Seções inválidas no contrato de pesquisa.")
    root = (path.parent / content["project"]["root"]).resolve()
    study, protocol = content["study"], content["protocol"]
    if protocol != {"seed": 42, "test_size": 0.2, "n_splits": 3}:
        raise ValueError("O estudo deve preservar 80/20, semente 42 e três dobras.")
    target = require_target(study["target"], kind=study["kind"])
    config = StudyConfig(
        config_path=path,
        theme=study["theme"],
        target=target,
        identifier=study["identifier"],
        kind=study["kind"],
        **{key: (root / value).resolve() for key, value in content["paths"].items()},
        numeric=tuple(content["features"]["numeric"]),
        categorical=tuple(content["features"]["categorical"]),
    )
    validate_features(config.features, identifier=config.identifier, target=target)
    return config


def verified_dataset(config: StudyConfig) -> tuple[ds.Dataset, dict]:
    """Conferir os hashes de todas as partes antes de usar resultados científicos."""
    manifest = json.loads((config.dataset / "manifesto.json").read_text(encoding="utf-8"))
    quality = json.loads((config.dataset / "qualidade.json").read_text(encoding="utf-8"))
    if manifest["kind"] != config.kind or quality["status"] != "passed":
        raise ValueError("Tipo de dados ou aprovação da qualidade incompatível com o estudo.")
    if config.kind == "enem2023":
        if config.dictionary is None:
            raise ValueError("O estudo oficial exige referência ao dicionário conferido.")
        dictionary = json.loads(config.dictionary.read_text(encoding="utf-8"))
        missing = set(config.features + [config.target, config.identifier]) - set(
            dictionary["columns"]
        )
        if missing:
            raise ValueError(f"Variáveis ausentes do dicionário oficial: {sorted(missing)}")
    parts = []
    for part in manifest["parts"]:
        path = config.dataset / part["file"]
        if path.parent != config.dataset or sha256_file(path) != part["sha256"]:
            raise ValueError("Parte Parquet alterada ou caminho inválido no manifesto.")
        parts.append(str(path))
    dataset = ds.dataset(parts, format="parquet")
    if dataset.count_rows() != manifest["rows"]:
        raise ValueError("Contagem do dataset difere do manifesto.")
    return dataset, manifest


def create_study_splits(config: StudyConfig) -> dict:
    dataset, manifest = verified_dataset(config)
    columns = [config.identifier, config.target]
    frame = dataset.to_table(columns=columns).to_pandas()
    return save_splits(
        frame,
        config.splits,
        identifier=config.identifier,
        target=config.target,
        kind=config.kind,
        source_sha256=manifest["source_sha256"],
    )


def load_development(config: StudyConfig) -> tuple[pd.DataFrame, dict]:
    """Filtrar os IDs de desenvolvimento antes de ler as features e o alvo.

    O manifesto e as partições são verificados; nenhuma estatística do teste é lida.
    A ordenação dos IDs de desenvolvimento é a da fonte, persistida em particoes.parquet.
    """
    dataset, source_manifest = verified_dataset(config)
    split_manifest = json.loads((config.splits / "manifesto.json").read_text(encoding="utf-8"))
    split_path = config.splits / "particoes.parquet"
    if (
        split_manifest["target"] != config.target
        or split_manifest["identifier"] != config.identifier
        or split_manifest["kind"] != config.kind
        or split_manifest["source_sha256"] != source_manifest["source_sha256"]
        or sha256_file(split_path) != split_manifest["partitions_sha256"]
    ):
        raise ValueError("As partições não correspondem ao alvo e à fonte atuais.")
    partitions = pd.read_parquet(split_path)
    development = partitions.loc[partitions.partition.eq("development")].copy()
    if len(development) != split_manifest["development"]:
        raise ValueError("Contagem de desenvolvimento difere do manifesto.")
    selected = ds.field(config.identifier).isin(development[config.identifier].tolist())
    columns = [config.identifier, config.target] + config.features
    # O filtro no scanner mantém fora da tabela retornada as linhas reservadas.
    frame = dataset.to_table(columns=columns, filter=selected).to_pandas()
    frame = development.merge(frame, on=config.identifier, how="left", validate="one_to_one")
    if frame[config.target].isna().any() or not np.isfinite(frame[config.target]).all():
        raise ValueError("Participantes do desenvolvimento sem alvo numérico observado.")
    if set(frame.validation_fold) != {0, 1, 2}:
        raise ValueError("As três dobras persistidas devem estar presentes.")
    for name in config.numeric:
        original = frame[name]
        converted = pd.to_numeric(original, errors="coerce")
        invalid = original.notna() & (converted.isna() | ~np.isfinite(converted))
        if invalid.any():
            raise ValueError(f"Feature numérica inválida: {name}")
        frame[name] = converted.astype("Float64")
    if config.dictionary is not None:
        dictionary = json.loads(config.dictionary.read_text(encoding="utf-8"))
        for name in config.categorical:
            allowed = set(dictionary["columns"][name]["categories"])
            if allowed and not frame[name].dropna().isin(allowed).all():
                raise ValueError(f"Categoria fora do dicionário no desenvolvimento: {name}")
        if "Q005" in config.numeric and not frame.Q005.dropna().between(1, 20).all():
            raise ValueError("Q005 fora das alternativas 1 a 20 do dicionário.")
    return frame, {
        "source_sha256": source_manifest["source_sha256"],
        "splits_sha256": split_manifest["partitions_sha256"],
        "study_sha256": sha256_file(config.config_path),
        "dictionary_sha256": sha256_file(config.dictionary) if config.dictionary else None,
        "target": config.target,
        "n_development": len(frame),
        "test_evaluated": False,
    }
