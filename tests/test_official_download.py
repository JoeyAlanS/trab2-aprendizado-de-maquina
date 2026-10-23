import zipfile

import pytest

from enem_base.official import obtain_official


def test_official_archive_extraction_is_selective_and_preserves_original(tmp_path):
    archive = tmp_path / "microdados_enem_2023.zip"
    with zipfile.ZipFile(archive, "w") as package:
        package.writestr("DADOS/MICRODADOS_ENEM_2023.csv", "id;x\na;1\n")
        package.writestr("DICIONARIO/Dicionario_2023.txt", "Exemplo fictício")
        package.writestr("PROVAS/arquivo_sem_interesse.pdf", b"not selected")
    before = archive.read_bytes()
    manifest = obtain_official(tmp_path)
    assert archive.read_bytes() == before
    assert (tmp_path / "MICRODADOS_ENEM_2023.csv").exists()
    assert (tmp_path / "Dicionario_2023.txt").exists()
    assert not (tmp_path / "arquivo_sem_interesse.pdf").exists()
    assert manifest["checksum_compared_to_publisher"] is False
    assert len(manifest["extracted"]) == 2
    assert not (tmp_path / ".enem2023-download.lock").exists()


def test_concurrent_download_is_blocked(tmp_path):
    lock = tmp_path / ".enem2023-download.lock"
    lock.write_text("another process")
    with pytest.raises(FileExistsError):
        obtain_official(tmp_path)
    assert lock.read_text() == "another process"


def test_incomplete_or_invalid_archive_cannot_extract(tmp_path):
    (tmp_path / "microdados_enem_2023.zip").write_bytes(b"invalid")
    with pytest.raises(zipfile.BadZipFile):
        obtain_official(tmp_path)
    assert not (tmp_path / "enem2023.source.json").exists()


def test_preexisting_partial_file_is_preserved(tmp_path):
    with zipfile.ZipFile(tmp_path / "microdados_enem_2023.zip", "w") as package:
        package.writestr("DADOS/MICRODADOS_ENEM_2023.csv", "id;x\na;1\n")
    partial = tmp_path / "MICRODADOS_ENEM_2023.csv.part"
    partial.write_bytes(b"preexisting content")
    with pytest.raises(FileExistsError):
        obtain_official(tmp_path)
    assert partial.read_bytes() == b"preexisting content"
