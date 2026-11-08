"""Reajuste no desenvolvimento e avaliação única, retomável, dos modelos congelados."""

import gc
import json
import logging
import os
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits

from enem_base.checkpointing import atomic_json, digest, identifiers_digest, run_lock
from enem_base.evidence import GROUP_FIELDS, PROVENANCE_KEYS, group_errors, read_run, seal_run
from enem_base.final_selection import load_frozen, recipe_estimator
from enem_base.frozen_curves import validate_curves
from enem_base.learning_curves import _predict
from enem_base.modeling import estimator_spec, regression_metrics
from enem_base.provenance import runtime_metadata, sha256_file, verify_sha256
from enem_base.search_cache import load_array, load_pickle, read_json, save_array, save_pickle
from enem_base.study import load_development
from enem_base.workflow import _load_final_test

logger = logging.getLogger(__name__)


def final_protocol(config, root):
    frozen = load_frozen(config, root)
    _, curves = validate_curves(config, root)
    protocol = {
        **{k: frozen[k] for k in (*PROVENANCE_KEYS, "n_development")},
        "frozen_sha256": sha256_file(root / "congelamento" / "receitas.json"),
        "curve_inputs": curves,
        "code_sha256": sha256_file(Path(__file__)),
        "models": list(frozen["recipes"]),
        "primary_models": frozen["primary_models"],
        "academic_solution": frozen["academic_solution"],
        "prediction_batch_size": 100_000,
        "test_criterion": frozen["test_criterion"],
        "no_post_test_tuning": True,
    }
    directory = root / "avaliacao_final"
    with run_lock(directory / "protocolo.json"):
        path = directory / "protocolo.json"
        if path.exists():
            if read_json(path) != protocol:
                raise ValueError("Protocolo final alterado após iniciar os ajustes.")
        else:
            if (config.splits / "avaliacao_final.json").exists():
                raise ValueError("Teste já aberto por outro protocolo.")
            atomic_json(path, protocol)
    return frozen, protocol


def fit_final_models(config, root, labels=None):
    frozen, protocol = final_protocol(config, root)
    directory = root / "avaliacao_final"
    requested = protocol["models"] if labels is None else labels
    if set(requested) - set(protocol["models"]):
        raise ValueError("Ajuste fora da lista congelada.")
    frame, provenance = load_development(config)
    pa.default_memory_pool().release_unused()
    y = frame[config.target].to_numpy(dtype=float)
    context_base = {
        "protocol_sha256": sha256_file(directory / "protocolo.json"),
        "n_train": len(y),
        "train_ids_sha256": identifiers_digest(frame[config.identifier]),
    }
    with threadpool_limits(2):
        for label in requested:
            path = directory / "modelos_ajustados" / f"{label}.pkl"
            recipe = frozen["recipes"][label]
            estimator = recipe_estimator(config, recipe)
            context = {**context_base, "model": label, "parameters": estimator_spec(estimator)}
            with run_lock(path):
                if path.with_suffix(".json").exists():
                    fitted, _ = load_pickle(path, context)
                    del fitted
                    logger.info("Ajuste final %s verificado e reutilizado", label)
                    continue
                if (config.splits / "avaliacao_final.json").exists():
                    raise ValueError("Teste já aberto: não ajustar novos pesos.")
                logger.info("Ajuste final %s: %d registros de desenvolvimento", label, len(y))
                began = time.perf_counter()
                with warnings.catch_warnings(record=True) as notices:
                    warnings.simplefilter("always")
                    features = (
                        np.zeros((len(y), 1)) if label == "baseline" else frame[config.features]
                    )
                    estimator.fit(features, y)
                if any(issubclass(w.category, ConvergenceWarning) for w in notices):
                    raise ValueError("Ajuste final sem convergência; teste permanece fechado.")
                save_pickle(
                    path,
                    estimator,
                    context,
                    fit_seconds=time.perf_counter() - began,
                    warnings=[f"{w.category.__name__}: {w.message}" for w in notices],
                    development_target_mean=float(y.mean()),
                    **{k: provenance[k] for k in PROVENANCE_KEYS},
                )
                del estimator, features
                gc.collect()
    return validate_fits(config, root, require_all=False)


def validate_fits(config, root, require_all=True):
    frozen, protocol = final_protocol(config, root)
    directory = root / "avaliacao_final"
    split = pd.read_parquet(config.splits / "particoes.parquet")
    train_ids = identifiers_digest(split.loc[split.partition.eq("development"), config.identifier])
    models = {}
    for label in protocol["models"]:
        path = directory / "modelos_ajustados" / f"{label}.pkl"
        if not path.with_suffix(".json").exists() and not require_all:
            continue
        meta = read_json(path.with_suffix(".json"))
        expected = {
            "protocol_sha256": sha256_file(directory / "protocolo.json"),
            "n_train": protocol["n_development"],
            "train_ids_sha256": train_ids,
            "model": label,
            "parameters": frozen["recipes"][label]["estimator"],
        }
        if meta["context"] != expected or meta["warnings"]:
            raise ValueError("Ajuste final incompatível ou com avisos; investigar antes do teste.")
        verify_sha256(path, meta["sha256"], "Pesos finais alterados")
        models[label] = {
            "path": str(path),
            "sha256": meta["sha256"],
            "metadata_sha256": sha256_file(path.with_suffix(".json")),
        }
    if require_all and len(models) != len(protocol["models"]):
        raise ValueError("Ajustes finais incompletos.")
    return models


def evaluate_frozen(config, root):
    frozen, protocol = final_protocol(config, root)
    models = validate_fits(config, root)
    directory = root / "avaliacao_final"
    lock = config.splits / "avaliacao_final.json"
    identity = {
        "output": str(directory.resolve()),
        "protocol_sha256": sha256_file(directory / "protocolo.json"),
        "frozen_sha256": protocol["frozen_sha256"],
        "models": models,
    }
    with run_lock(lock):
        if lock.exists():
            state = read_json(lock)
            if state.get("identity") != identity:
                raise ValueError(
                    "Teste reservado a outra execução; não reabrir com novas escolhas."
                )
            if state["status"] == "completed":
                validate_final_results(config, root)
                return read_run(directory, frozen, development=False)
        else:
            # A trava persistente é criada apenas depois de validar todos os pesos e curvas.
            with lock.open("x", encoding="utf-8") as stream:
                json.dump({"status": "started", "identity": identity, **runtime_metadata()}, stream)
                stream.flush()
                os.fsync(stream.fileno())
        manifest = {
            **runtime_metadata(),
            **{k: protocol[k] for k in PROVENANCE_KEYS},
            "status": "running",
            "experiment_kind": "final_frozen_test",
            "test_evaluated": True,
            "evaluated_set": "test",
            "identity": identity,
            "primary_models": protocol["primary_models"],
            "academic_solution": protocol["academic_solution"],
        }
        atomic_json(directory / "manifesto.json", manifest)
        try:
            test = _load_final_test(config)
            pa.default_memory_pool().release_unused()
            split = pd.read_parquet(config.splits / "particoes.parquet")
            expected_ids = split.loc[split.partition.eq("test"), config.identifier].reset_index(
                drop=True
            )
            if not test[config.identifier].reset_index(drop=True).equals(expected_ids):
                raise ValueError("Teste não corresponde exatamente aos IDs reservados.")
            ids_hash = identifiers_digest(test[config.identifier])
            predicted = test[[config.identifier, config.target, *GROUP_FIELDS]].rename(
                columns={config.identifier: "registro_id", config.target: "nota_observada"}
            )
            records, groups, assets = [], [], {}
            with threadpool_limits(2):
                for label, entry in models.items():
                    path = Path(entry["path"])
                    meta = read_json(path.with_suffix(".json"))
                    context = {
                        "identity_sha256": digest(identity),
                        "model": label,
                        "model_sha256": entry["sha256"],
                        "test_ids_sha256": ids_hash,
                        "n_test": len(test),
                    }
                    cache = directory / "predicoes_parciais" / f"{label}.npy"
                    if cache.with_suffix(".json").exists():
                        values = load_array(cache, context)
                        elapsed = read_json(cache.with_suffix(".json"))["prediction_seconds"]
                    else:
                        fitted, _ = load_pickle(path, meta["context"])
                        began = time.perf_counter()
                        values = (
                            fitted.predict(np.zeros((len(test), 1)))
                            if label == "baseline"
                            else _predict(fitted, test[config.features], 100_000)
                        )
                        elapsed = time.perf_counter() - began
                        if values.shape != (len(test),) or not np.isfinite(values).all():
                            raise ValueError("Previsões finais incompletas ou não finitas.")
                        save_array(cache, values, context, prediction_seconds=elapsed)
                        del fitted
                        gc.collect()
                    predicted[f"previsao_{label}"] = values
                    recipe = frozen["recipes"][label]
                    record = {
                        "experiment_id": f"{root.name}-test-{label}",
                        "row_type": "test_final",
                        "fold": None,
                        "model": label,
                        "variant": recipe["variant"],
                        **{k: protocol[k] for k in PROVENANCE_KEYS},
                        "evaluated_set": "test",
                        "features_json": json.dumps(
                            recipe["features"] if label != "baseline" else []
                        ),
                        "parameters_json": json.dumps(recipe["estimator"], sort_keys=True),
                        "n_train": protocol["n_development"],
                        "n_evaluated": len(test),
                        "test_ids_sha256": ids_hash,
                        "fit_seconds": meta["fit_seconds"],
                        "prediction_seconds": elapsed,
                        "elapsed_seconds": meta["fit_seconds"] + elapsed,
                        "test_evaluated": True,
                        **regression_metrics(test[config.target], values),
                    }
                    records.append(record)
                    groups.extend(group_errors(test, values, config.target, label))
                    assets[str(cache.relative_to(directory))] = sha256_file(cache)
                    assets[str(cache.with_suffix(".json").relative_to(directory))] = sha256_file(
                        cache.with_suffix(".json")
                    )
                    atomic_json(
                        directory / "progresso.json", {"status": "running", "metrics": records}
                    )
                    logger.info(
                        "Teste %s: RMSE %.6f MAE %.6f R² %.6f",
                        label,
                        record["rmse"],
                        record["mae"],
                        record["r2"],
                    )
            predicted.to_csv(directory / "previsoes_teste.csv", index=False)
            table = pd.DataFrame(records).sort_values(
                ["rmse", "mae", "r2", "model"], ascending=[True, True, False, True]
            )
            table.to_csv(directory / "metricas.csv", index=False)
            table.to_csv(directory / "experimentos.csv", index=False)
            pd.DataFrame(groups).to_csv(directory / "erros_grupos.csv", index=False)
            atomic_json(directory / "progresso.json", {"status": "completed", "metrics": records})
            manifest.update(
                status="completed",
                n_test=len(test),
                prediction_assets=assets,
                primary_observed_winner=table.loc[
                    table.model.isin(protocol["primary_models"])
                ].iloc[0]["model"],
                all_models_observed_winner=table.iloc[0]["model"],
                zero_observed_scores=int(test[config.target].eq(0).sum()),
                metrics=records,
            )
            seal_run(directory, manifest)
            validate_final_results(config, root)
            atomic_json(lock, {"status": "completed", "identity": identity})
            return manifest
        except Exception as error:
            manifest.update(status="failed", failure_type=type(error).__name__, message=str(error))
            atomic_json(directory / "manifesto.json", manifest)
            atomic_json(
                lock, {"status": "interrupted", "identity": identity, "message": str(error)}
            )
            raise


def validate_final_results(config, root):
    frozen = load_frozen(config, root)
    directory = root / "avaliacao_final"
    manifest = read_run(directory, frozen, development=False)
    fitted = validate_fits(config, root)
    guard = read_json(config.splits / "avaliacao_final.json")
    if (
        manifest["identity"]["models"] != fitted
        or manifest["identity"] != guard.get("identity")
        or manifest["identity"]["protocol_sha256"] != sha256_file(directory / "protocolo.json")
    ):
        raise ValueError("Pesos ou identidade do teste diferem da execução congelada.")
    if manifest["test_evaluated"] is not True or manifest["evaluated_set"] != "test":
        raise ValueError("Avaliação final não identificada como teste.")
    for path, expected in manifest["prediction_assets"].items():
        verify_sha256(directory / path, expected, "Predições finais alteradas")
    predicted = pd.read_csv(
        directory / "previsoes_teste.csv",
        dtype={"registro_id": "string", **{g: "string" for g in GROUP_FIELDS}},
    )
    split = pd.read_parquet(config.splits / "particoes.parquet")
    ids = (
        split.loc[split.partition.eq("test"), config.identifier]
        .astype("string")
        .reset_index(drop=True)
    )
    if not predicted.registro_id.equals(ids) or predicted.registro_id.duplicated().any():
        raise ValueError("Cobertura dos IDs de teste incorreta.")
    metrics = pd.read_csv(directory / "metricas.csv")
    groups = pd.read_csv(directory / "erros_grupos.csv", dtype={"category": "string"})
    if set(metrics.model) != set(frozen["recipes"]) or len(metrics) != len(frozen["recipes"]):
        raise ValueError("Modelos finais incompletos.")
    checks = []
    for row in metrics.itertuples():
        if (
            row.n_train != frozen["n_development"]
            or row.n_evaluated != len(ids)
            or row.test_ids_sha256 != identifiers_digest(ids)
        ):
            raise ValueError("Contagens ou IDs inconsistentes nas métricas finais.")
        values = predicted[f"previsao_{row.model}"].to_numpy()
        computed = regression_metrics(predicted.nota_observada, values)
        for key, value in computed.items():
            np.testing.assert_allclose(value, getattr(row, key), rtol=0, atol=1e-9)
        actual_groups = groups.loc[groups.model.eq(row.model)]
        recomputed = pd.DataFrame(group_errors(predicted, values, "nota_observada", row.model))
        if set(actual_groups.group) != {"faixa_nota", *GROUP_FIELDS}:
            raise ValueError("Grupos de análise incompletos.")
        for field in ("n", "rmse", "mae", "r2", "mean_residual"):
            left = actual_groups.set_index(["group", "category"])[field].sort_index()
            right = recomputed.set_index(["group", "category"])[field].sort_index()
            if not left.index.equals(right.index):
                raise ValueError("Categorias de análise inconsistentes.")
            np.testing.assert_allclose(left, right, rtol=0, atol=1e-8, equal_nan=True)
        for _, subgroup in actual_groups.groupby("group"):
            if subgroup.n.sum() != len(ids):
                raise ValueError("Cobertura dos grupos incorreta.")
        checks.append({"model": row.model, **computed})
    atomic_json(
        root / "validacao_teste.json",
        {
            "status": "passed",
            "n_test": len(ids),
            "models": len(metrics),
            "metrics_recomputed": checks,
            "test_ids_sha256": identifiers_digest(ids),
            "all_group_counts_cover_test": True,
            "all_group_metrics_recomputed": True,
            "final_manifest_sha256": sha256_file(directory / "manifesto.json"),
            "test_evaluated": True,
        },
    )
    return metrics
