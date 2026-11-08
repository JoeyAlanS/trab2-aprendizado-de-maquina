"""Recuperação dos dados reais a partir de um SQLite identificado por SHA-256.

O CSV original não é recriado: os Parquet são uma exportação da base limpa.
IDs/dobras são confrontados com o banco antes de publicar qualquer partição.
"""

import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from enem_base.database import load_database, readonly_connection
from enem_base.provenance import runtime_metadata, sha256_file, write_json
from enem_base.splits import make_split_table
from enem_base.study import StudyConfig

logger = logging.getLogger(__name__)


def recover_dataset(config: StudyConfig, database: Path) -> dict:
    """Exportar todas as linhas, sem sobrescrever dados nem alterar o banco."""
    if config.kind != "enem2023":
        raise ValueError("A recuperação exige o estudo oficial ENEM 2023.")
    if config.dataset.exists() or config.splits.exists():
        raise FileExistsError("Dataset/partições já existem; preserve-os e escolha novas saídas.")
    data = load_database(database)
    if data.manifest["target"] != config.target:
        raise ValueError("O alvo do banco não corresponde ao estudo.")
    config.dataset.parent.mkdir(parents=True, exist_ok=True)
    config.splits.parent.mkdir(parents=True, exist_ok=True)
    with (
        readonly_connection(database) as connection,
        TemporaryDirectory(prefix=".recovery-", dir=config.dataset.parent) as work,
        TemporaryDirectory(prefix=".recovery-", dir=config.splits.parent) as split_work,
    ):
        ingestion = json.loads(
            connection.execute("SELECT valor FROM metadados WHERE chave='ingestion'").fetchone()[0]
        )
        if connection.execute("PRAGMA quick_check").fetchone() != ("ok",):
            raise ValueError("Integridade SQLite reprovada.")
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise ValueError("Partições sem correspondência no banco.")
        if ingestion["source_sha256"] != data.manifest["source_sha256"]:
            raise ValueError("A origem da ingestão difere do manifesto do banco.")
        columns = ingestion["columns"]
        numeric = set(ingestion["configuration"]["numeric_columns"])
        schema = pa.schema(
            [(name, pa.float64() if name in numeric else pa.string()) for name in columns]
        )
        staging = Path(work) / "dataset"
        staging.mkdir()
        parts = []
        for index, frame in enumerate(
            pd.read_sql_query(
                "SELECT * FROM participantes ORDER BY rowid", connection, chunksize=50000
            )
        ):
            if frame.columns.tolist() != columns:
                raise ValueError("Esquema do SQLite difere da ingestão registrada.")
            for name in columns:
                frame[name] = frame[name].astype("Float64" if name in numeric else "string")
            path = staging / f"part-{index:05d}.parquet"
            pq.write_table(
                pa.Table.from_pandas(frame, schema=schema, preserve_index=False),
                path,
                compression="zstd",
            )
            parts.append({"file": path.name, "rows": len(frame), "sha256": sha256_file(path)})
            if index % 10 == 0:
                logger.info("Recuperação: %s linhas exportadas", sum(p["rows"] for p in parts))
        rows = sum(p["rows"] for p in parts)
        if rows != ingestion["rows"] or rows != data.manifest["rows"] or len(columns) != 76:
            raise ValueError("Contagens recuperadas não correspondem à base nacional.")
        dataset = ds.dataset([str(staging / p["file"]) for p in parts], format="parquet")
        controls = dataset.to_table(columns=[config.identifier, config.target]).to_pandas()
        expected, split_summary = make_split_table(
            controls, identifier=config.identifier, target=config.target, kind=config.kind
        )
        del controls
        saved = pd.read_sql_query("SELECT * FROM particoes", connection)
        saved[config.identifier] = saved[config.identifier].astype("string")
        saved["validation_fold"] = saved.validation_fold.astype("Int64")
        if saved[config.identifier].duplicated().any() or len(saved) != len(expected):
            raise ValueError("Identificadores de partições inválidos.")
        aligned = saved.set_index(config.identifier).reindex(expected[config.identifier])
        if (
            not aligned.partition.reset_index(drop=True).eq(expected.partition).all()
            or not aligned.validation_fold.reset_index(drop=True)
            .fillna(-1)
            .eq(expected.validation_fold.fillna(-1))
            .all()
        ):
            raise ValueError(
                "Partições do banco não reproduzem o protocolo 80/20 e KFold(3), seed 42."
            )
        del saved, aligned
        split_staging = Path(split_work) / "splits"
        split_staging.mkdir()
        split_path = split_staging / "particoes.parquet"
        expected.to_parquet(split_path, index=False)
        recovery = {
            "database_file": database.name,
            "database_sha256": data.manifest["sha256"],
            "original_partitions_sha256": data.manifest["splits_sha256"],
            "partition_membership_verified": True,
            "raw_csv_recreated": False,
            "method": "Exportação integral da base limpa SQLite em ordem de ingestão",
        }
        split_summary.update(
            source_sha256=ingestion["source_sha256"],
            partitions_sha256=sha256_file(split_path),
            recovery=recovery,
        )
        write_json(split_staging / "manifesto.json", split_summary)
        quality = {
            **data.dashboard.quality,
            "kind": config.kind,
            "recovery": recovery,
            "validation_scope": "Hash e integridade do SQLite, esquema, contagens e partições; "
            "diagnóstico de ingestão preservado dos metadados históricos.",
        }
        write_json(staging / "qualidade.json", quality)
        manifest = {
            **ingestion,
            **runtime_metadata(),
            "parts": parts,
            "recovery": recovery,
            "original_ingestion": ingestion,
            "elapsed_seconds": None,
        }
        write_json(staging / "manifesto.json", manifest)
        staging.rename(config.dataset)
        split_staging.rename(config.splits)
    return {"status": "completed", "rows": rows, "parts": len(parts), **split_summary}
