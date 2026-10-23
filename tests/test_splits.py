import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from enem_base.splits import make_split_table, save_splits


@pytest.fixture
def observations():
    # Nenhum desses valores é uma nota real ou alvo atribuído à equipe.
    return pd.DataFrame(
        {
            "id": [f"FAKE-{i:02}" for i in range(21)],
            "generic_target": [0.0] + list(range(1, 20)) + [None],
            "other_score": [None] * 21,
        }
    )


def test_partitions_are_disjoint_reproducible_and_keep_zero(observations):
    table, summary = make_split_table(
        observations, identifier="id", target="generic_target", kind="synthetic"
    )
    again, _ = make_split_table(
        observations, identifier="id", target="generic_target", kind="synthetic"
    )
    assert_frame_equal(table, again)
    development = table[table.partition == "development"]
    test = table[table.partition == "test"]
    assert len(development) == 16 and len(test) == 4
    assert set(development.id).isdisjoint(test.id)
    assert set(development.validation_fold) == {0, 1, 2}
    assert development.validation_fold.notna().all()
    assert test.validation_fold.isna().all()
    assert "FAKE-00" in set(table.id)
    assert "FAKE-20" not in set(table.id)
    assert set(table) == {"id", "partition", "validation_fold"}
    assert summary["missing_target"] == 1


def test_target_is_required_and_enem_target_must_be_from_assignment(observations):
    with pytest.raises(ValueError, match="ainda não foi definido"):
        make_split_table(observations, identifier="id", target=None, kind="enem2023")
    with pytest.raises(ValueError, match="cinco notas"):
        make_split_table(observations, identifier="id", target="generic_target", kind="enem2023")


def test_persisted_partitions_cannot_be_overwritten(observations, tmp_path):
    output = tmp_path / "splits"
    summary = save_splits(
        observations,
        output,
        identifier="id",
        target="generic_target",
        kind="synthetic",
        source_sha256="a" * 64,
    )
    assert (output / "particoes.parquet").exists()
    assert summary["source_sha256"] == "a" * 64
    with pytest.raises(FileExistsError):
        save_splits(
            observations,
            output,
            identifier="id",
            target="generic_target",
            kind="synthetic",
            source_sha256="a" * 64,
        )


@pytest.mark.parametrize("issue", ["duplicate", "missing_id", "infinite", "text"])
def test_inconsistent_inputs_are_rejected(observations, issue):
    frame = observations.copy()
    if issue == "duplicate":
        frame.loc[0, "id"] = frame.loc[1, "id"]
    elif issue == "missing_id":
        frame.loc[0, "id"] = None
    else:
        frame["generic_target"] = frame.generic_target.astype(object)
        frame.loc[0, "generic_target"] = float("inf") if issue == "infinite" else "broken"
    with pytest.raises(ValueError):
        make_split_table(frame, identifier="id", target="generic_target", kind="synthetic")
