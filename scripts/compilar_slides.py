"""Compilar PDFs da entrega a partir do LaTeX e montar o pacote independente do Overleaf."""

import argparse
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tectonic", default="tectonic")
    args = parser.parse_args()
    engine = shutil.which(args.tectonic)
    if engine is None:
        parser.error("Informe o executável Tectonic com --tectonic ou compile no Overleaf.")
    build = ROOT / "tmp/slides-build"
    output = ROOT / "output/pdf"
    build.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    # A apresentação final é exportada do Canva; compilar somente o acompanhamento.
    documents = [("slides_acompanhamento", "acompanhamento")]
    for source, _ in documents:
        result = subprocess.run(
            [engine, "--keep-logs", "--outdir", str(build), f"{source}.tex"],
            cwd=ROOT / "relatorio",
            capture_output=True,
            text=True,
        )
        (build / f"{source}.console.txt").write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f"Falha na compilação: {build / (source + '.console.txt')}")
        log = (build / f"{source}.log").read_text(errors="replace")
        if "Overfull \\" in log or "Missing character:" in log:
            raise ValueError(f"Revisar composição: {build / (source + '.log')}")
    for source, name in documents:
        shutil.copyfile(build / f"{source}.pdf", output / f"{source}.pdf")
        shutil.copyfile(build / f"{source}.pdf", ROOT / "docs" / f"{name}.pdf")
        print(f"Publicado: docs/{name}.pdf")
    with zipfile.ZipFile(
        ROOT / "output/overleaf-enem2023.zip", "w", compression=zipfile.ZIP_DEFLATED
    ) as package:
        for path in sorted((ROOT / "relatorio").rglob("*")):
            if path.is_file() and path.suffix in {".tex", ".md", ".png"}:
                package.write(path, str(path.relative_to(ROOT / "relatorio")))
    print("Pacote independente: output/overleaf-enem2023.zip")


if __name__ == "__main__":
    main()
