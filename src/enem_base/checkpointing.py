"""Persistência atômica de resultados reais para retomar comparações interrompidas."""

import hashlib
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

from enem_base.provenance import sha256_file, verify_sha256


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


@contextmanager
def run_lock(output):
    """Trava do sistema operacional; liberada também se o processo for encerrado."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with (output.parent / f".run-{output.name}.lock").open("a+b") as stream:
        if os.name == "nt":
            import msvcrt

            if stream.tell() == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ValueError("A comparação já está em execução em outro processo.") from error
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)


def identifiers_digest(values):
    hashed = pd.util.hash_pandas_object(values.astype("string"), index=False)
    return hashlib.sha256(hashed.to_numpy().tobytes()).hexdigest()


def save_fold(path, context, record, groups):
    payload = {"context": context, "record": record, "groups": groups}
    atomic_json(path, {"status": "completed", "sha256": digest(payload), **payload})


def load_fold(path, context):
    saved = json.loads(path.read_text(encoding="utf-8"))
    payload = {k: saved[k] for k in ("context", "record", "groups")}
    if (
        saved.get("status") != "completed"
        or saved["context"] != context
        or saved["sha256"] != digest(payload)
    ):
        raise ValueError(f"Dobra persistida incompatível ou alterada: {path}")
    return saved["record"], saved["groups"]


def prediction_blocks(estimator, features, identifiers, directory, context, fit_seconds, size=2048):
    """Gravar somente previsões já calculadas; nunca criar linhas de preenchimento.

    O gerador pode ser interrompido após qualquer bloco. Na próxima chamada,
    verifica hashes, contexto e IDs antes de reutilizar esses resultados.
    """
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "manifesto.json"
    expected = {**context, "rows": len(features), "batch_size": size}
    if path.exists():
        state = json.loads(path.read_text(encoding="utf-8"))
        if state["context"] != expected:
            raise ValueError("Os blocos de previsão pertencem a outra configuração ou população.")
    else:
        state = {"context": expected, "blocks": {}, "fit_seconds": [], "status": "running"}
    prior_fit_seconds = sum(state["fit_seconds"])
    state["fit_seconds"].append(float(fit_seconds))
    state["status"] = "running"
    atomic_json(path, state)
    for start in range(0, len(features), size):
        stop = min(start + size, len(features))
        key = str(start)
        ids = identifiers.iloc[start:stop].astype("string").reset_index(drop=True)
        reused = key in state["blocks"]
        if reused:
            entry = state["blocks"][key]
            name = entry["file"]
            if Path(name).name != name:
                raise ValueError("Caminho inválido no checkpoint de previsões.")
            block = directory / name
            verify_sha256(block, entry["sha256"], "Bloco de previsões alterado")
            saved = pd.read_parquet(block)
            if len(saved) != stop - start or not saved.registro_id.astype("string").equals(ids):
                raise ValueError("IDs do bloco não correspondem à validação persistida.")
            values = saved.previsao.to_numpy(dtype=float)
        else:
            began = time.perf_counter()
            values = np.asarray(estimator.predict(features.iloc[start:stop]), dtype=float)
            elapsed = time.perf_counter() - began
            if values.shape != (len(ids),) or not np.isfinite(values).all():
                raise ValueError("Previsões inválidas; o bloco não será publicado.")
            block = directory / f"bloco-{start:07d}-{stop:07d}.parquet"
            # Um arquivo órfão pode existir se houve interrupção antes do manifesto.
            # Preservá-lo e só adotar seu conteúdo após recalcular e comparar o bloco.
            if block.exists():
                orphan = pd.read_parquet(block)
                if not orphan.registro_id.astype("string").equals(ids) or not np.array_equal(
                    orphan.previsao.to_numpy(), values
                ):
                    raise ValueError(
                        "Bloco órfão difere da recomputação; preservar para investigação."
                    )
            else:
                temporary = block.with_suffix(".parquet.tmp")
                pd.DataFrame({"registro_id": ids, "previsao": values}).to_parquet(
                    temporary, index=False
                )
                temporary.replace(block)
            entry = {
                "file": block.name,
                "sha256": sha256_file(block),
                "rows": len(ids),
                "prediction_seconds": elapsed,
            }
            state["blocks"][key] = entry
            atomic_json(path, state)
        if not np.isfinite(values).all():
            raise ValueError("Bloco persistido contém previsão não finita.")
        yield start, stop, values, reused, entry["prediction_seconds"], prior_fit_seconds
    state["status"] = "completed"
    atomic_json(path, state)
