"""Validar e incorporar os ZIPs locais entregues, preservando as execuções científicas."""

import argparse
import csv
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from enem_base.provenance import sha256_file, verify_sha256, write_json


def incorporate(downloads, raw, evidence):
    if evidence.exists():
        raise FileExistsError("Preservar a evidência anterior; escolher nova saída")
    historical = json.loads(Path("docs/referencias/fonte_enem2023.json").read_text())
    names = ["microdados_enem_2023.zip", "competencias_redacao_enem_2023.zip"]
    packages = []
    for name in names:
        source = downloads / name
        digest = sha256_file(source)
        if name == names[0] and digest != historical["sha256"]:
            raise ValueError("ZIP nacional diferente da fonte histórica; investigar antes de mover")
        with zipfile.ZipFile(source) as z:
            bad = z.testzip()
            if bad:
                raise ValueError(f"CRC inválido: {bad}")
            for member in z.infolist():
                parts = Path(member.filename).parts
                if member.filename.startswith("/") or ".." in parts:
                    raise ValueError("Caminho inseguro no ZIP")
        packages.append(
            {
                "source": str(source),
                "destination": str(raw / name),
                "sha256": digest,
                "bytes": source.stat().st_size,
                "crc_all_members_passed": True,
            }
        )
    raw.mkdir(parents=True, exist_ok=True)
    extracted = []
    for package in packages:
        source, destination = Path(package["source"]), Path(package["destination"])
        if destination.exists():
            raise FileExistsError(f"Destino existente; não sobrescrever: {destination}")
        shutil.move(str(source), destination)
        verify_sha256(destination, package["sha256"], "ZIP alterado durante movimentação")
        with zipfile.ZipFile(destination) as z:
            for member in z.infolist():
                if member.is_dir():
                    continue
                if destination.name == names[0]:
                    if member.filename.endswith("/DADOS/MICRODADOS_ENEM_2023.csv"):
                        target = raw / "MICRODADOS_ENEM_2023.csv"
                    elif (
                        "/DICIONÁRIO/" in member.filename
                        or "/LEIA-ME E DOCUMENTOS TÉCNICOS/" in member.filename
                    ):
                        target = (
                            raw
                            / "documentacao_enem2023"
                            / Path(member.filename).relative_to("microdados_enem_2023")
                        )
                    else:
                        continue
                else:
                    target = raw / "complementos" / member.filename
                if target.exists():
                    raise FileExistsError(f"Extração não sobrescreve: {target}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(member) as src, target.open("xb") as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)
                if target.stat().st_size != member.file_size:
                    raise ValueError("Tamanho extraído incorreto")
                extracted.append(
                    {
                        "archive": str(destination),
                        "member": member.filename,
                        "file": str(target),
                        "bytes": target.stat().st_size,
                        "sha256": sha256_file(target),
                    }
                )
    original = next(x for x in extracted if Path(x["file"]).name == "MICRODADOS_ENEM_2023.csv")
    expected = next(x for x in historical["extracted"] if x["file"] == "MICRODADOS_ENEM_2023.csv")
    if original["sha256"] != expected["sha256"]:
        raise ValueError("CSV diferente da fonte histórica")
    complement = next(
        x for x in extracted if Path(x["file"]).name == "COMPETENCIAS_REDACAO_2023.csv"
    )
    with Path(complement["file"]).open(encoding="latin-1", newline="") as stream:
        header = next(csv.reader(stream, delimiter=";"))
    report = {
        "status": "passed",
        "incorporated_at": datetime.now(ZoneInfo("America/Fortaleza")).isoformat(),
        "method": (
            "ZIPs locais fornecidos pelo usuário; CRC de todos os membros e SHA-256; "
            "movimentação e extração seletiva"
        ),
        "packages": packages,
        "extracted": extracted,
        "national_archive_matches_historical_sha256": True,
        "national_csv_matches_historical_sha256": True,
        "complement_columns": header,
        "complement_used_for_modeling": False,
        "reason_complement_excluded": (
            "Competências e resultados da correção da redação "
            "não são preditores permitidos para estimar NU_NOTA_CN."
        ),
        "new_training": False,
        "new_test_evaluation": False,
    }
    evidence.parent.mkdir(parents=True, exist_ok=True)
    write_json(evidence, report)
    write_json(raw / "incorporacao_local_2026-11-07.json", report)
    source_manifest = {
        **historical,
        "archive": str(raw / names[0]),
        "extracted": [x for x in extracted if x["archive"] == str(raw / names[0])],
        "local_incorporation": str(evidence),
        "local_incorporated_at": report["incorporated_at"],
        "method": report["method"],
    }
    write_json(raw / "enem2023.source.json", source_manifest)
    print(
        json.dumps(
            {
                "status": "passed",
                "packages_moved": 2,
                "files_extracted": len(extracted),
                "raw_csv_sha256": original["sha256"],
                "complement_columns": header,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads", type=Path, required=True)
    parser.add_argument("--raw", type=Path, default=Path("dados/raw"))
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    incorporate(args.downloads, args.raw, args.evidence)
