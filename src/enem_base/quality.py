"""Diagnóstico incremental e duplicatas globais com índice em disco."""

import hashlib
import json
import sqlite3
from pathlib import Path

import pandas as pd

from enem_base.config import DataConfig


class DataQualityError(ValueError):
    def __init__(self, report: dict):
        self.report = report
        super().__init__("Validação reprovada: " + "; ".join(report["errors"]))


class QualityTracker:
    """Memória limitada ao lote e às colunas; identidades persistidas em SQLite.

    Duplicatas de conteúdo usam SHA-256, com probabilidade residual de colisão.
    Identificadores repetidos são detectados por igualdade textual exata.
    """

    def __init__(self, path: Path, columns: list[str], config: DataConfig):
        self.config = config
        self.connection = sqlite3.connect(path)
        self.connection.execute("CREATE TABLE ids (value TEXT PRIMARY KEY) WITHOUT ROWID")
        self.connection.execute("CREATE TABLE rows (digest BLOB PRIMARY KEY) WITHOUT ROWID")
        self.report = {
            "status": "pending",
            "kind": config.kind,
            "rows": 0,
            "columns": columns,
            "column_count": len(columns),
            "missing": dict.fromkeys(columns, 0),
            "numeric": {},
            "invalid_numeric": dict.fromkeys(config.numeric_columns, 0),
            "duplicate_identifiers": 0,
            "duplicate_rows": 0,
            "missing_identifiers": 0,
            "invalid_year": 0,
            "trimmed_cells": 0,
            "missing_tokens_replaced": 0,
            "rows_removed": 0,
            "columns_removed": [],
            "columns_created": [],
            "errors": [],
        }

    def update(self, frame: pd.DataFrame, changes: dict) -> None:
        r = self.report
        r["rows"] += len(frame)
        for key in ("trimmed_cells", "missing_tokens_replaced"):
            r[key] += changes[key]
        for name in frame:
            r["missing"][name] += int(frame[name].isna().sum())
        for name in self.config.numeric_columns:
            r["invalid_numeric"][name] += changes["invalid_numeric"][name]
            observed = frame[name].dropna()
            entry = r["numeric"].setdefault(
                name, {"observed": 0, "zeros": 0, "min": None, "max": None}
            )
            entry["observed"] += len(observed)
            entry["zeros"] += int(observed.eq(0).sum())
            if len(observed):
                lo, hi = float(observed.min()), float(observed.max())
                entry["min"] = lo if entry["min"] is None else min(entry["min"], lo)
                entry["max"] = hi if entry["max"] is None else max(entry["max"], hi)
        if self.config.year_column:
            year = pd.to_numeric(frame[self.config.year_column], errors="coerce")
            r["invalid_year"] += int((year.isna() | year.ne(self.config.expected_year)).sum())
        ids = frame[self.config.identifier]
        r["missing_identifiers"] += int((ids.isna() | ids.eq("").fillna(False)).sum())
        with self.connection:
            present_ids = ids.dropna()
            before = self.connection.total_changes
            self.connection.executemany(
                "INSERT OR IGNORE INTO ids VALUES (?)", ((value,) for value in present_ids)
            )
            r["duplicate_identifiers"] += len(present_ids) - (
                self.connection.total_changes - before
            )
            # Normalizar a máscara de ausência vetorialmente evita uma chamada
            # pd.isna por célula (centenas de milhões na base nacional).
            canonical = frame.astype(object).where(frame.notna(), None)
            before = self.connection.total_changes
            self.connection.executemany(
                "INSERT OR IGNORE INTO rows VALUES (?)",
                (
                    (hashlib.sha256(json.dumps(row, ensure_ascii=False).encode()).digest(),)
                    for row in canonical.itertuples(index=False, name=None)
                ),
            )
            r["duplicate_rows"] += len(frame) - (self.connection.total_changes - before)

    def finish(self) -> dict:
        r = self.report
        c = self.config
        if not r["rows"]:
            r["errors"].append("Arquivo sem registros")
        if c.expected_rows is not None and r["rows"] != c.expected_rows:
            r["errors"].append(f"Esperadas {c.expected_rows} linhas; encontradas {r['rows']}")
        if c.expected_columns is not None and r["column_count"] != c.expected_columns:
            r["errors"].append(f"Esperadas {c.expected_columns} colunas")
        for key in ("duplicate_identifiers", "missing_identifiers", "invalid_year"):
            if r[key]:
                r["errors"].append(f"{key}: {r[key]}")
        for name, count in r["invalid_numeric"].items():
            if count:
                r["errors"].append(f"Conversão numérica inválida em {name}: {count}")
        r["status"] = "failed" if r["errors"] else "passed"
        return r

    def close(self) -> None:
        self.connection.close()
