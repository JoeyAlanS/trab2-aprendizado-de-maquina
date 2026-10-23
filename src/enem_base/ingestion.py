"""CSV completo em lotes -> Parquet, sem filtros por tema e sem imputação."""

import csv
import logging
import tempfile
import time
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from enem_base.cleaning import normalize_chunk
from enem_base.config import DataConfig
from enem_base.provenance import runtime_metadata, sha256_file, write_json
from enem_base.quality import DataQualityError, QualityTracker

logger = logging.getLogger(__name__)


def _validate_csv_rows(config: DataConfig, columns: list[str]) -> None:
    """Pandas aceita algumas linhas curtas; validar larguras antes de importar."""
    with config.source.open(encoding=config.encoding, newline="") as stream:
        reader = csv.reader(stream, delimiter=config.separator, strict=True)
        next(reader)
        for row in reader:
            if len(row) != len(columns):
                raise ValueError(
                    f"CSV malformado na linha física {reader.line_num}: "
                    f"{len(row)} campos; esperados {len(columns)}."
                )


def prepare(config: DataConfig) -> dict:
    started = time.perf_counter()
    if config.output.exists():
        raise FileExistsError(
            "A saída já existe. Use outro nome para preservar a execução anterior."
        )
    with config.source.open(encoding=config.encoding, newline="") as stream:
        columns = next(csv.reader(stream, delimiter=config.separator, strict=True), [])
    if (
        not columns
        or any(not name.strip() for name in columns)
        or len(set(columns)) != len(columns)
    ):
        raise ValueError("Cabeçalho vazio, com nomes vazios ou colunas duplicadas.")
    if any(name != name.strip() for name in columns):
        raise ValueError("Espaços no cabeçalho: corrija o contrato ou a origem explicitamente.")
    required = set(config.required_columns) | set(config.numeric_columns)
    if config.year_column:
        required.add(config.year_column)
    missing = required.difference(columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {sorted(missing)}")
    source_sha = sha256_file(config.source)
    _validate_csv_rows(config, columns)
    config.output.parent.mkdir(parents=True, exist_ok=True)
    schema = pa.schema(
        [
            (name, pa.float64() if name in config.numeric_columns else pa.string())
            for name in columns
        ]
    )
    with tempfile.TemporaryDirectory(prefix=".preparacao-", dir=config.output.parent) as temp:
        staging = Path(temp)
        dataset = staging / "dataset"
        dataset.mkdir()
        tracker = QualityTracker(staging / "quality.sqlite", columns, config)
        parts = []
        try:
            reader = pd.read_csv(
                config.source,
                sep=config.separator,
                encoding=config.encoding,
                dtype="string",
                keep_default_na=False,
                na_filter=False,
                chunksize=config.chunksize,
                on_bad_lines="error",
                skip_blank_lines=False,
            )
            with reader:
                for number, chunk in enumerate(reader):
                    cleaned, changes = normalize_chunk(chunk, config)
                    tracker.update(cleaned, changes)
                    part = dataset / f"part-{number:05d}.parquet"
                    table = pa.Table.from_pandas(cleaned, schema=schema, preserve_index=False)
                    pq.write_table(table, part, compression="zstd")
                    parts.append(
                        {"file": part.name, "rows": len(cleaned), "sha256": sha256_file(part)}
                    )
                    logger.info(
                        "Lote %s concluído; %s linhas contabilizadas",
                        number,
                        tracker.report["rows"],
                    )
            report = tracker.finish()
        finally:
            tracker.close()
        if sha256_file(config.source) != source_sha:
            raise ValueError("A fonte mudou durante a execução; saída descartada.")
        if report["errors"]:
            raise DataQualityError(report)
        manifest = {
            **runtime_metadata(),
            "kind": config.kind,
            "synthetic": config.kind == "synthetic",
            "source_file": config.source.name,
            "source_sha256": source_sha,
            "config_sha256": sha256_file(config.config_path),
            "configuration": {
                "separator": config.separator,
                "encoding": config.encoding,
                "decimal": config.decimal,
                "chunksize": config.chunksize,
                "missing_tokens": config.missing_tokens,
                "numeric_columns": config.numeric_columns,
                "identifier": config.identifier,
                "expected_rows": config.expected_rows,
                "expected_columns": config.expected_columns,
                "year_column": config.year_column,
                "expected_year": config.expected_year,
            },
            "rows": report["rows"],
            "columns": columns,
            "parts": parts,
            "elapsed_seconds": time.perf_counter() - started,
            "target": None,
            "models_trained": False,
        }
        write_json(dataset / "qualidade.json", report)
        write_json(dataset / "manifesto.json", manifest)
        dataset.rename(config.output)
    return manifest
