import pandas as pd
import pytest

from enem_base.acquisition import collect
from enem_base.integration import merge_context
from enem_base.provenance import sha256_file


def test_collection_preserves_source_and_checks_hash(tmp_path):
    source, destination = tmp_path / "source.csv", tmp_path / "raw" / "copy.csv"
    source.write_bytes(b"id;x\na;1\n")
    digest = sha256_file(source)
    manifest = collect(str(source), destination, digest)
    assert destination.read_bytes() == source.read_bytes()
    assert manifest["sha256"] == sha256_file(destination) == digest
    assert destination.with_name("copy.csv.source.json").exists()
    with pytest.raises(FileExistsError):
        collect(str(source), destination)


@pytest.mark.parametrize("issue", ["checksum", "size"])
def test_failed_collection_does_not_publish(tmp_path, issue):
    source, destination = tmp_path / "source", tmp_path / "raw" / "copy"
    source.write_bytes(b"example")
    with pytest.raises(ValueError):
        collect(
            str(source),
            destination,
            "0" * 64 if issue == "checksum" else None,
            max_bytes=2 if issue == "size" else 100,
        )
    assert not destination.exists()


def test_http_rejected_without_network_access(tmp_path):
    with pytest.raises(ValueError, match="HTTPS"):
        collect("http://example.test/data.csv", tmp_path / "data.csv")


def test_context_join_preserves_participants_and_reports_losses():
    participants = pd.DataFrame({"id": ["a", "b", "c"], "local": ["001", "001", "002"]})
    context = pd.DataFrame({"local": ["001"], "indicator": [10]})
    merged, report = merge_context(
        participants,
        context,
        key="local",
        source="Fonte fictícia",
        reference_year=2023,
        geography="local de observação fictício",
    )
    assert len(merged) == 3 and merged.id.tolist() == participants.id.tolist()
    assert report["matched_rows"] == 2 and report["unmatched_rows"] == 1
    assert pd.isna(merged.loc[2, "indicator"])


def test_context_join_rejects_duplicate_keys_and_wrong_year():
    participants = pd.DataFrame({"local": ["001"]})
    duplicate = pd.DataFrame({"local": ["001", "001"], "x": [1, 2]})
    with pytest.raises(ValueError, match="chave única"):
        merge_context(
            participants,
            duplicate,
            key="local",
            source="Fictícia",
            reference_year=2023,
            geography="fictícia",
        )
    with pytest.raises(ValueError, match="2023"):
        merge_context(
            participants,
            duplicate.iloc[:1],
            key="local",
            source="Fictícia",
            reference_year=2022,
            geography="fictícia",
        )
