"""Particionamento futuro: 80/20 e três dobras no desenvolvimento.

O chamador precisa informar um alvo. Este módulo não lê features, não ajusta
transformações e não calcula estatísticas do teste.
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, train_test_split

from enem_base.features import require_target
from enem_base.provenance import sha256_file, write_json


def make_split_table(
    frame: pd.DataFrame, *, identifier: str, target: str | None, kind: str
) -> tuple[pd.DataFrame, dict]:
    target = require_target(target, kind=kind)
    if identifier == target:
        raise ValueError("Identificador e alvo devem ser diferentes.")
    ids = frame[identifier].astype("string")
    if ids.isna().any() or ids.str.strip().eq("").any() or ids.duplicated().any():
        raise ValueError("As partições exigem identificadores não vazios e únicos.")
    observed = pd.to_numeric(frame[target], errors="coerce")
    invalid = frame[target].notna() & (observed.isna() | ~np.isfinite(observed))
    if invalid.any():
        raise ValueError("O alvo contém valores não numéricos ou não finitos.")
    eligible = ids[observed.notna()].reset_index(drop=True)
    if len(eligible) < 5:
        raise ValueError("São necessários ao menos cinco registros elegíveis para três dobras.")
    development, test = train_test_split(np.arange(len(eligible)), test_size=0.2, random_state=42)
    partition = pd.DataFrame(
        {
            identifier: eligible,
            "partition": "test",
            "validation_fold": pd.Series(pd.NA, index=eligible.index, dtype="Int64"),
        }
    )
    partition.loc[development, "partition"] = "development"
    for fold, (_, validation) in enumerate(
        KFold(3, shuffle=True, random_state=42).split(development)
    ):
        partition.loc[development[validation], "validation_fold"] = fold
    summary = {
        "kind": kind,
        "target": target,
        "identifier": identifier,
        "seed": 42,
        "test_size": 0.2,
        "n_splits": 3,
        "shuffle": True,
        "source_rows": len(frame),
        "eligible": len(eligible),
        "missing_target": int(observed.isna().sum()),
        "development": len(development),
        "test": len(test),
        "rule": "Alvo observado; zero é elegível; outras notas não são exigidas.",
    }
    return partition, summary


def save_splits(
    frame: pd.DataFrame,
    output: Path,
    *,
    identifier: str,
    target: str | None,
    kind: str,
    source_sha256: str,
) -> dict:
    if len(source_sha256) != 64 or any(c not in "0123456789abcdef" for c in source_sha256.lower()):
        raise ValueError("Informe o SHA-256 da fonte usada nas partições.")
    if output.exists():
        raise FileExistsError("Partições existentes são preservadas; escolha outro diretório.")
    table, summary = make_split_table(frame, identifier=identifier, target=target, kind=kind)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".splits-", dir=output.parent) as temp:
        staged = Path(temp) / "splits"
        staged.mkdir()
        path = staged / "particoes.parquet"
        table.to_parquet(path, index=False)
        summary.update(source_sha256=source_sha256, partitions_sha256=sha256_file(path))
        write_json(staged / "manifesto.json", summary)
        staged.rename(output)
    return summary
