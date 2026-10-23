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


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
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
