"""Compilar as fontes da entrega com Tectonic; não regenera nem sobrescreve o TEX."""

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = {"artigo": "artigo_latex", "acompanhamento": "acompanhamento"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tectonic", default="tectonic", help="Executável Tectonic 0.17.0 ou compatível"
    )
    parser.add_argument("--documents", nargs="+", choices=DOCUMENTS, default=list(DOCUMENTS))
    args = parser.parse_args()
    engine = shutil.which(args.tectonic)
    if engine is None:
        parser.error(
            "Tectonic não encontrado; informe --tectonic ou compile no Overleaf com XeLaTeX."
        )
    build = ROOT / "tmp/latex-build"
    output = ROOT / "output/pdf"
    build.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for stem in args.documents:
        destination = DOCUMENTS[stem]
        command = [engine, "--keep-logs", "--outdir", str(build), f"{stem}.tex"]
        result = subprocess.run(command, cwd=ROOT / "relatorio", text=True, capture_output=True)
        (build / f"{stem}.console.txt").write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f"Falha em {stem}; consultar {build / (stem + '.console.txt')}")
        log = (build / f"{stem}.log").read_text(errors="replace")
        if "Overfull \\" in log or "Missing character:" in log:
            raise ValueError(f"Revisar composição de {stem}: excesso de largura ou glifo ausente")
        path = output / f"{destination}.pdf"
        shutil.copyfile(build / f"{stem}.pdf", path)
        if stem == "artigo":
            shutil.copyfile(path, ROOT / "docs/artigo.pdf")
        records.append(
            {
                "source": f"relatorio/{stem}.tex",
                "output": str(path.relative_to(ROOT)),
                "exit_code": 0,
                "pdf_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "log_sha256": hashlib.sha256(log.encode()).hexdigest(),
                "overfull_boxes": 0,
                "missing_glyphs": 0,
            }
        )
        print(f"Compilado: {path.relative_to(ROOT)}")
    version = subprocess.check_output([engine, "--version"], text=True).strip()
    (build / "compilacao_latex.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "engine": version,
                "documents": records,
                "compiled_inside_overleaf": False,
                "visual_review_required": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
