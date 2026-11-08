"""Validação das buscas e receitas congeladas antes de qualquer acesso ao teste."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from enem_base.checkpointing import atomic_json, digest, run_lock
from enem_base.evidence import PROVENANCE_KEYS, comparison_rows, read_run, seal_run
from enem_base.modeling import estimator_spec, regression_metrics
from enem_base.provenance import runtime_metadata, sha256_file, verify_sha256
from enem_base.search_cache import load_array, read_json
from enem_base.study import load_development
from enem_base.tuning import MODELS, validate_search_protocol
from enem_base.variants import variant_catalog
from enem_base.workflow import initial_comparison


def validate_searches(config, root):
    protocol = validate_search_protocol(config, root)
    preflight = read_json(root / "validacao_cache.json")
    if (
        preflight.get("status") != "passed"
        or preflight.get("code_sha256") != protocol["numeric_code_sha256"]
        or any(preflight.get(k) != protocol[k] for k in PROVENANCE_KEYS)
    ):
        raise ValueError("Validação do cache não corresponde ao código e à fonte das buscas.")
    frame, _ = load_development(config)
    y = frame[config.target].to_numpy(dtype=float)
    labels = frame.validation_fold.to_numpy(dtype=int)
    inputs = {str(root / "validacao_cache.json"): sha256_file(root / "validacao_cache.json")}
    tables, checks = [], []
    for name in MODELS:
        directory = root / "buscas" / name
        manifest = read_run(directory, protocol)
        if manifest.get("configurations") != 12 or manifest.get("evaluated_folds") != 36:
            raise ValueError("Busca nacional incompleta.")
        if manifest["protocol_sha256"] != sha256_file(root / "protocolo_buscas.json"):
            raise ValueError("Busca de outro protocolo.")
        for path, expected in manifest["fit_assets"].items():
            verify_sha256(directory / path, expected, "Modelo de busca alterado")
        folds = pd.read_csv(directory / "metricas_dobras.csv")
        table = pd.read_csv(directory / "comparacao_configuracoes.csv")
        raw = pd.read_csv(directory / "gridsearch_cv_results.csv")
        if (
            set(zip(folds.candidate_id, folds.fold, strict=True))
            != {(i, f) for i in range(12) for f in range(3)}
            or len(folds) != 36
            or set(table.candidate_id) != set(range(12))
        ):
            raise ValueError("Cobertura de configurações/dobras incorreta.")
        for row in folds.itertuples():
            expected = protocol["candidates"][name][row.candidate_id]
            if json.loads(row.parameters_json) != expected["parameters"] or json.loads(
                row.warnings_json
            ):
                raise ValueError("Parâmetros ou avisos exigem investigação.")
            registered = protocol["folds"][row.fold]
            if (row.n_train, row.n_validation) != (
                registered["n_train"],
                registered["n_validation"],
            ):
                raise ValueError("Tamanhos das dobras incorretos.")
            fit = (
                directory
                / "modelos_ajustados"
                / (f"config-{row.candidate_id:02d}-dobra-{row.fold}.json")
            )
            meta = read_json(fit)
            context = {
                "protocol_sha256": sha256_file(root / "protocolo_buscas.json"),
                "model": name,
                "fold": row.fold,
                "train_data_sha256": registered["train_data_sha256"],
                "train_target_sha256": registered["train_target_sha256"],
                "parameters": expected["estimator"],
            }
            if meta["context"] != context:
                raise ValueError("Ajuste não corresponde aos dados e parâmetros registrados.")
            prediction = (
                root
                / "cache_buscas"
                / "predicoes"
                / name
                / (f"config-{row.candidate_id:02d}-dobra-{row.fold}.npy")
            )
            values = load_array(
                prediction,
                {
                    **context,
                    "fit_sha256": meta["sha256"],
                    "validation_data_sha256": registered["validation_data_sha256"],
                },
            )
            metrics = regression_metrics(y[labels == row.fold], values)
            for metric, actual in metrics.items():
                np.testing.assert_allclose(actual, getattr(row, metric), rtol=0, atol=1e-9)
                sign = 1 if metric == "r2" else -1
                np.testing.assert_allclose(
                    actual,
                    sign * raw.iloc[row.candidate_id][f"split{row.fold}_test_{metric}"],
                    rtol=0,
                    atol=1e-9,
                )
            checks.append(
                {
                    "model": name,
                    "candidate_id": row.candidate_id,
                    "fold": row.fold,
                    "prediction_sha256": sha256_file(prediction),
                    **metrics,
                }
            )
        for row in table.itertuples():
            subset = folds.loc[folds.candidate_id.eq(row.candidate_id)]
            for metric in ("rmse", "mae", "r2"):
                for suffix, actual in (
                    ("mean", subset[metric].mean()),
                    ("std", subset[metric].std(ddof=0)),
                ):
                    np.testing.assert_allclose(
                        actual, getattr(row, metric + "_" + suffix), rtol=0, atol=1e-9
                    )
        inputs[str(directory / "manifesto.json")] = sha256_file(directory / "manifesto.json")
        tables.append(table)
    atomic_json(
        root / "validacao_buscas.json",
        {
            "status": "passed",
            "protocol_sha256": sha256_file(root / "protocolo_buscas.json"),
            "configurations": 60,
            "fold_evaluations": len(checks),
            "warnings": 0,
            "independent_prediction_metrics": checks,
            "inputs": inputs,
            "test_evaluated": False,
        },
    )
    return protocol, pd.concat(tables, ignore_index=True), inputs


def recipe_estimator(config, recipe):
    catalog, _ = variant_catalog(config, recipe["variant"])
    model = catalog[recipe["model"]].set_params(**recipe["parameters"])
    if estimator_spec(model) != recipe["estimator"]:
        raise ValueError("Estimador difere da receita congelada.")
    return model


def freeze_recipes(config, root, variant_paths):
    directory = root / "congelamento"
    with run_lock(directory):
        if directory.exists():
            return load_frozen(config, root)
        if (config.splits / "avaliacao_final.json").exists():
            raise ValueError("Teste já aberto: não selecionar novas configurações.")
        p, searches, inputs = validate_searches(config, root)
        original, _ = initial_comparison(config, [Path(s) for s in p["original_paths"]], p)
        candidates, initial = [], {}

        def add(name, variant, parameters, group, source, candidate_id=None):
            catalog, features = variant_catalog(config, variant)
            model = catalog[name].set_params(**parameters)
            item = {
                "model": name,
                "variant": variant,
                "parameters": parameters,
                "estimator": estimator_spec(model),
                "features": features,
                "source": source,
                "candidate_id": candidate_id,
                **{m + "_mean": float(group[m].mean()) for m in ("rmse", "mae", "r2")},
                **{m + "_std": float(group[m].std(ddof=0)) for m in ("rmse", "mae", "r2")},
            }
            candidates.append(item)
            return item

        for name, group in original.groupby("model"):
            params = {"regressor__n_jobs": 6} if name == "random_forest" else {}
            initial[name] = add(name, "original", params, group, p["original_paths"])
        chosen = dict(initial)
        changes = []
        for name in MODELS:
            best = (
                searches.loc[searches.model.eq(name)]
                .sort_values(
                    ["rmse_mean", "mae_mean", "r2_mean", "candidate_id"],
                    ascending=[True, True, False, True],
                )
                .iloc[0]
            )
            params = json.loads(best.parameters_json)
            if name == "svm":
                params["regressor__max_iter"] = 50_000
            if name == "random_forest":
                params["regressor__n_jobs"] = 6
            source = root / "buscas" / name
            folds = pd.read_csv(source / "metricas_dobras.csv")
            searched = add(
                name,
                "original",
                params,
                folds.loc[folds.candidate_id.eq(best.candidate_id)],
                str(source),
                int(best.candidate_id),
            )
            improvement = initial[name]["rmse_mean"] - searched["rmse_mean"]
            if improvement > p["retain_initial_if_improvement_at_most"]:
                chosen[name] = searched
            changes.append(
                {
                    "model": name,
                    "initial_rmse": initial[name]["rmse_mean"],
                    "best_search_rmse": searched["rmse_mean"],
                    "selected_rmse": chosen[name]["rmse_mean"],
                    "improvement": improvement,
                    "initial_retained": chosen[name] is initial[name],
                    "parameters_json": json.dumps(chosen[name]["parameters"], sort_keys=True),
                }
            )
        covered = {}
        for path in variant_paths:
            rows, manifest = comparison_rows(path, p)
            variant = manifest["variant"]
            covered.setdefault(variant, set()).update(rows.model)
            inputs[str(path / "manifesto.json")] = sha256_file(path / "manifesto.json")
            for name, group in rows.groupby("model"):
                if name != "baseline":
                    add(name, variant, {}, group, str(path))
        required = {"engineered", "selected", "pca", "weighted", "without_socio", "without_uf"}
        if required - covered.keys() or len(covered.get("pca", set()) - {"baseline"}) < 2:
            raise ValueError("Comparações de variantes incompletas.")
        if any("ridge" not in covered[v] for v in required - {"pca"}):
            raise ValueError("As variantes precisam comparar Ridge.")
        # Uma busca numericamente equivalente não substitui a configuração inicial.
        eligible = [
            r
            for r in candidates
            if r["model"] != "baseline"
            and (r["variant"] != "original" or r is chosen.get(r["model"]))
        ]
        academic = min(
            eligible,
            key=lambda r: (r["rmse_mean"], r["mae_mean"], -r["r2_mean"], r["model"], r["variant"]),
        )
        recipes = {name: chosen[name] for name in p["primary_models"]}
        recipes.update(baseline=initial["baseline"], linear_reference=initial["linear"])
        academic_label = next(
            (name for name, r in recipes.items() if r["estimator"] == academic["estimator"]), None
        )
        if academic_label is None:
            academic_label = "academic_solution"
            recipes[academic_label] = academic
        curves = list(p["primary_models"])
        if academic_label not in curves:
            curves.append(academic_label)
        inputs.update(p["inputs"])
        inputs[str(root / "validacao_buscas.json")] = sha256_file(root / "validacao_buscas.json")
        frozen = {
            **{
                k: p[k]
                for k in (
                    "source_sha256",
                    "splits_sha256",
                    "study_sha256",
                    "dictionary_sha256",
                    "target",
                    "n_development",
                )
            },
            "recipes": recipes,
            "primary_models": p["primary_models"],
            "curve_models": curves,
            "academic_solution": academic_label,
            "academic_recipe": academic,
            "inputs": inputs,
            "search_protocol_sha256": sha256_file(root / "protocolo_buscas.json"),
            "selection_criterion": "RMSE médio, MAE médio, R² médio; apenas desenvolvimento",
            "test_ranking_is_descriptive": True,
            "test_criterion": [
                "rmse ascending",
                "mae ascending",
                "r2 descending",
                "model ascending",
            ],
            "score_edges": [0, 400, 500, 600, 700, "+inf"],
            "group_fields": ["TP_ESCOLA", "SG_UF_PROVA", "Q006"],
            "learning_fractions": [0.1, 0.25, 0.5, 0.75, 1.0],
            "selection_code_sha256": sha256_file(Path(__file__)),
            "test_evaluated": False,
        }
        directory.mkdir(parents=True)
        atomic_json(directory / "receitas.json", frozen)
        atomic_json(directory / "candidatos.json", candidates)
        pd.DataFrame(changes).to_csv(directory / "antes_depois_buscas.csv", index=False)
        seal_run(
            directory,
            {
                **runtime_metadata(),
                **{
                    k: frozen[k]
                    for k in (
                        "source_sha256",
                        "splits_sha256",
                        "study_sha256",
                        "dictionary_sha256",
                        "target",
                    )
                },
                "status": "completed",
                "evaluated_set": "development_cv",
                "test_evaluated": False,
                "experiment_kind": "frozen_checkpoint4_recipes",
                "recipe_digest": digest(frozen),
            },
        )
        return frozen


def load_frozen(config, root):
    p = validate_search_protocol(config, root)
    read_run(root / "congelamento", p)
    frozen = read_json(root / "congelamento" / "receitas.json")
    if frozen["selection_code_sha256"] != sha256_file(Path(__file__)):
        raise ValueError("Código de seleção alterado após congelamento.")
    for source, expected in frozen["inputs"].items():
        verify_sha256(Path(source), expected, "Evidência da seleção alterada")
    for recipe in frozen["recipes"].values():
        recipe_estimator(config, recipe)
    return frozen
