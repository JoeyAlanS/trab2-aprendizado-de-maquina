"""Curvas dos três selecionados, com subconjuntos comuns e retomada verificável.

Cada ponto ajusta novamente todo o pipeline. O teste reservado não é carregado.
Os pickles locais são produzidos por este módulo e conferidos antes de abrir.
"""

import gc
import json
import logging
import os
import pickle
import time
import warnings
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from sklearn.base import clone
from threadpoolctl import threadpool_limits

from enem_base.checkpointing import atomic_json, digest, identifiers_digest, run_lock
from enem_base.evidence import PROVENANCE_KEYS, read_run, seal_run
from enem_base.modeling import estimator_spec, model_catalog, regression_metrics
from enem_base.provenance import runtime_metadata, sha256_file, verify_sha256
from enem_base.selection import load_selection
from enem_base.study import load_development
from enem_base.workflow import FRACTIONS

logger = logging.getLogger(__name__)
NUMERIC_SOURCES = (
    "checkpointing",
    "evidence",
    "learning_curves",
    "modeling",
    "preprocessing",
    "provenance",
    "selection",
    "splits",
    "study",
    "workflow",
)


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _dependencies():
    return {
        name: version(name)
        for name in (
            "numpy",
            "pandas",
            "pyarrow",
            "scikit-learn",
            "scipy",
            "threadpoolctl",
        )
    }


def _code_hashes():
    root = Path(__file__).parent
    return {name: sha256_file(root / f"{name}.py") for name in NUMERIC_SOURCES}


def selected_checkpoint(config, selection_path):
    selection = load_selection(config, selection_path)
    marker = _json(selection_path / "checkpoint.json")
    if (
        marker.get("checkpoint") != 2
        or marker.get("status") != "completed"
        or marker.get("test_evaluated") is not False
        or marker.get("selected_models") != selection["selected_models"]
    ):
        raise ValueError("O Checkpoint 2 deve estar concluído e validado.")
    for file, key in (
        ("manifesto.json", "manifest_sha256"),
        ("selecionados.json", "selection_sha256"),
        ("validacao.json", "validation_sha256"),
    ):
        verify_sha256(selection_path / file, marker[key], "Checkpoint 2 alterado")
    if _json(selection_path / "validacao.json").get("status") != "passed":
        raise ValueError("A validação do Checkpoint 2 não foi aprovada.")
    verify_sha256(Path(marker["report"]), marker["report_sha256"], "Relatório alterado")
    return selection


def subsets(frame, identifier):
    """Prefixos aleatórios cumulativos; ordem de ajuste igual à da fonte.

    Ordenar os índices não muda a seleção. Em 100%, reproduz a ordem do CP1.
    """
    labels = frame.validation_fold.to_numpy(dtype=int)
    for fold in range(3):
        eligible = np.flatnonzero(labels != fold)
        validation = np.flatnonzero(labels == fold)
        shuffled = np.random.RandomState(42).permutation(eligible)
        previous = np.array([], dtype=int)
        val_hash = identifiers_digest(frame.iloc[validation][identifier])
        for fraction in FRACTIONS:
            train = np.sort(shuffled[: int(len(eligible) * fraction)])
            if not np.array_equal(train[np.searchsorted(train, previous)], previous):
                raise ValueError("Subconjuntos não cumulativos.")
            if np.any(labels[train] == fold) or (
                fraction == 1.0 and not np.array_equal(train, eligible)
            ):
                raise ValueError("Treino/validação incompatíveis com as partições.")
            point = {
                "key": f"dobra-{fold}-fracao-{int(fraction * 100):03d}",
                "fold": fold,
                "fraction": fraction,
                "n_train": len(train),
                "n_validation": len(validation),
                "train_ids_sha256": identifiers_digest(frame.iloc[train][identifier]),
                "validation_ids_sha256": val_hash,
            }
            yield point, train, validation
            previous = train


def prepare_curves(config, selection_path, output, forest_jobs=2):
    """Congelar o plano antes do primeiro ajuste; nunca substituir plano existente."""
    if forest_jobs < 1:
        raise ValueError("O número de trabalhadores deve ser positivo.")
    with run_lock(output):
        selection = selected_checkpoint(config, selection_path)
        frame, provenance = load_development(config)
        plan = [point for point, _, _ in subsets(frame, config.identifier)]
        catalog = model_catalog(config)
        actual = {name: clone(catalog[name]) for name in selection["selected_models"]}
        actual["random_forest"].set_params(regressor__n_jobs=forest_jobs)
        protocol = {
            **provenance,
            "checkpoint": 3,
            "evaluated_set": "development_cv",
            "selected_models": selection["selected_models"],
            "selection_path": str(selection_path),
            "selection_sha256": sha256_file(selection_path / "selecionados.json"),
            "previous_checkpoint_sha256": sha256_file(selection_path / "checkpoint.json"),
            "features": config.features,
            "variant": "original",
            "seed": 42,
            "fractions": list(FRACTIONS),
            "n_splits": 3,
            "std_ddof": 0,
            "subset_method": "RandomState(42) prefix per fold, sorted into source order",
            "reference_parameters": selection["parameters"],
            "actual_parameters": {name: estimator_spec(est) for name, est in actual.items()},
            "execution_overrides": {"random_forest": {"regressor__n_jobs": forest_jobs}},
            "blas_threads": 2,
            "prediction_batch_size": 100_000,
            "hyperparameter_search_completed": False,
            "numeric_code_sha256": _code_hashes(),
            "dependencies": _dependencies(),
            "points": plan,
        }
        path = output / "protocolo.json"
        if path.exists():
            if _json(path) != protocol:
                raise ValueError("Plano existente difere da execução solicitada.")
            logger.info("Protocolo existente verificado; preservado")
        else:
            atomic_json(path, protocol)
            atomic_json(
                output / "inicio.json",
                {
                    **runtime_metadata(),
                    "status": "prepared",
                    "checkpoint": 3,
                    "protocol_sha256": sha256_file(path),
                    "expected_points": 45,
                    "next_checkpoint_started": False,
                    "test_evaluated": False,
                },
            )
        return protocol


def validate_protocol(config, selection_path, output):
    protocol = _json(output / "protocolo.json")
    selection = selected_checkpoint(config, selection_path)
    verify_sha256(
        selection_path / "selecionados.json", protocol["selection_sha256"], "Seleção alterada"
    )
    verify_sha256(
        selection_path / "checkpoint.json",
        protocol["previous_checkpoint_sha256"],
        "Checkpoint anterior alterado",
    )
    verify_sha256(
        output / "protocolo.json",
        _json(output / "inicio.json")["protocol_sha256"],
        "Protocolo alterado",
    )
    if (
        protocol["numeric_code_sha256"] != _code_hashes()
        or protocol["dependencies"] != _dependencies()
        or protocol["selected_models"] != selection["selected_models"]
        or protocol["reference_parameters"] != selection["parameters"]
        or protocol["features"] != config.features
        or protocol["fractions"] != list(FRACTIONS)
        or any(protocol[k] != selection[k] for k in PROVENANCE_KEYS)
    ):
        raise ValueError("Código, ambiente ou configuração mudaram após o plano.")
    return protocol


def _point_context(output, name, point, protocol):
    return {
        "protocol_sha256": sha256_file(output / "protocolo.json"),
        "model": name,
        "point": point,
        "parameters": protocol["actual_parameters"][name],
    }


def read_point(path, context):
    saved = _json(path)
    payload = {key: saved[key] for key in ("context", "record", "fit")}
    if (
        saved.get("status") != "completed"
        or saved["context"] != context
        or saved["sha256"] != digest(payload)
    ):
        raise ValueError(f"Ponto persistido incompatível ou alterado: {path}")
    return saved


def _predict(estimator, features, batch_size):
    result = np.empty(len(features), dtype=float)
    for start in range(0, len(features), batch_size):
        stop = min(start + batch_size, len(features))
        values = np.asarray(estimator.predict(features.iloc[start:stop]), dtype=float)
        if values.shape != (stop - start,) or not np.isfinite(values).all():
            raise ValueError("Previsões inválidas; não publicar o ponto.")
        result[start:stop] = values
    return result


def _save_fit(path, estimator, context, seconds, captured):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".pkl.tmp")
    with temporary.open("wb") as stream:
        pickle.dump(estimator, stream, protocol=5)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    metadata = {
        "context": context,
        "sha256": sha256_file(path),
        "fit_seconds": seconds,
        "warnings": captured,
    }
    atomic_json(path.with_suffix(".json"), metadata)
    return metadata


def curve_model(config, selection_path, output, name, resume=False):
    protocol = validate_protocol(config, selection_path, output)
    if name not in protocol["selected_models"]:
        raise ValueError("Modelo fora do trio selecionado.")
    directory = output / name
    with run_lock(directory):
        if directory.exists() and not resume:
            raise FileExistsError("Execução existente; use --resume para conferir e retomar.")
        directory.mkdir(parents=True, exist_ok=True)
        frame, provenance = load_development(config)
        if any(provenance[k] != protocol[k] for k in PROVENANCE_KEYS):
            raise ValueError("Origem mudou após registrar o plano.")
        pa.default_memory_pool().release_unused()
        estimator = clone(model_catalog(config)[name])
        estimator.set_params(**protocol["execution_overrides"].get(name, {}))
        if estimator_spec(estimator) != protocol["actual_parameters"][name]:
            raise ValueError("Parâmetros de execução diferem do protocolo.")
        manifest_path = directory / "manifesto.json"
        completed = manifest_path.exists() and _json(manifest_path).get("status") == "completed"
        if completed:
            read_run(directory, provenance)
        manifest = {
            **runtime_metadata(),
            **provenance,
            "status": "running",
            "experiment_kind": "selected_learning_curves",
            "evaluated_set": "development_cv",
            "model": name,
            "protocol_sha256": sha256_file(output / "protocolo.json"),
            "actual_parameters": estimator_spec(estimator),
            "completed_points": 0,
        }
        if not completed:
            atomic_json(manifest_path, manifest)
        x, y = frame[config.features], frame[config.target].to_numpy(dtype=float)
        records, point_assets, fit_assets = [], {}, {}
        try:
            with threadpool_limits(limits=protocol["blas_threads"]):
                for i, (point, train, validation) in enumerate(subsets(frame, config.identifier)):
                    if point != protocol["points"][i]:
                        raise ValueError("IDs ou contagens do subconjunto diferem do plano.")
                    context = _point_context(output, name, point, protocol)
                    point_path = directory / "pontos" / f"{point['key']}.json"
                    fit_path = directory / "modelos_ajustados" / f"{point['key']}.pkl"
                    if point_path.exists():
                        saved = read_point(point_path, context)
                        verify_sha256(fit_path, saved["fit"]["sha256"], "Modelo local alterado")
                        record = saved["record"]
                        logger.info("%s/%s: ponto verificado e reutilizado", name, point["key"])
                    elif completed:
                        raise ValueError("Manifesto concluído com ponto ausente.")
                    else:
                        logger.info("%s/%s: ajuste, n=%d", name, point["key"], len(train))
                        fitted = clone(estimator)
                        reused_fit = fit_path.with_suffix(".json").exists()
                        if reused_fit:
                            fit = _json(fit_path.with_suffix(".json"))
                            if fit["context"] != context:
                                raise ValueError("Modelo local incompatível.")
                            verify_sha256(fit_path, fit["sha256"], "Modelo local alterado")
                            with fit_path.open("rb") as stream:
                                fitted = pickle.load(stream)
                        else:
                            started = time.perf_counter()
                            with warnings.catch_warnings(record=True) as captured:
                                warnings.simplefilter("always")
                                fitted.fit(x.iloc[train], y[train])
                            seconds = time.perf_counter() - started
                            fit_warnings = [f"{w.category.__name__}: {w.message}" for w in captured]
                            fit = _save_fit(fit_path, fitted, context, seconds, fit_warnings)
                        logger.info(
                            "%s/%s: ajuste salvo; calculando treino e validação", name, point["key"]
                        )
                        started = time.perf_counter()
                        with warnings.catch_warnings(record=True) as captured:
                            warnings.simplefilter("always")
                            train_metrics = regression_metrics(
                                y[train],
                                _predict(fitted, x.iloc[train], protocol["prediction_batch_size"]),
                            )
                            metrics = regression_metrics(
                                y[validation],
                                _predict(
                                    fitted, x.iloc[validation], protocol["prediction_batch_size"]
                                ),
                            )
                        score_seconds = time.perf_counter() - started
                        warning_text = fit["warnings"] + [
                            f"{w.category.__name__}: {w.message}" for w in captured
                        ]
                        record = {
                            "model": name,
                            **point,
                            **metrics,
                            **{key + "_train": value for key, value in train_metrics.items()},
                            "gap_rmse": metrics["rmse"] - train_metrics["rmse"],
                            "fit_seconds": fit["fit_seconds"],
                            "score_seconds": score_seconds,
                            "elapsed_seconds": fit["fit_seconds"] + score_seconds,
                            "fit_reused": reused_fit,
                            "warning_count": len(warning_text),
                            "warnings_json": json.dumps(warning_text, ensure_ascii=False),
                            "test_evaluated": False,
                        }
                        payload = {"context": context, "record": record, "fit": fit}
                        atomic_json(
                            point_path,
                            {
                                "status": "completed",
                                "sha256": digest(payload),
                                **payload,
                            },
                        )
                        del fitted
                        gc.collect()
                        logger.info(
                            "%s/%s: RMSE treino=%.6f, validação=%.6f",
                            name,
                            point["key"],
                            record["rmse_train"],
                            record["rmse"],
                        )
                    records.append(record)
                    point_assets[str(point_path.relative_to(directory))] = sha256_file(point_path)
                    fit_assets[str(fit_path.relative_to(directory))] = sha256_file(fit_path)
                    if not completed:
                        manifest["completed_points"] = len(records)
                        atomic_json(manifest_path, manifest)
            table = pd.DataFrame(records)
            if len(table) != 15 or table.duplicated(["fold", "fraction"]).any():
                raise ValueError("Curva exige quinze pontos distintos.")
            if completed:
                old = pd.read_csv(directory / "curvas.csv")
                pd.testing.assert_frame_equal(table, old, check_dtype=False, rtol=1e-12, atol=1e-12)
                return _json(manifest_path)
            table.to_csv(directory / "curvas.csv", index=False)
            manifest.update(status="completed", point_assets=point_assets, fit_assets=fit_assets)
            seal_run(directory, manifest)
            return manifest
        except Exception as error:
            if not completed:
                manifest.update(
                    status="failed", failure_type=type(error).__name__, message=str(error)
                )
                atomic_json(manifest_path, manifest)
            raise
