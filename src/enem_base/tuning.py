"""Busca nacional nos dois escopos, com GridSearchCV real e retomada por ajuste."""

import gc
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from sklearn.base import clone
from sklearn.model_selection import GridSearchCV, ParameterGrid, PredefinedSplit
from threadpoolctl import threadpool_limits

from enem_base.checkpointing import atomic_json, identifiers_digest, run_lock
from enem_base.evidence import PROVENANCE_KEYS, read_run, seal_run
from enem_base.learning_curves import _code_hashes, _dependencies, validate_protocol
from enem_base.modeling import estimator_spec, model_catalog
from enem_base.provenance import runtime_metadata, sha256_file, verify_sha256
from enem_base.search_cache import CachedCVRegressor, data_digest, read_json, target_digest
from enem_base.study import load_development
from enem_base.workflow import initial_comparison

logger = logging.getLogger(__name__)
MODELS = ("svm", "linear", "ridge", "random_forest", "stacking")
ALPHAS = [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 1000.0]
SPACES = {
    "svm": {"regressor__C": [0.01, 0.1, 1.0, 10.0], "regressor__epsilon": [0.0, 0.1, 1.0]},
    "linear": {
        "regressor__fit_intercept": [True, False],
        "regressor__tol": [1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8],
    },
    "ridge": {"regressor__alpha": ALPHAS},
    "random_forest": {
        "regressor__max_depth": [8, 12],
        "regressor__n_estimators": [5, 10, 15, 20, 25, 30],
    },
    "stacking": {"final_estimator__alpha": ALPHAS},
}


def code_hashes():
    root = Path(__file__).parent
    return {
        **_code_hashes(),
        **{name: sha256_file(root / f"{name}.py") for name in ("search_cache", "tuning")},
    }


def search_estimator(config, name):
    result = clone(model_catalog(config)[name])
    if name == "random_forest":
        result.set_params(regressor__n_jobs=6)
    if name == "svm":
        result.set_params(regressor__max_iter=50_000)
    return result


def prepare_search(config, checkpoint2, checkpoint3, references, output):
    with run_lock(output):
        old_protocol = validate_protocol(config, checkpoint2, checkpoint3)
        marker = read_json(checkpoint3 / "checkpoint.json")
        if (
            marker.get("status") != "completed"
            or marker.get("validated_points") != 45
            or marker.get("test_evaluated") is not False
        ):
            raise ValueError("O Checkpoint 3 deve estar concluído.")
        publication = Path(marker["publication"])
        for path, key in (
            (publication / "manifesto.json", "publication_manifest_sha256"),
            (checkpoint3 / "validacao.json", "validation_sha256"),
            (Path(marker["report"]), "report_sha256"),
        ):
            verify_sha256(path, marker[key], "Checkpoint 3 alterado")
        published = read_run(publication, old_protocol)
        inputs = {
            str(checkpoint3 / "checkpoint.json"): sha256_file(checkpoint3 / "checkpoint.json")
        }
        for source, expected in published["inputs"].items():
            verify_sha256(Path(source), expected, "Fonte do CP3 alterada")
            inputs[source] = expected
        checkpoint1 = Path(read_json(checkpoint2 / "checkpoint.json")["previous_checkpoint"]).parent
        original_paths = [references] + [
            checkpoint1 / name
            for name in (
                "svm",
                "knn",
                "bagging",
                "pasting",
                "random_forest",
                "boosting",
                "stacking",
            )
        ]
        _, ranking = initial_comparison(config, original_paths, old_protocol)
        academic = ranking.index[:3].tolist()
        selected = old_protocol["selected_models"]
        if set(academic) | set(selected) != set(MODELS):
            raise ValueError("O catálogo mudou; reavaliar explicitamente o escopo das buscas.")
        inputs.update(
            {str(p / "manifesto.json"): sha256_file(p / "manifesto.json") for p in original_paths}
        )
        frame, provenance = load_development(config)
        x = frame[[config.identifier, *config.features]]
        y = frame[config.target].to_numpy(dtype=float)
        labels = frame.validation_fold.to_numpy(dtype=int)
        folds = []
        for fold in range(3):
            train, validation = np.flatnonzero(labels != fold), np.flatnonzero(labels == fold)
            folds.append(
                {
                    "fold": fold,
                    "n_train": len(train),
                    "n_validation": len(validation),
                    "train_data_sha256": data_digest(x.iloc[train]),
                    "validation_data_sha256": data_digest(x.iloc[validation]),
                    "train_target_sha256": target_digest(y[train]),
                    "validation_target_sha256": target_digest(y[validation]),
                    "train_ids_sha256": identifiers_digest(frame.iloc[train][config.identifier]),
                    "validation_ids_sha256": identifiers_digest(
                        frame.iloc[validation][config.identifier]
                    ),
                }
            )
        candidates = {
            name: [
                {
                    "parameters": params,
                    "estimator": estimator_spec(
                        search_estimator(config, name).set_params(**params)
                    ),
                }
                for params in ParameterGrid(SPACES[name])
            ]
            for name in MODELS
        }
        protocol = {
            **provenance,
            "checkpoint": 4,
            "stage": "hyperparameter_search",
            "primary_models": selected,
            "academic_top_three": academic,
            "search_models": list(MODELS),
            "identifier": config.identifier,
            "features": config.features,
            "spaces": SPACES,
            "candidates": candidates,
            "folds": folds,
            "selection_path": str(checkpoint2),
            "checkpoint3_path": str(checkpoint3),
            "reference_path": str(references),
            "original_paths": [str(p) for p in original_paths],
            "inputs": inputs,
            "criterion": [
                "rmse_mean ascending",
                "mae_mean ascending",
                "r2_mean descending",
                "candidate_id ascending",
            ],
            "retain_initial_if_improvement_at_most": 1e-8,
            "numeric_tolerance_is_significance_threshold": False,
            "initial_candidates_remain_eligible": True,
            "gridsearch": {
                "cv": "persisted three folds via PredefinedSplit",
                "n_jobs": 1,
                "refit": False,
                "return_train_score": False,
                "error_score": "raise",
            },
            "numerical_limits": {"svm_max_iter": 50_000, "blas_threads": 2, "forest_jobs": 6},
            "numeric_code_sha256": code_hashes(),
            "dependencies": _dependencies(),
            "cached_fit_equivalence_required": True,
            "expected_candidate_fold_evaluations": 180,
        }
        path = output / "protocolo_buscas.json"
        if path.exists():
            if read_json(path) != protocol:
                raise ValueError("Protocolo existente difere da preparação solicitada.")
        else:
            atomic_json(path, protocol)
            atomic_json(
                output / "inicio_buscas.json",
                {
                    **runtime_metadata(),
                    "status": "prepared",
                    "protocol_sha256": sha256_file(path),
                    "test_evaluated": False,
                },
            )
        return protocol


def validate_search_protocol(config, output):
    path = output / "protocolo_buscas.json"
    p = read_json(path)
    verify_sha256(
        path,
        read_json(output / "inicio_buscas.json")["protocol_sha256"],
        "Protocolo de busca alterado",
    )
    validate_protocol(config, Path(p["selection_path"]), Path(p["checkpoint3_path"]))
    if p["numeric_code_sha256"] != code_hashes() or p["dependencies"] != _dependencies():
        raise ValueError("Código ou ambiente alterado após registrar as buscas.")
    for source, expected in p["inputs"].items():
        verify_sha256(Path(source), expected, "Entrada das buscas alterada")
    return p


def search_model(config, output, name, resume=False):
    p = validate_search_protocol(config, output)
    preflight = read_json(output / "validacao_cache.json")
    if preflight.get("status") != "passed" or preflight.get("code_sha256") != code_hashes():
        raise ValueError("Conferir equivalência dos caches em dados reais antes das buscas.")
    directory = output / "buscas" / name
    with run_lock(directory):
        if directory.exists() and not resume:
            raise FileExistsError("Busca existente; usar --resume para verificar e retomar.")
        if (directory / "manifesto.json").exists():
            previous = read_json(directory / "manifesto.json")
            if previous.get("status") == "completed":
                return read_run(directory, p)
        directory.mkdir(parents=True, exist_ok=True)
        manifest = {
            **runtime_metadata(),
            **{k: p[k] for k in (*PROVENANCE_KEYS, "n_development")},
            "status": "running",
            "test_evaluated": False,
            "evaluated_set": "development_cv",
            "experiment_kind": "grid_search_cached",
            "model": name,
            "protocol_sha256": sha256_file(output / "protocolo_buscas.json"),
        }
        atomic_json(directory / "manifesto.json", manifest)
        frame, actual = load_development(config)
        if any(actual[k] != p[k] for k in PROVENANCE_KEYS):
            raise ValueError("Origem mudou antes da busca.")
        pa.default_memory_pool().release_unused()
        wrapper = CachedCVRegressor(
            search_estimator(config, name), name, str(output / "protocolo_buscas.json")
        )
        grid = {"estimator__" + key: value for key, value in p["spaces"][name].items()}
        search = GridSearchCV(
            wrapper,
            grid,
            cv=PredefinedSplit(frame.validation_fold.to_numpy(dtype=int)),
            scoring={
                "rmse": "neg_root_mean_squared_error",
                "mae": "neg_mean_absolute_error",
                "r2": "r2",
            },
            n_jobs=1,
            refit=False,
            return_train_score=False,
            error_score="raise",
            verbose=1,
        )
        try:
            started = time.perf_counter()
            with threadpool_limits(2):
                search.fit(
                    frame[[config.identifier, *config.features]],
                    frame[config.target].to_numpy(dtype=float),
                )
            elapsed = time.perf_counter() - started
            result = pd.DataFrame(search.cv_results_)
            if len(result) != 12 or not np.isfinite(result.mean_test_rmse).all():
                raise ValueError("Cada busca deve produzir doze configurações válidas.")
            records, folds, fit_assets = [], [], {}
            for index, row in result.iterrows():
                params = {
                    key.removeprefix("estimator__"): value for key, value in row.params.items()
                }
                if params != p["candidates"][name][index]["parameters"]:
                    raise ValueError("A ordem do GridSearchCV difere do protocolo.")
                record = {
                    "model": name,
                    "candidate_id": int(index),
                    "parameters_json": json.dumps(params, sort_keys=True),
                    "n_splits": 3,
                    "mean_fit_time": float(row.mean_fit_time),
                    "mean_score_time": float(row.mean_score_time),
                }
                for metric in ("rmse", "mae", "r2"):
                    sign = 1 if metric == "r2" else -1
                    record[metric + "_mean"] = sign * float(row["mean_test_" + metric])
                    record[metric + "_std"] = float(row["std_test_" + metric])
                records.append(record)
                for fold in range(3):
                    fit = directory / "modelos_ajustados" / f"config-{index:02d}-dobra-{fold}.pkl"
                    meta = read_json(fit.with_suffix(".json"))
                    verify_sha256(fit, meta["sha256"], "Ajuste de busca alterado")
                    fit_assets[str(fit.relative_to(directory))] = meta["sha256"]
                    fit_assets[str(fit.with_suffix(".json").relative_to(directory))] = sha256_file(
                        fit.with_suffix(".json")
                    )
                    folds.append(
                        {
                            "model": name,
                            "candidate_id": int(index),
                            "fold": fold,
                            "n_train": p["folds"][fold]["n_train"],
                            "n_validation": p["folds"][fold]["n_validation"],
                            "parameters_json": record["parameters_json"],
                            "warnings_json": json.dumps(meta["warnings"], ensure_ascii=False),
                            **{
                                m: (1 if m == "r2" else -1) * float(row[f"split{fold}_test_{m}"])
                                for m in ("rmse", "mae", "r2")
                            },
                        }
                    )
            result["params"] = result.params.map(lambda x: json.dumps(x, sort_keys=True))
            result.to_csv(directory / "gridsearch_cv_results.csv", index=False)
            table = pd.DataFrame(records).sort_values(
                ["rmse_mean", "mae_mean", "r2_mean", "candidate_id"],
                ascending=[True, True, False, True],
            )
            table.to_csv(directory / "comparacao_configuracoes.csv", index=False)
            pd.DataFrame(folds).to_csv(directory / "metricas_dobras.csv", index=False)
            best = table.iloc[0].to_dict()
            manifest.update(
                status="completed",
                configurations=len(table),
                evaluated_folds=len(folds),
                best=best,
                gridsearch_wall_seconds=elapsed,
                fit_assets=fit_assets,
            )
            seal_run(directory, manifest)
            logger.info("Busca %s concluída: 12 configurações, RMSE %.6f", name, best["rmse_mean"])
            gc.collect()
            return manifest
        except Exception as error:
            manifest.update(status="failed", failure_type=type(error).__name__, message=str(error))
            atomic_json(directory / "manifesto.json", manifest)
            raise
