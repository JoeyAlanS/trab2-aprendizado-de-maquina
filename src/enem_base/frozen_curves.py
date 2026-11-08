"""Curvas das receitas pós-busca, com reaproveitamento verificável de ajustes."""

import gc
import logging
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits

from enem_base.checkpointing import atomic_json, digest, run_lock
from enem_base.evidence import read_run, seal_run
from enem_base.final_selection import load_frozen, recipe_estimator
from enem_base.learning_curves import _predict, subsets
from enem_base.modeling import estimator_spec, model_catalog, regression_metrics
from enem_base.provenance import runtime_metadata, sha256_file, verify_sha256
from enem_base.search_cache import (
    data_digest,
    forest_prefix,
    load_pickle,
    oof_features,
    prior_curve_fit,
    read_json,
    save_pickle,
    stacking_meta_fit,
    target_digest,
)

logger = logging.getLogger(__name__)


def curve_binding(root):
    return {
        "frozen_sha256": sha256_file(root / "congelamento" / "receitas.json"),
        "code_sha256": sha256_file(Path(__file__)),
        "test_evaluated": False,
    }


def fitted_curve_point(config, root, label, recipe, estimator, point, x, y, context):
    """Retorna ajuste e origem; nunca reutiliza uma validação para aprender pesos."""
    p = read_json(root / "protocolo_buscas.json")
    name = recipe["model"]
    if point["fraction"] == 1 and recipe["candidate_id"] is not None:
        source = (
            Path(recipe["source"])
            / "modelos_ajustados"
            / (f"config-{recipe['candidate_id']:02d}-dobra-{point['fold']}.pkl")
        )
        meta = read_json(source.with_suffix(".json"))
        if meta["context"]["parameters"] != estimator_spec(estimator) or meta["context"][
            "train_target_sha256"
        ] != target_digest(y):
            raise ValueError("Ajuste integral da busca incompatível com a curva.")
        manifest = read_run(Path(recipe["source"]), p)
        verify_sha256(
            source,
            manifest["fit_assets"][str(source.relative_to(Path(recipe["source"])))],
            "Ajuste selecionado alterado",
        )
        fitted, _ = load_pickle(source, meta["context"])
        return fitted, "search_full_training_fold"
    if name in p["primary_models"] and recipe["variant"] == "original":
        base = clone(model_catalog(config)[name])
        if name == "random_forest":
            base.set_params(regressor__n_jobs=6)
        old = prior_curve_fit(
            p, name, point["fold"], point["fraction"], base, point["train_ids_sha256"]
        )
        if old is not None:
            if estimator_spec(base) == estimator_spec(estimator):
                return old, "checkpoint3_exact_parameters"
            if name == "random_forest":
                selected = estimator.get_params()
                compatible = clone(estimator).set_params(regressor__n_estimators=30)
                if estimator_spec(compatible) == estimator_spec(base):
                    return forest_prefix(
                        old, selected["regressor__n_estimators"]
                    ), "checkpoint3_tree_prefix"
            if name == "stacking":
                compatible = clone(estimator).set_params(final_estimator__alpha=1.0)
                if estimator_spec(compatible) == estimator_spec(base):
                    cache = root / "cache_buscas" / "curvas" / label / point["key"]
                    internal = {
                        **context,
                        "data_sha256": data_digest(x),
                        "target_sha256": target_digest(y),
                    }
                    oof = oof_features(base, x, y, cache, internal)
                    check = stacking_meta_fit(old, oof, y, 1.0)
                    np.testing.assert_allclose(
                        check.final_estimator_.coef_, old.final_estimator_.coef_, rtol=0, atol=1e-10
                    )
                    np.testing.assert_allclose(
                        check.final_estimator_.intercept_,
                        old.final_estimator_.intercept_,
                        rtol=0,
                        atol=1e-10,
                    )
                    alpha = estimator.get_params()["final_estimator__alpha"]
                    return stacking_meta_fit(old, oof, y, alpha), "checkpoint3_bases_new_oof_meta"
            del old
    return clone(estimator).fit(x, y), "new_fit"


def curve_model(config, root, label):
    from enem_base.study import load_development

    frozen = load_frozen(config, root)
    if label not in frozen["curve_models"]:
        raise ValueError("Modelo não pertence às curvas congeladas.")
    binding = curve_binding(root)
    directory = root / "curvas_finais" / label
    with run_lock(directory):
        if (directory / "manifesto.json").exists():
            previous = read_json(directory / "manifesto.json")
            if previous["binding"] != binding:
                raise ValueError("Código ou receita alterado após iniciar a curva.")
            if previous["status"] == "completed":
                validate_curves(config, root, labels=[label])
                return previous
        if (config.splits / "avaliacao_final.json").exists():
            raise ValueError("Teste já aberto: não recalcular curvas de seleção.")
        frame, provenance = load_development(config)
        pa.default_memory_pool().release_unused()
        recipe = frozen["recipes"][label]
        estimator = recipe_estimator(config, recipe)
        manifest = {
            **runtime_metadata(),
            **provenance,
            "status": "running",
            "experiment_kind": "frozen_learning_curves",
            "evaluated_set": "development_cv",
            "binding": binding,
            "model": label,
            "completed_points": 0,
        }
        atomic_json(directory / "manifesto.json", manifest)
        records, assets, models = [], {}, {}
        x, y = frame[config.features], frame[config.target].to_numpy(dtype=float)
        try:
            with threadpool_limits(2):
                for point, train, validation in subsets(frame, config.identifier):
                    context = {
                        **binding,
                        "label": label,
                        "point": point,
                        "parameters": estimator_spec(estimator),
                    }
                    path = directory / "pontos" / f"{point['key']}.json"
                    model_path = directory / "modelos_ajustados" / f"{point['key']}.pkl"
                    if path.exists():
                        saved = read_json(path)
                        payload = {k: saved[k] for k in ("context", "record", "fit")}
                        if saved["context"] != context or saved["sha256"] != digest(payload):
                            raise ValueError("Ponto da curva alterado.")
                        verify_sha256(
                            model_path, saved["fit"]["sha256"], "Ajuste da curva alterado"
                        )
                        record = saved["record"]
                    else:
                        logger.info("Curva final %s/%s", label, point["key"])
                        if model_path.with_suffix(".json").exists():
                            fitted, fit = load_pickle(model_path, context)
                        else:
                            began = time.perf_counter()
                            with warnings.catch_warnings(record=True) as notices:
                                warnings.simplefilter("always")
                                fitted, origin = fitted_curve_point(
                                    config,
                                    root,
                                    label,
                                    recipe,
                                    estimator,
                                    point,
                                    x.iloc[train],
                                    y[train],
                                    context,
                                )
                            if any(issubclass(w.category, ConvergenceWarning) for w in notices):
                                raise ValueError("Curva não convergiu.")
                            fit = save_pickle(
                                model_path,
                                fitted,
                                context,
                                origin=origin,
                                fit_seconds=time.perf_counter() - began,
                                warnings=[str(w.message) for w in notices],
                            )
                        if estimator_spec(fitted) != estimator_spec(estimator):
                            raise ValueError("Parâmetros do ajuste diferentes da receita.")
                        began = time.perf_counter()
                        training = regression_metrics(
                            y[train], _predict(fitted, x.iloc[train], 100_000)
                        )
                        validation_metrics = regression_metrics(
                            y[validation], _predict(fitted, x.iloc[validation], 100_000)
                        )
                        record = {
                            "model": label,
                            **point,
                            **validation_metrics,
                            **{m + "_train": v for m, v in training.items()},
                            "gap_rmse": validation_metrics["rmse"] - training["rmse"],
                            "fit_seconds": fit["fit_seconds"],
                            "origin": fit["origin"],
                            "score_seconds": time.perf_counter() - began,
                            "warning_count": len(fit["warnings"]),
                            "test_evaluated": False,
                        }
                        payload = {"context": context, "record": record, "fit": fit}
                        atomic_json(
                            path, {"status": "completed", "sha256": digest(payload), **payload}
                        )
                        del fitted
                        gc.collect()
                    records.append(record)
                    assets[str(path.relative_to(directory))] = sha256_file(path)
                    models[str(model_path.relative_to(directory))] = sha256_file(model_path)
                    models[str(model_path.with_suffix(".json").relative_to(directory))] = (
                        sha256_file(model_path.with_suffix(".json"))
                    )
                    manifest["completed_points"] = len(records)
                    atomic_json(directory / "manifesto.json", manifest)
                    logger.info("%s/%s: validação RMSE %.6f", label, point["key"], record["rmse"])
            table = pd.DataFrame(records)
            table.to_csv(directory / "curvas.csv", index=False)
            manifest.update(status="completed", point_assets=assets, fit_assets=models)
            seal_run(directory, manifest)
            validate_curves(config, root, labels=[label])
            return manifest
        except Exception as error:
            manifest.update(status="failed", failure_type=type(error).__name__, message=str(error))
            atomic_json(directory / "manifesto.json", manifest)
            raise


def validate_curves(config, root, labels=None):
    frozen = load_frozen(config, root)
    search = read_json(root / "protocolo_buscas.json")
    plan = read_json(Path(search["checkpoint3_path"]) / "protocolo.json")["points"]
    inputs, tables = {}, []
    for label in frozen["curve_models"] if labels is None else labels:
        directory = root / "curvas_finais" / label
        manifest = read_run(directory, frozen)
        if manifest["binding"] != curve_binding(root):
            raise ValueError("Curva não corresponde à receita/código atual.")
        for assets in ("point_assets", "fit_assets"):
            for path, expected in manifest[assets].items():
                verify_sha256(directory / path, expected, "Artefato da curva alterado")
        table = pd.read_csv(directory / "curvas.csv")
        saved_rows = []
        for point in plan:
            saved = read_json(directory / "pontos" / f"{point['key']}.json")
            payload = {k: saved[k] for k in ("context", "record", "fit")}
            context = {
                **curve_binding(root),
                "label": label,
                "point": point,
                "parameters": frozen["recipes"][label]["estimator"],
            }
            if (
                saved.get("status") != "completed"
                or saved["context"] != context
                or saved["fit"]["context"] != context
                or saved["sha256"] != digest(payload)
                or any(saved["record"][k] != v for k, v in point.items())
            ):
                raise ValueError("Ponto incompatível com o plano nacional da curva.")
            saved_rows.append(saved["record"])
        pd.testing.assert_frame_equal(
            table, pd.DataFrame(saved_rows), check_dtype=False, rtol=1e-12, atol=1e-12
        )
        if (
            len(table) != 15
            or set(zip(table.fold, table.fraction, strict=True))
            != {(f, p) for f in range(3) for p in frozen["learning_fractions"]}
            or not table.warning_count.eq(0).all()
        ):
            raise ValueError("Curva incompleta ou com avisos.")
        if (
            not np.isfinite(
                table[["rmse", "mae", "r2", "rmse_train", "mae_train", "r2_train", "gap_rmse"]]
            )
            .all()
            .all()
        ):
            raise ValueError("Métricas não finitas na curva.")
        np.testing.assert_allclose(
            table.gap_rmse, table.rmse - table.rmse_train, rtol=0, atol=1e-10
        )
        full = table.loc[table.fraction.eq(1)]
        for metric in ("rmse", "mae", "r2"):
            np.testing.assert_allclose(
                full[metric].mean(), frozen["recipes"][label][metric + "_mean"], rtol=0, atol=1e-8
            )
        inputs[str(directory / "manifesto.json")] = sha256_file(directory / "manifesto.json")
        tables.append(table)
    return pd.concat(tables, ignore_index=True), inputs
