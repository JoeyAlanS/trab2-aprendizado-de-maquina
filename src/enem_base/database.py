"""Banco SQLite local: base limpa completa, partições e resultados do desenvolvimento."""

import json
import logging
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pyarrow as pa

from enem_base.dashboard import DashboardData, load_dashboard, read_json, statistics
from enem_base.provenance import sha256_file, write_json
from enem_base.relations import RelationData, load_relations
from enem_base.study import StudyConfig, verified_dataset

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DatabaseData:
    dashboard: DashboardData
    relations: RelationData
    manifest: dict


def _identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


@contextmanager
def readonly_connection(path: Path) -> Iterator[sqlite3.Connection]:
    """URI somente leitura: o frontend não pode modificar o banco."""
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        connection.execute("PRAGMA query_only = ON")
        yield connection
    finally:
        connection.close()


def build_database(
    config: StudyConfig, output: Path, dashboard_dir: Path, relations_dir: Path
) -> dict:
    if output.exists():
        raise FileExistsError("Banco existente: use outra saída para preservar a versão atual.")
    dashboard = load_dashboard(dashboard_dir)
    relations = load_relations(relations_dir, dashboard.manifest)
    dataset, ingestion = verified_dataset(config)
    partition_file = config.splits / "particoes.parquet"
    if (
        ingestion["source_sha256"] != dashboard.manifest["source_sha256"]
        or sha256_file(partition_file) != dashboard.manifest["splits_sha256"]
    ):
        raise ValueError("Fonte, partições e resultados não correspondem ao mesmo estudo.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".sqlite-", dir=output.parent) as temp:
        staging = Path(temp) / "database"
        staging.mkdir()
        db_path = staging / "enem2023.sqlite3"
        with closing(sqlite3.connect(db_path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA user_version = 1")
            connection.execute("PRAGMA cache_size = -65536")
            definitions = [
                f"{_identifier(field.name)} "
                + ("REAL" if pa.types.is_floating(field.type) else "TEXT")
                + (" NOT NULL" if field.name == config.identifier else "")
                for field in dataset.schema
            ]
            connection.execute("CREATE TABLE participantes (" + ", ".join(definitions) + ")")
            placeholders = ",".join("?" for _ in dataset.schema)
            insert = f"INSERT INTO participantes VALUES ({placeholders})"
            total = 0
            for batch in dataset.scanner(batch_size=25000).to_batches():
                # Arrow mantém texto/código, NULL e zero sem imputação ou arredondamento.
                columns = [column.to_pylist() for column in batch.columns]
                connection.executemany(insert, zip(*columns, strict=True))
                total += batch.num_rows
                connection.commit()
                if total % 250000 == 0:
                    logger.info("SQLite: %s registros limpos importados", total)
            if total != ingestion["rows"]:
                raise ValueError("Contagem importada difere da fonte preparada.")
            connection.execute(
                "CREATE UNIQUE INDEX idx_participantes_id ON participantes ("
                + _identifier(config.identifier)
                + ")"
            )
            connection.execute(
                "CREATE TABLE particoes ("
                + _identifier(config.identifier)
                + " TEXT PRIMARY KEY REFERENCES participantes("
                + _identifier(config.identifier)
                + "), partition TEXT NOT NULL CHECK(partition IN ('development','test')), "
                "validation_fold INTEGER, CHECK((partition='test' AND validation_fold IS NULL) "
                "OR (partition='development' AND validation_fold IN (0,1,2)))) WITHOUT ROWID"
            )
            partitions = pd.read_parquet(partition_file)
            partitions.to_sql(
                "particoes", connection, if_exists="append", index=False, chunksize=25000
            )
            connection.execute(
                "CREATE INDEX idx_particoes_conjunto ON particoes(partition, validation_fold)"
            )
            inputs = [config.identifier, config.target, *config.features]
            selection = ", ".join("p." + _identifier(name) for name in inputs)
            connection.execute(
                "CREATE VIEW desenvolvimento AS SELECT "
                + selection
                + ", f.validation_fold FROM participantes p JOIN particoes f ON p."
                + _identifier(config.identifier)
                + "=f."
                + _identifier(config.identifier)
                + " WHERE f.partition='development'"
            )
            connection.execute(
                "CREATE VIEW contagens_particoes AS SELECT partition, COUNT(*) AS participantes "
                "FROM particoes GROUP BY partition"
            )
            frames = {
                "agregados_desenvolvimento": dashboard.cube,
                "resumo_cv": dashboard.cv,
                "dobras_cv": dashboard.folds,
                "relacoes_alvo": relations.target,
                "associacoes_entradas": relations.pairs,
                "perfis": relations.profiles,
                "cruzamentos": relations.cells,
            }
            for name, frame in frames.items():
                frame.to_sql(name, connection, index=False)
            dictionary = read_json(config.dictionary) if config.dictionary else {"columns": {}}
            pd.DataFrame(
                [
                    {
                        "variavel": name,
                        "descricao": item.get("description", name),
                        "tipo_declarado": item.get("declared_type", ""),
                        "alternativas_json": json.dumps(
                            item.get("categories", {}), ensure_ascii=False
                        ),
                    }
                    for name, item in dictionary["columns"].items()
                ]
            ).to_sql("dicionario", connection, index=False)
            metadata = {
                "dashboard": dashboard.manifest,
                "relations": relations.manifest,
                "eda": dashboard.eda,
                "quality": dashboard.quality,
                "dictionary": dashboard.dictionary,
                "ingestion": ingestion,
            }
            connection.execute(
                "CREATE TABLE metadados(chave TEXT PRIMARY KEY, valor TEXT NOT NULL)"
            )
            connection.executemany(
                "INSERT INTO metadados VALUES (?,?)",
                [
                    (key, json.dumps(value, ensure_ascii=False, allow_nan=False))
                    for key, value in metadata.items()
                ],
            )
            counts = dict(
                connection.execute("SELECT partition, participantes FROM contagens_particoes")
            )
            population = dashboard.manifest["population"]
            if counts != {"development": population["development"], "test": population["test"]}:
                raise ValueError("Partições do banco diferem do protocolo.")
            missing, zeros = connection.execute(
                "SELECT SUM("
                + _identifier(config.target)
                + " IS NULL), SUM("
                + _identifier(config.target)
                + " = 0) FROM participantes"
            ).fetchone()
            # Apenas contagens de diagnóstico da ingestão; nenhuma média ou modelo no teste.
            if missing != population["missing_target"]:
                raise ValueError("As ausências do alvo não foram preservadas no banco.")
            if connection.execute("PRAGMA quick_check").fetchone() != ("ok",):
                raise ValueError("A integridade física do SQLite foi reprovada.")
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise ValueError("Partições com identificador sem correspondência.")
            connection.commit()
            schema = "\n\n".join(
                row[0] + ";"
                for row in connection.execute(
                    "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type,name"
                )
            )
            (staging / "schema.sql").write_text(schema + "\n", encoding="utf-8", newline="\n")
        manifest = {
            "version": 1,
            "status": "completed",
            "created_at_utc": datetime.now(UTC).isoformat(),
            "file": db_path.name,
            "sha256": sha256_file(db_path),
            "bytes": db_path.stat().st_size,
            "source_sha256": ingestion["source_sha256"],
            "splits_sha256": dashboard.manifest["splits_sha256"],
            "target": config.target,
            "test_evaluated": False,
            "rows": total,
            "columns": len(dataset.schema),
            "partitions": counts,
            "missing_target": missing,
            "zero_target": zeros,
            "tables": {
                "participantes": total,
                "particoes": len(partitions),
                **{name: len(frame) for name, frame in frames.items()},
                "dicionario": len(dictionary["columns"]),
                "metadados": len(metadata),
            },
            "validation": {"quick_check": "ok", "foreign_key_check": "passed"},
        }
        write_json(staging / "manifesto.json", manifest)
        load_database(db_path)
        staging.rename(output)
    return manifest


def load_database(path: Path) -> DatabaseData:
    manifest = read_json(path.parent / "manifesto.json")
    if (
        manifest.get("version") != 1
        or manifest.get("status") != "completed"
        or manifest.get("test_evaluated") is not False
        or manifest.get("file") != path.name
        or manifest.get("bytes") != path.stat().st_size
        or sha256_file(path) != manifest.get("sha256")
    ):
        raise ValueError("Banco ausente, alterado ou sem manifesto válido.")
    with readonly_connection(path) as connection:
        metadata = {
            key: json.loads(value)
            for key, value in connection.execute("SELECT chave,valor FROM metadados")
        }
        d, r = metadata["dashboard"], metadata["relations"]
        if (
            d["test_evaluated"] is not False
            or r["test_evaluated"] is not False
            or d["source_sha256"] != manifest["source_sha256"]
            or d["splits_sha256"] != manifest["splits_sha256"]
            or any(
                d[key] != r[key]
                for key in (
                    "source_sha256",
                    "splits_sha256",
                    "study_sha256",
                    "dictionary_sha256",
                    "target",
                    "n_development",
                )
            )
        ):
            raise ValueError("Metadados inconsistentes no banco do estudo.")
        # Não há SELECT sobre participantes ou sobre a view de indivíduos nesta leitura do frontend.
        frames = {
            name: pd.read_sql_query(f'SELECT * FROM "{name}"', connection)
            for name in (
                "agregados_desenvolvimento",
                "resumo_cv",
                "dobras_cv",
                "relacoes_alvo",
                "associacoes_entradas",
                "perfis",
                "cruzamentos",
            )
        }
    if statistics(frames["agregados_desenvolvimento"])["count"] != d["n_development"]:
        raise ValueError("Agregados SQLite inconsistentes com o desenvolvimento.")
    dashboard = DashboardData(
        {**d, "storage": "sqlite", "database_file": str(path)},
        frames["agregados_desenvolvimento"],
        metadata["eda"],
        metadata["quality"],
        metadata["dictionary"],
        frames["resumo_cv"],
        frames["dobras_cv"],
    )
    relations = RelationData(
        r,
        frames["relacoes_alvo"],
        frames["associacoes_entradas"],
        frames["perfis"],
        frames["cruzamentos"],
    )
    return DatabaseData(dashboard, relations, manifest)
