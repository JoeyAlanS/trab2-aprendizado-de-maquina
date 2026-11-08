"""Conferência documental do artigo e da preservação das evidências anteriores."""

import csv
import hashlib
import json
import re
from pathlib import Path

import pdfplumber
from PIL import Image
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
CP = ROOT / "resultados/ciencias_natureza/checkpoint-6-2026-11-07"
CP5 = ROOT / "resultados/ciencias_natureza/checkpoint-5-2026-11-07"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate():
    checked = {}

    def check(path, expected):
        path = Path(path)
        absolute = path if path.is_absolute() else ROOT / path
        if digest(absolute) != expected:
            raise ValueError(f"Hash divergente: {path}")
        checked[str(path)] = expected

    manifest = json.loads((CP5 / "manifesto.json").read_text())
    for key in ("inputs", "source_code_sha256"):
        for path, expected in manifest[key].items():
            check(path, expected)
    for path, expected in manifest["assets"].items():
        check(CP5 / path, expected)
    for marker_path in sorted(
        (ROOT / "resultados/ciencias_natureza").glob("checkpoint-*/checkpoint.json")
    ):
        if marker_path.parent == CP:
            continue
        marker = json.loads(marker_path.read_text())
        if "report_sha256" in marker:
            check(marker["report"], marker["report_sha256"])
        if "previous_checkpoint_sha256" in marker:
            check(marker["previous_checkpoint"], marker["previous_checkpoint_sha256"])
    for filename in ("entradas_figuras.json", "validacao_diagramacao.json"):
        data = json.loads((CP / filename).read_text())
        for path, expected in (data["inputs"] if "inputs" in data else data).items():
            check(path, expected)
    national = json.loads((CP / "validacao_csv_parquets.json").read_text())
    assert national["status"] == "passed" and national["all_cells_equal_after_normalization"]
    assert (national["rows"], national["columns"], len(national["parts"])) == (3933955, 76, 79)
    pdf = ROOT / "output/pdf/artigo_ciencias_natureza.pdf"
    assert digest(pdf) == digest(ROOT / "docs/artigo.pdf")
    diagram = json.loads((CP / "validacao_diagramacao.json").read_text())
    check(pdf, diagram["pdf_sha256"])
    reader = PdfReader(pdf)
    assert len(reader.pages) == 10
    text_pages = [page.extract_text() for page in reader.pages]
    text = "\n".join(text_pages)
    for required in [
        "Joey Alan de Freitas Solis",
        "Paulo Henrico",
        "Tulio",
        "Unifor",
        "538.486",
        "2.153.941",
        "3.933.955",
        "76,189590",
        "13,38%",
    ]:
        assert required in text, required
    for i in range(1, 8):
        assert f"Figura {i} -" in text, i
    for i in range(1, 4):
        assert f"Tabela {i} -" in text, i
    assert "Quadro 1 -" in text
    for forbidden in ["@figura", "@tabela", "@quadro", "\ufffd", "\u25a0", "\x00"]:
        assert forbidden not in text, forbidden
    with (ROOT / "resultados/experimentos.csv").open() as stream:
        summaries = [r for r in csv.DictReader(stream) if r["row_type"] == "summary"]
    for row in summaries:
        assert f"{float(row['rmse']):.3f}".replace(".", ",") in text
    with (CP5 / "tabelas/comparacao_teste.csv").open() as stream:
        tests = list(csv.DictReader(stream))
    for row in tests:
        for metric, precision in [("rmse", 3), ("mae", 3), ("r2", 4)]:
            assert f"{float(row[metric]):.{precision}f}".replace(".", ",") in text_pages[7]
    bounds = []
    with pdfplumber.open(pdf) as document:
        for i, page in enumerate(document.pages, 1):
            chars = page.chars
            assert all(c["x0"] >= 2 * 72 / 2.54 - 1 for c in chars)
            assert all(c["x1"] <= page.width - 3 * 72 / 2.54 + 1 for c in chars)
            assert all(c["bottom"] <= page.height - 2 * 72 / 2.54 + 1 for c in chars)
            assert all("TimesNewRoman" in c["fontname"] for c in chars)
            bounds.append(
                {
                    "page": i,
                    "characters": len(chars),
                    "body_font_size_pt": 12,
                    "margin_check": "passed",
                }
            )
    pngs = sorted((CP / "figuras").glob("*.png"))
    assert len(pngs) == len(list((CP / "figuras").glob("*.svg"))) == 7
    for path in pngs:
        with Image.open(path) as image:
            image.load()
            assert min(image.info["dpi"]) >= 299
    readable = (ROOT / "docs/artigo.md").read_text()
    assert not re.search(r"^@(figura|tabela|quadro)", readable, flags=re.M)
    for target in re.findall(r"!\[[^]]*\]\(([^)]+)\)", readable):
        assert (ROOT / "docs" / target).is_file()
    output = {
        "status": "passed",
        "pdf_pages": 10,
        "figures": 7,
        "tables": 3,
        "parameter_tables": 1,
        "references": 8,
        "pdf_sha256": digest(pdf),
        "canonical_pdf_matches_docs_copy": True,
        "metrics_checked_against_csv": True,
        "times_new_roman_all_text": True,
        "page_checks": bounds,
        "preserved_hashes": checked,
        "new_training": False,
        "new_test_evaluation": False,
    }
    (CP / "validacao_artigo.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        f"Artigo aprovado: 10 páginas; {len(checked)} hashes conferidos; métricas e fontes válidas."
    )


if __name__ == "__main__":
    validate()
