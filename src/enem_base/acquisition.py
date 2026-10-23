"""Coleta explícita para raw, com escrita temporária e checksum.

Não extrai ZIPs nem baixa a base automaticamente durante demonstrações.
"""

import shutil
import tempfile
from contextlib import closing
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from enem_base.provenance import sha256_file, write_json


def collect(
    source: str, destination: Path, expected_sha256: str | None = None, max_bytes: int = 8 * 1024**3
) -> dict:
    destination = destination.resolve()
    manifest_path = destination.with_name(destination.name + ".source.json")
    if destination.exists() or manifest_path.exists():
        raise FileExistsError("Destino ou manifesto já existe; escolha um novo nome.")
    if max_bytes < 1:
        raise ValueError("max_bytes deve ser positivo.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    is_url = source.lower().startswith(("https:", "http:"))
    if is_url and urlparse(source).scheme != "https":
        raise ValueError("Downloads exigem HTTPS.")
    with tempfile.TemporaryDirectory(prefix=".coleta-", dir=destination.parent) as temp:
        partial = Path(temp) / "download.part"
        if is_url:
            stream = closing(urlopen(source, timeout=60))
        else:
            stream = Path(source).open("rb")
        total = 0
        with stream as response, partial.open("wb") as target:
            if is_url and urlparse(response.geturl()).scheme != "https":
                raise ValueError("Redirecionamento para protocolo diferente de HTTPS.")
            while block := response.read(1024 * 1024):
                total += len(block)
                if total > max_bytes:
                    raise ValueError("Fonte ultrapassa o limite de bytes configurado.")
                target.write(block)
        digest = sha256_file(partial)
        if expected_sha256 is not None and digest.lower() != expected_sha256.lower():
            raise ValueError("SHA-256 não confere; arquivo não foi publicado em raw.")
        manifest = {
            "source": source if is_url else Path(source).name,
            "file": destination.name,
            "bytes": total,
            "sha256": digest,
            "checksum_compared": expected_sha256 is not None,
        }
        # Exclusividade também no momento da publicação.
        with destination.open("xb") as target, partial.open("rb") as incoming:
            shutil.copyfileobj(incoming, target)
        write_json(manifest_path, manifest)
    return manifest
