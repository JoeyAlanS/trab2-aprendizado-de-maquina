"""Contratos do painel: pesos, isolamento do teste, integridade e interações."""

import sqlite3
from contextlib import closing
from dataclasses import replace

import numpy as np
import pytest
from conftest import ROOT
from streamlit.testing.v1 import AppTest

from enem_base.dashboard import (
    DIMENSIONS,
    aggregate_development,
    build_dashboard,
    filter_cube,
    grouped_statistics,
    load_dashboard,
    statistics,
)
from enem_base.database import build_database, load_database, readonly_connection
from enem_base.exploration import explore_development
from enem_base.ingestion import prepare
from enem_base.modeling import compare_models
from enem_base.provenance import write_json
from enem_base.relations import build_relations, load_relations, pair_cells
from enem_base.study import StudyConfig, create_study_splits, load_development


@pytest.fixture
def dashboard_study(example_config, tmp_path):
    source = tmp_path / "source.csv"
    rows = ["registro_id;alvo;Q005;" + ";".join(DIMENSIONS)]
    for i in range(61):
        score = str(0 if i == 0 else 300 + i * 2.3) if i < 60 else ""
        rows.append(
            f"SIM-{i:03};{score};{i % 5 + 1};{'CE' if i % 3 else 'SP'};"
            f"{i % 3 + 1};{'M' if i % 2 else 'F'};{i % 2};{'A' if i % 4 else 'B'}"
        )
    source.write_text("\n".join(rows) + "\n", encoding="utf-8")
    ingestion = replace(
        example_config,
        source=source,
        numeric_columns=("alvo", "Q005"),
        required_columns=("registro_id", "alvo", "Q005", *DIMENSIONS),
        expected_rows=61,
        expected_columns=None,
    )
    prepare(ingestion)
    config_path = tmp_path / "study.toml"
    config_path.write_text("# estudo fictício exclusivo dos testes\n", encoding="utf-8")
    dictionary = tmp_path / "dictionary.json"
    write_json(
        dictionary,
        {
            "columns": {
                name: {"description": name, "categories": {}}
                for name in ("alvo", "Q005", *DIMENSIONS)
            }
        },
    )
    study = StudyConfig(
        config_path=config_path,
        theme="Fictício",
        target="alvo",
        identifier="registro_id",
        kind="synthetic",
        dataset=ingestion.output,
        splits=tmp_path / "splits",
        results=tmp_path / "results",
        numeric=("Q005",),
        categorical=DIMENSIONS,
        dictionary=dictionary,
    )
    create_study_splits(study)
    return study


@pytest.fixture
def dashboard_bundle(dashboard_study, tmp_path):
    eda, cv, output = (tmp_path / name for name in ("eda", "cv", "dashboard"))
    explore_development(dashboard_study, eda)
    compare_models(dashboard_study, cv)
    build_dashboard(dashboard_study, output, eda, cv)
    return output


def test_aggregates_match_original_scores_and_weighted_groups(dashboard_study):
    frame, _ = load_development(dashboard_study)
    cube = aggregate_development(frame, "alvo")
    summary = statistics(cube)
    assert summary["count"] == len(frame)
    assert summary["mean"] == pytest.approx(frame.alvo.mean())
    assert summary["std"] == pytest.approx(frame.alvo.std())
    assert summary["zeros"] == frame.alvo.eq(0).sum()
    for uf in ("CE", "SP"):
        filtered = filter_cube(cube, {"SG_UF_PROVA": [uf]})
        original = frame.loc[frame.SG_UF_PROVA.eq(uf)]
        assert statistics(filtered)["mean"] == pytest.approx(original.alvo.mean())
        assert statistics(filtered)["count"] == len(original)
    grouped = grouped_statistics(cube, "TP_ESCOLA").set_index("TP_ESCOLA")
    expected = frame.groupby("TP_ESCOLA").alvo.mean()
    np.testing.assert_allclose(grouped.nota_media, expected)
    assert "registro_id" not in cube
    assert statistics(filter_cube(cube, {"SG_UF_PROVA": ["INEXISTENTE"]}))["mean"] is None


def test_aggregation_refuses_test_or_unobserved_targets(dashboard_study):
    frame, _ = load_development(dashboard_study)
    frame.loc[0, "partition"] = "test"
    with pytest.raises(ValueError, match="exclusivamente"):
        aggregate_development(frame, "alvo")
    frame.loc[0, "partition"] = "development"
    frame.loc[0, "alvo"] = np.nan
    with pytest.raises(ValueError, match="observado"):
        aggregate_development(frame, "alvo")


def test_bundle_integrity_and_refusal_to_overwrite(dashboard_bundle, dashboard_study, tmp_path):
    data = load_dashboard(dashboard_bundle)
    assert data.manifest["test_evaluated"] is False
    assert data.manifest["n_development"] == 48
    assert data.folds.evaluated_set.eq("development_cv").all()
    assert not {"registro_id", "NU_INSCRICAO"} & set(data.cube)
    with pytest.raises(FileExistsError):
        build_dashboard(dashboard_study, dashboard_bundle, tmp_path / "eda", tmp_path / "cv")
    with (dashboard_bundle / "resumo_cv.csv").open("a", encoding="utf-8") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="Integridade"):
        load_dashboard(dashboard_bundle)


def test_ui_filter_reset_and_empty_intersection(dashboard_bundle, monkeypatch):
    monkeypatch.setenv("ENEM_DASHBOARD_DIR", str(dashboard_bundle))
    at = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=30).run()
    assert not at.exception
    assert at.metric[0].value == "48"
    at.multiselect(key="filter_uf").set_value(["CE"]).run()
    assert not at.exception
    expected = statistics(
        filter_cube(load_dashboard(dashboard_bundle).cube, {"SG_UF_PROVA": ["CE"]})
    )
    assert at.metric[0].value == str(expected["count"])
    at.selectbox(key="filter_sex").set_value("F").run()
    at.selectbox(key="filter_training").set_value("1").run()
    assert not at.exception
    assert any("Nenhum participante" in item.value for item in at.info)
    at.button(key="reset_filters").click().run()
    assert not at.exception
    assert at.multiselect(key="filter_uf").value == []
    assert at.metric[0].value == "48"


def test_ui_pages_metrics_dictionary_and_exports(dashboard_bundle, monkeypatch):
    monkeypatch.setenv("ENEM_DASHBOARD_DIR", str(dashboard_bundle))
    at = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=30).run()
    at.switch_page("app_pages/explorar.py").run()
    assert not at.exception
    at.selectbox(key="explore_dimension").set_value("Renda familiar").run()
    assert not at.exception
    assert at.dataframe[0].value.participantes.sum() == 48
    assert at.get("download_button")
    at.switch_page("app_pages/modelos.py").run()
    assert not at.exception
    at.segmented_control(key="cv_metric").set_value("R²").run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 4
    at.switch_page("app_pages/metodo.py").run()
    assert not at.exception
    at.text_input(key="dictionary_search").set_value("Q006").run()
    assert not at.exception
    assert list(at.dataframe[0].value.Variável) == ["Q006"]
    at.text_input(key="dictionary_search").set_value("zz_sem_resultado").run()
    assert not at.exception
    assert any("Nenhuma variável" in item.value for item in at.info)


def test_ui_missing_bundle_explains_recovery(tmp_path, monkeypatch):
    monkeypatch.setenv("ENEM_DASHBOARD_DIR", str(tmp_path / "missing"))
    at = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=30).run()
    assert not at.exception
    assert at.error and "integridade" in at.error[0].value
    assert not at.metric


def test_relations_cover_all_pairs_and_missing_sensitivity(dashboard_study, tmp_path):
    output = tmp_path / "relations"
    build_relations(dashboard_study, output)
    data = load_relations(output)
    assert len(data.target) == 6
    assert len(data.pairs) == 15
    assert data.profiles.groupby("variable").n.sum().eq(48).all()
    assert data.cells.groupby(["variable_a", "variable_b"]).n.sum().eq(48).all()
    assert data.target.loc[data.target.kind.eq("categorical"), "pearson"].isna().all()
    cells = pair_cells(data, "TP_ESCOLA", "Q005")
    assert cells.n.sum() == 48
    assert cells.variable_a.eq("TP_ESCOLA").all()
    assert cells.variable_b.eq("Q005").all()
    with pytest.raises(ValueError, match="distintas"):
        pair_cells(data, "Q005", "Q005")
    expected = {
        key: data.manifest[key]
        for key in (
            "source_sha256",
            "splits_sha256",
            "study_sha256",
            "dictionary_sha256",
            "target",
            "n_development",
        )
    }
    expected["source_sha256"] = "different"
    with pytest.raises(ValueError, match="proveniências"):
        load_relations(output, expected)
    with (output / "pares.csv").open("a") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="Integridade"):
        load_relations(output)


def test_ui_relation_views_and_joint_orientation(
    dashboard_bundle, dashboard_study, tmp_path, monkeypatch
):
    output = tmp_path / "relations"
    build_relations(dashboard_study, output)
    monkeypatch.setenv("ENEM_DASHBOARD_DIR", str(dashboard_bundle))
    monkeypatch.setenv("ENEM_RELATIONS_DIR", str(output))
    at = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=30).run()
    at.switch_page("app_pages/relacoes.py").run()
    assert not at.exception
    assert at.metric[0].value == "6"
    assert at.metric[1].value == "15"
    at.selectbox(key="relation_field").set_value("Q005").run()
    assert not at.exception
    at.segmented_control(key="relations_mode").set_value("Cruzamentos de perfis").run()
    assert not at.exception
    assert at.dataframe[0].value.n.sum() == 48
    at.selectbox(key="joint_a").set_value("TP_ESCOLA").run()
    at.selectbox(key="joint_b").set_value("Q005").run()
    assert not at.exception
    assert at.dataframe[0].value.variable_a.eq("TP_ESCOLA").all()
    at.segmented_control(key="relations_mode").set_value("Associações entre entradas").run()
    assert not at.exception
    at.selectbox(key="pair_metric").set_value("eta_squared").run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 5
    at.segmented_control(key="relations_mode").set_value("Relatório PDF").run()
    assert not at.exception
    assert any(
        button.proto.label == "Baixar todas as tabelas (ZIP)"
        for button in at.get("download_button")
    )


@pytest.fixture
def study_database(dashboard_bundle, dashboard_study, tmp_path):
    relations = tmp_path / "relations"
    build_relations(dashboard_study, relations)
    output = tmp_path / "database"
    build_database(dashboard_study, output, dashboard_bundle, relations)
    return output / "enem2023.sqlite3"


def test_database_preserves_clean_rows_null_zero_and_partition_view(study_database):
    bundle = load_database(study_database)
    assert bundle.manifest["rows"] == 61
    assert bundle.manifest["partitions"] == {"development": 48, "test": 12}
    assert bundle.dashboard.manifest["storage"] == "sqlite"
    with readonly_connection(study_database) as connection:
        missing, zeros = connection.execute(
            "SELECT SUM(alvo IS NULL), SUM(alvo=0) FROM participantes"
        ).fetchone()
        assert (missing, zeros) == (1, 1)
        assert connection.execute("SELECT COUNT(*) FROM desenvolvimento").fetchone()[0] == 48
        assert connection.execute("SELECT COUNT(*) FROM participantes").fetchone()[0] == 61
        assert connection.execute("PRAGMA foreign_key_check").fetchone() is None
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("UPDATE participantes SET alvo=0")
    assert bundle.relations.profiles.groupby("variable").n.sum().eq(48).all()
    with closing(sqlite3.connect(study_database)) as connection:
        connection.execute("UPDATE participantes SET alvo=123 WHERE registro_id='SIM-000'")
        connection.commit()
    with pytest.raises(ValueError, match="alterado"):
        load_database(study_database)


def test_frontend_uses_sqlite_when_selected(study_database, monkeypatch):
    monkeypatch.setenv("ENEM_DATABASE", str(study_database))
    at = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=30).run()
    assert not at.exception
    assert at.metric[0].value == "48"
    assert any("Banco local" in item.value for item in at.caption)
    at.switch_page("app_pages/relacoes.py").run()
    assert not at.exception
    assert at.metric[0].value == "6"
    assert at.metric[1].value == "15"
