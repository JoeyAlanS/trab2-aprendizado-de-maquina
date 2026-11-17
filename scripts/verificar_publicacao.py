"""Conferir a entrega de um clone sem microdados, treinamento ou novas previsões."""

import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from enem_base.dashboard import load_dashboard
from enem_base.dashboard_results import load_model_results
from enem_base.provenance import verify_sha256
from enem_base.relations import load_relations

ROOT = Path(__file__).resolve().parents[1]


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.sources.extend(value for key, value in attrs if key == "src" and value)


def main():
    required = [
        "README.md",
        "requirements.txt",
        ".gitignore",
        "dados/raw/README.md",
        "dados/processed/README.md",
        "dados/splits/README.md",
        "notebooks/01_analise_resultados.py",
        "resultados/experimentos.csv",
        "resultados/colunas.csv",
        "resultados/comparacao_modelos.csv",
        "app/app.py",
        "app/requirements.txt",
    ]
    for name in required:
        if not (ROOT / name).is_file():
            raise ValueError(f"Arquivo da entrega ausente: {name}")
    for name in ("acompanhamento", "artigo", "apresentacao_canva"):
        path = ROOT / "docs" / f"{name}.pdf"
        with path.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                raise ValueError(f"PDF inválido: {path.relative_to(ROOT)}")

    data = load_dashboard(ROOT / "resultados/ciencias_natureza/dashboard-v1")
    load_relations(ROOT / "resultados/ciencias_natureza/relacoes-v1", data.manifest)
    results = load_model_results(ROOT / "resultados", data.manifest)
    print(f"Catálogo: {len(results.cv)} configurações; 33 dobras iniciais; cinco testes finais.")

    manifest = json.loads((ROOT / "resultados/manifesto_entrega.json").read_text(encoding="utf-8"))
    local = set(manifest["large_local_files"])
    verified = 0
    for name, digest in manifest["outputs"].items():
        path = ROOT / name
        if name in local and not path.exists():
            print(f"Arquivo individual local omitido neste clone: {name}")
            continue
        verify_sha256(path, digest, "Publicação diferente da entrega selada")
        verified += 1
    print(f"Integridade: {verified} produtos conferidos, sem alterar resultados.")

    for source in ("slides_acompanhamento.tex", "artigo.tex"):
        content = (ROOT / "relatorio" / source).read_text(encoding="utf-8")
        images = re.findall(r"\\(?:includegraphics(?:\[[^\]]*\])?|figura)\{([^}]+)\}", content)
        for image in images:
            if not any(
                (ROOT / "relatorio" / prefix / image).is_file() for prefix in ("", "figuras")
            ):
                raise ValueError(f"Figura ausente em {source}: {image}")
    for name in ("apresentacao/index.html", "output/apresentacao/ENEM_2023_Design_Final.html"):
        path = ROOT / name
        parser = Images()
        parser.feed(path.read_text(encoding="utf-8"))
        for source in parser.sources:
            url = urlsplit(source)
            if not url.scheme and not url.netloc and url.path:
                if not (path.parent / unquote(url.path)).is_file():
                    raise ValueError(f"Imagem local ausente em {name}: {source}")
    for name in ("overleaf-enem2023.zip",):
        with zipfile.ZipFile(ROOT / "output" / name) as package:
            if package.testzip() is not None:
                raise ValueError(f"Pacote corrompido: {name}")
            for source in (
                "main.tex",
                "slides_acompanhamento.tex",
                "artigo.tex",
            ):
                if package.read(source) != (ROOT / "relatorio" / source).read_bytes():
                    raise ValueError(f"Fonte desatualizada no pacote {name}: {source}")
    print("Documentos: PDFs presentes; apresentação do Canva; imagens e pacote Overleaf íntegros.")
    print("Publicação conferida. Esta verificação não publica o aplicativo no Streamlit.")


if __name__ == "__main__":
    main()
