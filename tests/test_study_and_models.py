import json
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from conftest import ROOT
from sklearn.base import clone

from enem_base.exploration import explore_development
from enem_base.ingestion import prepare
from enem_base.modeling import compare_models, estimator_spec, model_catalog, regression_metrics
from enem_base.study import StudyConfig, create_study_splits, load_development, load_study


@pytest.fixture
def synthetic_study(example_config, tmp_path):
    source = tmp_path / "source.csv"
    rows = ["registro_id;alvo;x;TP_ESCOLA;categoria"]
    for i in range(31):
        target = str(100 + 3 * i) if i < 30 else ""
        rows.append(f"SIM-{i:03};{target};{i};{i % 3};{'A' if i % 2 else 'B'}")
    source.write_text("\n".join(rows) + "\n", encoding="utf-8")
    ingestion = replace(
        example_config,
        source=source,
        numeric_columns=("alvo", "x"),
        required_columns=("registro_id", "alvo", "x", "TP_ESCOLA", "categoria"),
        expected_rows=31,
    )
    prepare(ingestion)
    config_path = tmp_path / "study.toml"
    config_path.write_text("# teste fictício de proveniência\n", encoding="utf-8")
    study = StudyConfig(
        config_path=config_path,
        theme="Fictício",
        target="alvo",
        identifier="registro_id",
        kind="synthetic",
        dataset=ingestion.output,
        splits=tmp_path / "splits",
        results=tmp_path / "results",
        numeric=("x",),
        categorical=("TP_ESCOLA", "categoria"),
    )
    create_study_splits(study)
    return study


def test_natureza_assignment_is_explicit_and_safe():
    study = load_study(ROOT / "configs/ciencias_natureza.toml")
    assert study.target == "NU_NOTA_CN" and study.kind == "enem2023"
    assert "NU_NOTA_CN" not in study.features
    assert not any(name.startswith("TP_PRESENCA_") for name in study.features)


def test_only_development_ids_are_returned(synthetic_study):
    frame, metadata = load_development(synthetic_study)
    partitions = pd.read_parquet(synthetic_study.splits / "particoes.parquet")
    test_ids = partitions.loc[partitions.partition.eq("test"), "registro_id"]
    assert len(frame) == 24 and metadata["n_development"] == 24
    assert set(frame.registro_id).isdisjoint(test_ids)
    assert frame.partition.eq("development").all()
    assert metadata["test_evaluated"] is False
    assert "SIM-030" not in set(frame.registro_id)


def test_altered_partition_is_rejected(synthetic_study):
    path = synthetic_study.splits / "particoes.parquet"
    frame = pd.read_parquet(path)
    frame.loc[0, "partition"] = "modified"
    frame.to_parquet(path, index=False)
    with pytest.raises(ValueError, match="partições"):
        load_development(synthetic_study)


def test_dictionary_categories_are_checked_on_development(synthetic_study, tmp_path):
    dictionary = tmp_path / "dictionary.json"
    dictionary.write_text(
        json.dumps(
            {
                "columns": {
                    "TP_ESCOLA": {"categories": {"0": "Zero", "1": "Um"}},
                    "categoria": {"categories": {"A": "A", "B": "B"}},
                }
            }
        ),
        encoding="utf-8",
    )
    configured = replace(synthetic_study, dictionary=dictionary)
    with pytest.raises(ValueError, match="Categoria fora do dicionário"):
        load_development(configured)


def test_comparison_records_all_development_rows_and_no_test(synthetic_study, tmp_path):
    output = tmp_path / "comparison"
    manifest = compare_models(synthetic_study, output)
    rows = pd.read_csv(output / "experimentos.csv")
    assert len(rows) == 12
    assert set(rows.evaluated_set) == {"development_cv"}
    assert rows.test_evaluated.eq(False).all()
    assert rows.n_train.eq(16).all() and rows.n_evaluated.eq(8).all()
    assert set(rows.fold) == {0, 1, 2}
    assert manifest["status"] == "completed" and manifest["test_evaluated"] is False
    assert len(pd.read_csv(output / "resumo_cv.csv")) == 4
    with pytest.raises(FileExistsError):
        compare_models(synthetic_study, output)


def test_catalog_contains_all_required_families_and_internal_stacking_pipelines(synthetic_study):
    catalog = model_catalog(synthetic_study)
    assert set(catalog) == {
        "baseline",
        "linear",
        "ridge",
        "svm",
        "arvore",
        "knn",
        "bagging",
        "pasting",
        "random_forest",
        "boosting",
        "stacking",
    }
    assert catalog["pasting"]["regressor"].bootstrap is False
    assert catalog["pasting"]["regressor"].max_samples < 1
    assert catalog["bagging"]["regressor"].bootstrap is True
    for _, estimator in catalog["stacking"].estimators:
        assert "preparation" in estimator.named_steps
    for estimator in catalog.values():
        clone(estimator)


def test_parameter_spec_is_complete_stable_json(synthetic_study):
    catalog = model_catalog(synthetic_study)
    spec = {name: estimator_spec(model) for name, model in catalog.items()}
    serialized = json.dumps(spec, ensure_ascii=False, allow_nan=False)
    assert "0x" not in serialized and "..." not in serialized
    assert spec["baseline"]["parameters"]["strategy"] == "mean"
    steps = spec["ridge"]["parameters"]["steps"]
    assert steps[-1][1]["parameters"]["alpha"] == 1.0


def test_metrics_and_constant_group_r2():
    result = regression_metrics([1, 2, 3], [1, 1, 1])
    assert result["mae"] == 1
    assert result["rmse"] == pytest.approx(np.sqrt(5 / 3))
    assert regression_metrics([1, 1], [1, 1])["r2"] is None
    with pytest.raises(ValueError):
        regression_metrics([1, 2], [np.nan, 3])


def test_exploration_uses_development_and_preserves_source(synthetic_study, tmp_path):
    output = tmp_path / "eda"
    report = explore_development(synthetic_study, output)
    assert report["rows"] == 24 and report["test_evaluated"] is False
    assert (output / "distribuicao_nota_cn.png").exists()
    assert (
        json.loads((output / "diagnostico_desenvolvimento.json").read_text(encoding="utf-8"))[
            "evaluated_set"
        ]
        == "development"
    )
