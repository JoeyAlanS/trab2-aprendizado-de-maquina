"""Compor artigo verificável de dez páginas, sem executar aprendizado de máquina.

Dependências de publicação: reportlab e pypdf. Fontes Times New Roman locais
em --font-dir; não há substituição tipográfica silenciosa.
"""

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
CP = ROOT / "resultados/ciencias_natureza/checkpoint-6-2026-11-07"
TABLES = ROOT / "resultados/ciencias_natureza/checkpoint-5-2026-11-07/tabelas"
LABELS = {
    "stacking": "Stacking",
    "svm": "SVM linear",
    "random_forest": "Random Forest",
    "knn": "KNN",
    "bagging": "Bagging",
    "pasting": "Pasting",
    "boosting": "Boosting",
    "baseline": "Média",
    "linear": "Linear",
    "ridge": "Ridge",
    "arvore": "Árvore",
    "linear_reference": "Linear (ref.)",
}
INPUTS = {}


def source(path):
    INPUTS[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return path


def records(path):
    with source(path).open() as stream:
        return list(csv.DictReader(stream))


def number(value, digits=3):
    return f"{float(value):.{digits}f}".replace(".", ",")


def markup(text):
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(
        r"10⁻([³⁵⁶⁸])",
        lambda m: "10<super>-" + {"³": "3", "⁵": "5", "⁶": "6", "⁸": "8"}[m[1]] + "</super>",
        text,
    )
    return re.sub(
        r"(https://[^\s]+?)(?=\. Acesso|$)", r'<link href="\1" color="black">\1</link>', text
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font-dir", type=Path, default=ROOT / "tmp/fonts")
    args = parser.parse_args()
    for name, filename in [
        ("TNR", "Times.TTF"),
        ("TNR-Bold", "Timesbd.TTF"),
        ("TNR-Italic", "Timesi.TTF"),
        ("TNR-BoldItalic", "Timesbi.TTF"),
    ]:
        pdfmetrics.registerFont(TTFont(name, str(args.font_dir / filename)))
    pdfmetrics.registerFontFamily(
        "TNR", normal="TNR", bold="TNR-Bold", italic="TNR-Italic", boldItalic="TNR-BoldItalic"
    )
    base = ParagraphStyle(
        "body",
        fontName="TNR",
        fontSize=12,
        leading=18,
        alignment=TA_JUSTIFY,
        firstLineIndent=1.25 * cm,
        spaceAfter=6,
    )
    styles = {
        "body": base,
        "title": ParagraphStyle(
            "title",
            parent=base,
            fontName="TNR-Bold",
            alignment=TA_CENTER,
            firstLineIndent=0,
            spaceAfter=12,
        ),
        "center": ParagraphStyle(
            "center", parent=base, alignment=TA_CENTER, firstLineIndent=0, leading=14, spaceAfter=2
        ),
        "heading": ParagraphStyle(
            "heading",
            parent=base,
            fontName="TNR-Bold",
            firstLineIndent=0,
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "caption": ParagraphStyle(
            "caption",
            parent=base,
            fontSize=10,
            leading=12,
            firstLineIndent=0,
            alignment=TA_LEFT,
            spaceAfter=5,
        ),
        "abstract": ParagraphStyle(
            "abstract", parent=base, leading=12, firstLineIndent=0, spaceAfter=8
        ),
        "reference": ParagraphStyle(
            "reference",
            parent=base,
            leading=14,
            firstLineIndent=0,
            alignment=TA_LEFT,
            spaceAfter=14,
        ),
        "cell": ParagraphStyle(
            "cell", parent=base, leading=13, firstLineIndent=0, alignment=TA_LEFT, spaceAfter=0
        ),
    }
    width = A4[0] - 5 * cm

    def p(text, style="body"):
        return Paragraph(markup(text), styles[style])

    markdown_tables = {}

    def table(name):
        if name == "configuracoes":
            rows = [
                ["Modelo", "Parâmetros principais"],
                ["SVM", "LinearSVR; C=1; epsilon=0; tol=0,001; 5.000 iterações"],
                ["KNN", "25 vizinhos; pesos inversos à distância euclidiana"],
                ["Bagging", "20 árvores; profundidade 8; amostra de 70%, com reposição"],
                ["Pasting", "Mesmos parâmetros do Bagging, sem reposição"],
                ["Random Forest", "30 árvores; profundidade 12; max_features=0,8"],
                ["Boosting", "60 estágios; profundidade 2; taxa de aprendizado 0,1"],
                [
                    "Stacking",
                    "Linear + árvore (profundidade 12); combinador Ridge alpha=1; "
                    "três dobras internas",
                ],
            ]
            widths = [94, width - 94]
        elif name in ("iniciais", "variantes"):
            data = records(ROOT / "resultados/experimentos.csv")
            data = [r for r in data if r["row_type"] == "summary"]
            if name == "iniciais":
                data = sorted(
                    [r for r in data if r["variant"] == "original"], key=lambda r: float(r["rmse"])
                )
                rows = [["Modelo", "RMSE ± DP", "MAE ± DP", "R² ± DP", "Tempo (s)"]]
                for r in data:
                    cells = [LABELS[r["model"]]]
                    for key, digits in [("rmse", 3), ("mae", 3), ("r2", 4)]:
                        cells.append(
                            number(r[key], digits) + " ± " + number(r[key + "_std"], digits)
                        )
                    cells.append(number(r["elapsed_seconds"], 1))
                    rows.append(cells)
                widths = [95, 99, 99, 101, width - 394]
            else:
                names = {
                    "engineered": "Ridge + engenharia",
                    "selected": "Ridge + seleção",
                    "weighted": "Ridge + ponderação",
                    "without_socio": "Ridge sem bloco socioeconômico",
                    "without_uf": "Ridge sem UF da prova",
                }
                rows = [["Modelo / representação", "RMSE ± DP"]]
                for r in data:
                    if r["variant"] == "original":
                        continue
                    label = (
                        LABELS[r["model"]] + " + PCA"
                        if r["variant"] == "pca"
                        else names[r["variant"]]
                    )
                    rows.append([label, number(r["rmse"]) + " ± " + number(r["rmse_std"])])
                widths = [width * 0.69, width * 0.31]
        else:
            assert name == "teste"
            data = sorted(records(TABLES / "comparacao_teste.csv"), key=lambda r: float(r["rmse"]))
            rows = [["Modelo", "RMSE", "MAE", "R²", "Ajuste (s)"]]
            for r in data:
                rows.append(
                    [
                        LABELS[r["model"]],
                        number(r["rmse"]),
                        number(r["mae"]),
                        number(r["r2"], 4),
                        number(r["fit_seconds"], 3 if r["model"] == "baseline" else 2),
                    ]
                )
            widths = [115, 85, 85, 85, width - 370]
        markdown_tables[name] = (
            "| "
            + " | ".join(rows[0])
            + " |\n"
            + "|"
            + " --- |" * len(rows[0])
            + "\n"
            + "\n".join("| " + " | ".join(row) + " |" for row in rows[1:])
        )
        cells = [
            [p("**" + c + "**" if i == 0 else c, "cell") for c in row] for i, row in enumerate(rows)
        ]
        t = Table(cells, colWidths=widths, hAlign="LEFT")
        t.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEABOVE", (0, 0), (-1, 0), 0.7, colors.black),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                    ("LINEBELOW", (0, -1), (-1, -1), 0.7, colors.black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        return t

    text = source(ROOT / "docs/artigo-fonte.md").read_text()
    pages = text.split("<!-- pagina -->")
    assert len(pages) == 10
    destination = ROOT / "output/pdf/artigo_ciencias_natureza.pdf"
    destination.parent.mkdir(parents=True, exist_ok=True)
    draft = ROOT / "tmp/pdfs/artigo_checkpoint6.pdf"
    draft.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(draft), pagesize=A4, invariant=1, pageCompression=1)
    c.setTitle("Comparação nacional de modelos de aprendizado de máquina - ENEM 2023")
    c.setAuthor("Joey Alan de Freitas Solis; Paulo Henrico")
    c.setSubject("Artigo científico - Universidade de Fortaleza (Unifor) - Professor Tulio")
    layout = []
    for index, page in enumerate(pages, 1):
        y = A4[1] - 3 * cm
        abstract = False
        for block in re.split(r"\n\s*\n", page.strip()):
            block = block.strip()
            if not block:
                continue
            flowables = []
            if block.startswith("@autores"):
                for line in block.splitlines():
                    tag, value = line.split(" ", 1)
                    flowables.append(p(value, "caption" if tag == "@repositorio" else "center"))
            elif block.startswith("@figura"):
                name, title, height = block[len("@figura ") :].split(" | ")
                flowables = [
                    p(title, "caption"),
                    Image(
                        str(source(CP / "figuras" / f"{name}.png")),
                        width=width,
                        height=float(height) * inch,
                    ),
                ]
            elif block.startswith(("@tabela", "@quadro")):
                name, title = block.split(" ", 1)[1].split(" | ")
                flowables = [p(title, "caption"), table(name)]
            elif block.startswith("@fonte "):
                flowables = [p(block[7:], "caption")]
            elif block.startswith("@palavras "):
                flowables = [p(block[10:], "abstract")]
                abstract = False
            elif block.startswith("# "):
                flowables = [p(block[2:], "title")]
            elif block.startswith("##"):
                title = block.lstrip("# ")
                abstract = title == "Resumo"
                flowables = [p(title, "title" if title in ("Referências", "Resumo") else "heading")]
            else:
                flowables = [
                    p(block, "reference" if index == 10 else "abstract" if abstract else "body")
                ]
            for f in flowables:
                _, height = f.wrap(width, 10000)
                y -= height
                if y < 2 * cm - 0.01:
                    raise ValueError(
                        f"Página {index} excedeu a margem em {2 * cm - y:.1f} pt: {block[:90]}"
                    )
                f.drawOn(c, 2 * cm, y)
                y -= getattr(f, "spaceAfter", 4)
        c.setFont("TNR", 10)
        c.drawRightString(A4[0] - 3 * cm, A4[1] - 2 * cm, str(index))
        layout.append({"page": index, "content_bottom_pt": y, "remaining_pt": y - 2 * cm})
        c.showPage()
    c.save()
    reader = PdfReader(draft)
    assert len(reader.pages) == 10
    extracted = "\n".join(page.extract_text() for page in reader.pages)
    for required in [
        "Joey Alan de Freitas Solis",
        "Paulo Henrico",
        "Tulio",
        "538.486",
        "76,190",
        "Referências",
        "Figura 7",
        "Tabela 3",
    ]:
        assert required in extracted, required
    shutil.copyfile(draft, destination)
    shutil.copyfile(destination, ROOT / "docs/artigo.pdf")
    readable = text.replace("<!-- pagina -->", "")
    readable = re.sub(
        r"@(tabela|quadro) (\w+) \| (.+)", lambda m: m[3] + "\n\n" + markdown_tables[m[2]], readable
    )
    readable = re.sub(
        r"@figura (\w+) \| (.+) \| [0-9.]+",
        lambda m: (
            "![" + m[2] + "](../" + str((CP / "figuras" / (m[1] + ".png")).relative_to(ROOT)) + ")"
        ),
        readable,
    )
    readable = re.sub(
        r"^@(autores|instituicao|professor|repositorio|fonte|palavras) ", "", readable, flags=re.M
    )
    (ROOT / "docs/artigo.md").write_text(readable)

    (CP / "validacao_diagramacao.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "pages": 10,
                "font": "Times New Roman incorporada",
                "body_size_pt": 12,
                "body_leading_pt": 18,
                "margins_cm": {"top": 3, "right": 3, "left": 2, "bottom": 2},
                "layout": layout,
                "inputs": INPUTS,
                "pdf_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "visual_review": "pending",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(layout, indent=2))
    print(destination)


if __name__ == "__main__":
    main()
