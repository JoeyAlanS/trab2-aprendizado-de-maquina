"""Identidade de arquivos, serialização e metadados de execução."""

import hashlib
import importlib.metadata
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_sha256(path: Path, expected: str, message: str) -> None:
    """Exigir o hash registrado; a verificação continua estrita, byte a byte.

    Em falha, distinguir uma simples conversão de fim de linha (CRLF/LF, comum ao
    alternar Windows e Linux via Git) de uma alteração real de conteúdo, para orientar
    a recuperação sem aceitar silenciosamente nenhuma das duas.
    """
    if sha256_file(path) == expected:
        return
    data = path.read_bytes()
    lf = data.replace(b"\r\n", b"\n")
    variants = {hashlib.sha256(v).hexdigest() for v in (lf, lf.replace(b"\n", b"\r\n"))}
    if expected in variants:
        raise ValueError(
            f"{message}: {path.name} difere do manifesto apenas no fim de linha (CRLF/LF). "
            "O conteúdo é o mesmo; restaure a cópia versionada com "
            f"'git add --renormalize . && git checkout -- \"{path}\"' "
            "ou gere o artefato novamente."
        )
    raise ValueError(f"{message}: {path.name}")


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def runtime_metadata() -> dict:
    code_root = Path(__file__).resolve().parents[2]
    try:
        commit = subprocess.run(
            ["git", "-C", str(code_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    try:
        dirty = bool(
            subprocess.run(
                ["git", "-C", str(code_root), "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )
    except (OSError, subprocess.CalledProcessError):
        dirty = None
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "git_commit": commit,
        "git_dirty": dirty,
        "dependencies": {
            name: importlib.metadata.version(name)
            for name in ("enem-base", "pandas", "pyarrow", "scikit-learn", "matplotlib")
        },
    }
