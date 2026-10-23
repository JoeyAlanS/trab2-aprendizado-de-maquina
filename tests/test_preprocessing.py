import numpy as np
import pandas as pd
import pytest

from enem_base.preprocessing import build_preprocessor


def test_preprocessor_consumes_nullable_parquet_output(example_config):
    from enem_base.ingestion import prepare

    prepare(example_config)
    data = pd.concat([pd.read_parquet(p) for p in sorted(example_config.output.glob("*.parquet"))])
    original = data.copy(deep=True)
    transformer = build_preprocessor(
        ["medida_a", "medida_b"], ["categoria", "codigo_local"], identifier="registro_id"
    )
    transformed = transformer.fit_transform(data.iloc[:8])
    validation = transformer.transform(data.iloc[8:])
    assert transformed.shape[1] == validation.shape[1]
    assert transformed.shape[0] == 8 and validation.shape[0] == 4
    pd.testing.assert_frame_equal(data, original)


@pytest.mark.parametrize(
    "column",
    [
        "NU_NOTA_MT",
        "NU_NOTA_COMP1",
        "TX_RESPOSTAS_CN",
        "TX_GABARITO_LC",
        "TP_PRESENCA_MT",
        "TP_STATUS_REDACAO",
        "NU_INSCRICAO",
        "NU_ANO",
        "CO_PROVA_MT",
        "id",
    ],
)
def test_leakage_and_control_columns_are_blocked(column):
    with pytest.raises(ValueError, match="bloqueadas"):
        build_preprocessor([], [column], identifier="id")


def test_imputer_and_categories_are_learned_only_from_train():
    train = pd.DataFrame({"x": [1.0, 3.0, np.nan], "category": ["A", "B", np.nan]})
    validation = pd.DataFrame({"x": [1000.0, np.nan], "category": ["NEW", "A"]})
    transformer = build_preprocessor(["x"], ["category"], identifier="id")
    assert not hasattr(transformer, "transformers_")
    transformer.fit(train)
    assert transformer.named_transformers_["numeric"]["imputer"].statistics_[0] == 2
    before = transformer.named_transformers_["categorical"]["encoder"].categories_[0].copy()
    result = transformer.transform(validation)
    assert result.shape[0] == 2
    assert transformer.named_transformers_["numeric"]["imputer"].statistics_[0] == 2
    assert "NEW" not in before
    np.testing.assert_array_equal(
        transformer.named_transformers_["categorical"]["encoder"].categories_[0], before
    )


def test_duplicate_feature_and_target_are_blocked():
    with pytest.raises(ValueError):
        build_preprocessor(["x"], ["x"], identifier="id")
    with pytest.raises(ValueError):
        build_preprocessor(["future_target"], [], identifier="id", target="future_target")
