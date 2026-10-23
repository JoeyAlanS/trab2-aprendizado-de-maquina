"""Obtenção e extração seletiva do pacote ENEM 2023, preservando arquivos originais."""

import shutil
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from enem_base.provenance import sha256_file, write_json

OFFICIAL_PAGE = "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem"
OFFICIAL_ARCHIVE = "https://download.inep.gov.br/microdados/microdados_enem_2023.zip"


def obtain_official(raw: Path) -> dict:
    raw = raw.resolve()
    raw.mkdir(parents=True, exist_ok=True)
    lock = raw / ".enem2023-download.lock"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(datetime.now(UTC).isoformat())
    try:
        return _obtain_official(raw)
    finally:
        lock.unlink(missing_ok=True)


def _obtain_official(raw: Path) -> dict:
    """Usar TLS do curl do sistema; sem desabilitar verificação de certificado.

    O .part pode ser retomado com Range. Só publicar depois de validar o ZIP.
    O hash calculado identifica o conteúdo; não há digest externo fornecido pelo Inep.
    """
    raw = raw.resolve()
    raw.mkdir(parents=True, exist_ok=True)
    archive = raw / "microdados_enem_2023.zip"
    partial = raw / "microdados_enem_2023.zip.part"
    if not archive.exists():
        if not partial.exists() or not zipfile.is_zipfile(partial):
            subprocess.run(
                [
                    "curl.exe" if shutil.which("curl.exe") else "curl",
                    "--fail",
                    "--location",
                    "--proto",
                    "=https",
                    "--proto-redir",
                    "=https",
                    "--connect-timeout",
                    "20",
                    "--max-time",
                    "900",
                    "--retry",
                    "3",
                    "--retry-all-errors",
                    "--retry-delay",
                    "3",
                    "--silent",
                    "--show-error",
                    "--continue-at",
                    "-",
                    "--max-filesize",
                    str(2 * 1024**3),
                    "--output",
                    str(partial),
                    OFFICIAL_ARCHIVE,
                ],
                check=True,
            )
        if not zipfile.is_zipfile(partial):
            raise ValueError("Download concluído sem um ZIP válido.")
        with zipfile.ZipFile(partial) as package:
            bad_member = package.testzip()
            if bad_member is not None:
                raise ValueError(f"CRC inválido no ZIP: {bad_member}")
        partial.rename(archive)
    extracted = []
    with zipfile.ZipFile(archive) as package:
        members = [
            info
            for info in package.infolist()
            if not info.is_dir()
            and (
                Path(info.filename).name.upper() == "MICRODADOS_ENEM_2023.CSV"
                or "DICION" in info.filename.upper()
                or "LEIA" in info.filename.upper()
            )
        ]
        if sum(Path(m.filename).name.upper() == "MICRODADOS_ENEM_2023.CSV" for m in members) != 1:
            raise ValueError("O pacote deve conter exatamente um CSV nacional de 2023.")
        for info in members:
            destination = raw / Path(info.filename).name
            if info.file_size > 8 * 1024**3:
                raise ValueError("Membro do ZIP excede o limite de oito GiB.")
            if not destination.exists():
                staged = destination.with_name(destination.name + ".part")
                created = False
                try:
                    with staged.open("xb") as target:
                        created = True
                        with package.open(info) as incoming:
                            shutil.copyfileobj(incoming, target, length=1024 * 1024)
                    staged.rename(destination)
                except Exception:
                    if created:
                        staged.unlink(missing_ok=True)
                    raise
            if destination.stat().st_size != info.file_size:
                raise ValueError("Arquivo extraído existente tem tamanho incompatível com o ZIP.")
            extracted.append(
                {
                    "member": info.filename,
                    "file": destination.name,
                    "bytes": info.file_size,
                    "sha256": sha256_file(destination),
                }
            )
    manifest = {
        "obtained_at_utc": datetime.now(UTC).isoformat(),
        "source_page": OFFICIAL_PAGE,
        "url": OFFICIAL_ARCHIVE,
        "archive": archive.name,
        "bytes": archive.stat().st_size,
        "sha256": sha256_file(archive),
        "checksum_compared_to_publisher": False,
        "extracted": extracted,
        "method": "HTTPS com verificação TLS; extração seletiva com verificação CRC do ZIP",
    }
    manifest_path = raw / "enem2023.source.json"
    if manifest_path.exists():
        raise FileExistsError("Manifesto oficial já existe; preservar a execução anterior.")
    write_json(manifest_path, manifest)
    return manifest
