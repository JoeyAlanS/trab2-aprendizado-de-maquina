"""Comparar o CSV original normalizado com todos os Parquets já usados no estudo."""

import argparse
import json
from pathlib import Path

import pandas as pd

from enem_base.cleaning import normalize_chunk
from enem_base.config import load_config
from enem_base.provenance import sha256_file, verify_sha256, write_json


def validate(config_path, output):
    if output.exists():
        raise FileExistsError("Evidência existente; preservar")
    config = load_config(config_path)
    manifest = json.loads((config.output / "manifesto.json").read_text())
    verify_sha256(config.source, manifest["source_sha256"], "Fonte diferente da preparação")
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
    checks = []
    eligible = zero = rows = 0
    with reader:
        for number, chunk in enumerate(reader):
            cleaned, changes = normalize_chunk(chunk, config)
            if cleaned.shape[1] != 76 or not cleaned.NU_ANO.eq(2023).all():
                raise ValueError("Contrato nacional não atendido")
            if any(changes["invalid_numeric"].values()):
                raise ValueError("Conversão numérica inválida")
            part = config.output / manifest["parts"][number]["file"]
            verify_sha256(part, manifest["parts"][number]["sha256"], "Parquet alterado")
            persisted = pd.read_parquet(part)
            pd.testing.assert_frame_equal(
                cleaned.reset_index(drop=True),
                persisted.reset_index(drop=True),
                check_dtype=False,
                check_exact=True,
            )
            rows += len(cleaned)
            eligible += int(cleaned.NU_NOTA_CN.notna().sum())
            zero += int(cleaned.NU_NOTA_CN.eq(0).sum())
            checks.append(
                {
                    "part": str(part),
                    "rows": len(cleaned),
                    "columns": 76,
                    "all_cells_equal_after_normalization": True,
                    "sha256": sha256_file(part),
                }
            )
            if number % 10 == 0:
                print(f"Conferidas {rows:,} linhas e todas as 76 colunas", flush=True)
    if (rows, eligible, zero, len(checks)) != (3933955, 2692427, 16547, 79):
        raise ValueError("Contagens nacionais divergentes")
    write_json(
        output,
        {
            "status": "passed",
            "source": str(config.source),
            "source_sha256": sha256_file(config.source),
            "rows": rows,
            "columns": 76,
            "eligible_cn": eligible,
            "missing_cn": rows - eligible,
            "zero_cn": zero,
            "all_cells_equal_after_normalization": True,
            "parts": checks,
            "models_retrained": False,
            "partitions_changed": False,
            "scientific_results_changed": False,
        },
    )
    print("Comparação integral aprovada; dados e resultados anteriores preservados.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/enem2023.toml"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate(args.config, args.output)
