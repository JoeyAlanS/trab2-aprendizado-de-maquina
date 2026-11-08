"""Gerar fontes portáveis da entrega; não treina nem consulta novos dados de teste."""

import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "relatorio"
CP6 = ROOT / "resultados/ciencias_natureza/checkpoint-6-2026-11-07"
CP7 = ROOT / "resultados/ciencias_natureza/checkpoint-7-2026-11-07"


def esc(text):
    substitutions = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "²": r"\textsuperscript{2}",
        "³": r"\textsuperscript{3}",
        "⁵": r"\textsuperscript{5}",
        "⁶": r"\textsuperscript{6}",
        "⁸": r"\textsuperscript{8}",
        "⁻": r"\textsuperscript{-}",
        "±": r"\ensuremath{\pm}",
        "×": r"\ensuremath{\times}",
        "≥": r"\ensuremath{\geq}",
        "–": "-",
        "—": "-",
        "−": "-",
        "∞": r"\ensuremath{\infty}",
    }
    return "".join(substitutions.get(c, c) for c in text)


def inline(text):
    parts = re.split(r"(https://\S+|(?:resultados|scripts|dados|src|\.venv)/\S+|\*\*.*?\*\*)", text)
    result = []
    for part in parts:
        if part.startswith("https://"):
            url = part.rstrip(".,;")
            result.append(r"\url{" + url + "}" + part[len(url) :])
        elif "/" in part and not part.startswith("**") and " " not in part:
            path = part.rstrip(".,;")
            result.append(r"\nolinkurl{" + path + "}" + part[len(path) :])
        elif part.startswith("**"):
            result.append(r"\textbf{" + esc(part[2:-2]) + "}")
        else:
            result.append(esc(part))
    return "".join(result)


def rows_from_markdown(block):
    return [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in block.splitlines()
        if line.strip().startswith("|") and not re.fullmatch(r"[| :\-]+", line.strip())
    ]


def table(rows, name=None, long=False):
    count = len(rows[0])
    if name == "iniciais":
        widths = [".20", ".22", ".22", ".22", ".14"]
    elif name == "configuracoes":
        widths = [".23", ".77"]
    elif name == "variantes":
        widths = [".68", ".32"]
    elif name == "teste":
        widths = [".27", ".18", ".18", ".16", ".21"]
    elif count == 2:
        widths = [".46", ".54"]
    elif count == 3:
        widths = [".25", ".35", ".40"]
    else:
        widths = [".31", ".23", ".23", ".23"] if count == 4 else [str(1 / count)] * count
    # Allocate the actual width after subtracting inter-column padding.
    columns = (
        "@{}"
        + "".join(
            r">{\raggedright\arraybackslash}p{\dimexpr"
            + w
            + r"\linewidth-"
            + str((count - 1) * 6 / count)
            + r"pt\relax}"
            for w in widths
        )
        + "@{}"
    )
    env = "longtable" if long else "tabular"
    lines = [
        r"\begingroup\singlespacing\setlength{\tabcolsep}{3pt}",
        r"\renewcommand{\arraystretch}{1.08}",
        (r"\noindent" if not long else "") + r"\begin{" + env + "}{" + columns + "}",
        r"\toprule",
    ]
    header = " & ".join(r"\textbf{" + inline(c) + "}" for c in rows[0]) + r" \\"
    lines += [header, r"\midrule"]
    if long:
        lines += [r"\endfirsthead", r"\toprule", header, r"\midrule\endhead"]
    lines += [" & ".join(inline(c) for c in row) + r" \\" for row in rows[1:]]
    lines += [r"\bottomrule", r"\end{" + env + "}", r"\endgroup\par\vspace{4pt}"]
    return "\n".join(lines)


PREAMBLE = r"""% Compilador recomendado no Overleaf: XeLaTeX. Também compatível com pdfLaTeX.
\documentclass[12pt,a4paper]{article}
\usepackage{iftex}
\ifPDFTeX\usepackage[utf8]{inputenc}\fi
\usepackage[T1]{fontenc}
\usepackage[brazil]{babel}
\usepackage{mathptmx}
\usepackage[left=2cm,right=3cm,top=3cm,bottom=2cm,headheight=15pt]{geometry}
\usepackage{graphicx,booktabs,array,longtable,setspace,needspace,fancyhdr}
\usepackage{xurl}
\usepackage[hidelinks,unicode]{hyperref}
\urlstyle{same}
\setlength{\parindent}{1.25cm}
\setlength{\parskip}{3pt}
\setlength{\LTpre}{2pt}\setlength{\LTpost}{4pt}
\setlength{\emergencystretch}{2em}
\onehalfspacing
\pagestyle{fancy}\fancyhf{}\fancyhead[R]{\fontsize{10}{12}\selectfont\thepage}
\renewcommand{\headrulewidth}{0pt}
\newcommand{\heading}[1]{\par\Needspace{4\baselineskip}\noindent\textbf{#1}\par\vspace{5pt}}
\newcommand{\captiontext}[1]{\par\begingroup\fontsize{10}{12}\selectfont%
\setstretch{1}\noindent #1\par\endgroup\vspace{3pt}}
\hypersetup{pdfauthor={Joey Alan de Freitas Solis; Paulo Henrico}}
\begin{document}
"""


def article():
    source = (ROOT / "docs/artigo-fonte.md").read_text()
    readable = (ROOT / "docs/artigo.md").read_text()
    names = {
        "Quadro 1": "configuracoes",
        "Tabela 1": "variantes",
        "Tabela 2": "iniciais",
        "Tabela 3": "teste",
    }
    tables = {}
    blocks = re.split(r"\n\s*\n", readable)
    for i, block in enumerate(blocks):
        for title, name in names.items():
            if block.startswith(title + " -"):
                tables[name] = rows_from_markdown(blocks[i + 1])
    assert len(tables) == 4
    tex = [PREAMBLE]
    for page_no, page in enumerate(source.split("<!-- pagina -->"), 1):
        if page_no > 1:
            tex.append(r"\clearpage")
        abstract = False
        if page_no == 8:
            tex.append(r"\begingroup\setlength{\parskip}{0pt}")
        for block in re.split(r"\n\s*\n", page.strip()):
            if block.startswith("# "):
                tex.append(r"\begin{center}\textbf{" + inline(block[2:]) + r"}\end{center}")
            elif block.startswith("@autores"):
                for line in block.splitlines():
                    tag, value = line.split(" ", 1)
                    tex.append(
                        r"\begingroup\singlespacing\centering " + inline(value) + r"\par\endgroup"
                    )
            elif block.startswith("##"):
                title = block.lstrip("# ")
                abstract = title == "Resumo"
                tex.append(
                    r"\begin{center}\textbf{" + inline(title) + r"}\end{center}"
                    if title in ("Resumo", "Referências")
                    else r"\heading{" + inline(title) + "}"
                )
            elif block.startswith("@figura"):
                stem, title, height = block[len("@figura ") :].split(" | ")
                if page_no == 8:
                    height = "2.6"
                shutil.copyfile(CP6 / "figuras" / f"{stem}.png", OUT / "figuras" / f"{stem}.png")
                tex.extend(
                    [
                        r"\captiontext{" + inline(title) + "}",
                        r"\noindent\includegraphics[width=\linewidth,height="
                        + height
                        + r"in,keepaspectratio]{figuras/"
                        + stem
                        + r".png}\par",
                    ]
                )
            elif block.startswith(("@tabela", "@quadro")):
                name, title = block.split(" ", 1)[1].split(" | ")
                tex.extend([r"\captiontext{" + inline(title) + "}", table(tables[name], name)])
            elif block.startswith("@fonte"):
                tex.append(r"\captiontext{" + inline(block[7:]) + "}")
            elif block.startswith("@palavras"):
                tex.append(
                    r"\begingroup\singlespacing\noindent " + inline(block[10:]) + r"\par\endgroup"
                )
                abstract = False
            else:
                if page_no == 8 and block.startswith("A Figura 6 mostra"):
                    block = (
                        "Na Figura 6, as previsões ocupam faixa mais estreita que as notas "
                        "observadas. Os resíduos incluem notas zero com erros negativos. "
                        "Os extremos são aproximados de valores intermediários, apesar "
                        "do RMSE global semelhante na validação e no teste."
                    )
                value = inline(block)
                if abstract or page_no == 10:
                    tex.append(
                        r"\begingroup\singlespacing\noindent "
                        + value
                        + r"\par\endgroup\vspace{6pt}"
                    )
                else:
                    tex.append(value + "\n\n")
        if page_no == 8:
            tex.append(r"\endgroup")
    tex.append(r"\end{document}")
    (OUT / "artigo.tex").write_text("\n".join(tex) + "\n")


def document(name):
    text = (ROOT / "docs" / f"{name}.md").read_text()
    tex = [PREAMBLE]
    for block in re.split(r"\n\s*\n", text.strip()):
        if block.startswith("# "):
            tex.append(r"\begin{center}\large\textbf{" + inline(block[2:]) + r"}\end{center}")
        elif block.startswith("## "):
            if name == "pitch" and block.startswith("## Números para consulta"):
                tex.append(r"\Needspace{14\baselineskip}")
            tex.append(r"\heading{" + inline(block[3:]) + "}")
        elif block.startswith("|"):
            tex.append(table(rows_from_markdown(block), long=True))
        else:
            tex.append(inline(block) + "\n\n")
    tex.append(r"\end{document}")
    (OUT / f"{name}.tex").write_text("\n".join(tex) + "\n")


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "figuras").mkdir(exist_ok=True)
    article()
    document("pitch")
    document("acompanhamento")
    (OUT / "main.tex").write_text(
        "% Documento principal padrão do pacote: roteiro do pitch.\n\\input{pitch.tex}\n"
    )
    sources = ["docs/artigo-fonte.md", "docs/artigo.md", "docs/pitch.md", "docs/acompanhamento.md"]
    files = sorted(p for p in OUT.rglob("*") if p.is_file() and p.suffix in (".tex", ".png"))
    manifest = {
        "source_documents": {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources
        },
        "assets": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files
        },
        "scientific_results_changed": False,
        "default_main": "main.tex",
        "compiler": "XeLaTeX (Overleaf); Tectonic 0.17.0 (verificação local)",
        "portable_font": "Times equivalente via mathptmx, sem fontes externas proprietárias",
    }
    (CP7 / "fontes_latex.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print("Fontes LaTeX geradas: artigo, pitch e acompanhamento.")


if __name__ == "__main__":
    main()
