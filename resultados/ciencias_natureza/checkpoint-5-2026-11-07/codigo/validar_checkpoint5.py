"""Conferir a coleção visual com seus arquivos reais, sem treinar modelos."""

import argparse
import json
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from enem_base.provenance import sha256_file, verify_sha256, write_json


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.articles = 0
        self.images = 0
        self.filters = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.links.extend(attrs[k] for k in ("href", "src") if k in attrs)
        self.articles += tag == "article"
        self.images += tag == "img"
        if tag == "button":
            self.filters.append(attrs.get("data-filter"))


def validate(root):
    manifest = json.loads((root / "manifesto.json").read_text())
    if manifest["new_training"] or manifest["new_test_evaluation"]:
        raise ValueError("Esta coleção deve somente publicar resultados existentes")
    for path, digest in manifest["inputs"].items():
        verify_sha256(Path(path), digest, "Fonte científica alterada")
    for path, digest in manifest["assets"].items():
        verify_sha256(root / path, digest, "Artefato visual alterado")
    verify_sha256(
        Path("scripts/publicar_checkpoint5.py"),
        manifest["script_sha256"],
        "Gerador diferente do registrado",
    )
    catalog = json.loads((root / "catalogo.json").read_text())["figures"]
    if len(catalog) != 17 or len({f["id"] for f in catalog}) != 17:
        raise ValueError("Catálogo visual incompleto")
    figures = {}
    for figure in catalog:
        with Image.open(root / figure["png"]) as image:
            image.load()
            if min(image.info.get("dpi", (0, 0))) < 299:
                raise ValueError(f"Resolução insuficiente: {figure['png']}")
            figures[figure["id"]] = {
                "size": image.size,
                "dpi": image.info["dpi"],
                "png_sha256": sha256_file(root / figure["png"]),
                "svg_sha256": sha256_file(root / figure["svg"]),
            }
        svg = ET.parse(root / figure["svg"]).getroot()
        if not svg.tag.endswith("svg") or not svg.get("viewBox"):
            raise ValueError("SVG inválido")
        for table in figure["tables"]:
            if not (root / table).is_file():
                raise ValueError("Tabela de apoio ausente")
        if figure["origin"] != "Gerado de tabelas verificadas":
            for ext in ("png", "svg"):
                verify_sha256(
                    root / figure[ext],
                    sha256_file(Path(figure["origin"] + "." + ext)),
                    "Figura reaproveitada diferente da aprovada",
                )
    parser = Links()
    parser.feed((root / "index.html").read_text())
    if parser.articles != 17 or parser.images != 17:
        raise ValueError("Galeria incompleta")
    if parser.filters != ["Todos", "Desenvolvimento", "Teste"]:
        raise ValueError("Filtros de etapa ausentes")
    for target in parser.links:
        if "://" in target or not (root / target).is_file():
            raise ValueError(f"Link não local ou ausente: {target}")
    tables = root / "tabelas"
    hist = pd.read_csv(tables / "distribuicao_desenvolvimento.csv")
    if hist.n.sum() != 2153941 or hist.iloc[0].n != 13236:
        raise ValueError("Histograma inconsistente")
    pca = pd.read_csv(tables / "pca_variancia.csv")
    if len(pca.groupby(["model", "fold"])) != 6:
        raise ValueError("PCA incompleto")
    for _, group in pca.groupby(["model", "fold"]):
        if len(group) != 235 or not group.cumulative_variance.is_monotonic_increasing:
            raise ValueError("Curva PCA inconsistente")
        if group.iloc[44].cumulative_variance < 0.8 or group.iloc[43].cumulative_variance >= 0.8:
            raise ValueError("Número de componentes incorreto")
    cells = pd.read_csv(tables / "residuos_stacking_celulas.csv")
    if cells.n.sum() != 538486:
        raise ValueError("Resíduos não cobrem todos os participantes")
    test = pd.read_csv(tables / "comparacao_teste.csv")
    if len(test) != 5 or not test.n_evaluated.eq(538486).all():
        raise ValueError("Comparação final incompleta")
    if not np.isfinite(test[["rmse", "mae", "r2"]]).all().all():
        raise ValueError("Métricas não finitas")
    groups = pd.read_csv(tables / "erros_grupos.csv")
    if len(groups) != 260 or not groups.groupby(["model", "group"]).n.sum().eq(538486).all():
        raise ValueError("Grupos incompletos")
    curves = pd.read_csv(tables / "curvas_por_dobra.csv")
    if len(curves) != 45 or len(curves.groupby(["model", "fraction"])) != 15:
        raise ValueError("Curvas incompletas")
    comparisons = pd.read_csv(tables / "comparacoes_cv_completas.csv")
    if len(comparisons) != 18 or comparisons.test_evaluated.any():
        raise ValueError("Mistura entre CV e teste")
    validation = {
        "status": "passed",
        "figures": figures,
        "png_count": 17,
        "svg_count": 17,
        "table_count": len(list(tables.glob("*.csv"))),
        "html_local_links_checked": len(parser.links),
        "source_hashes_checked": len(manifest["inputs"]),
        "all_copied_figures_identical_to_approved_sources": True,
        "development_histogram_n": 2153941,
        "development_zero_scores": 13236,
        "test_residual_cells_n": 538486,
        "test_models": 5,
        "pca_curves": 6,
        "final_learning_curve_points": 45,
        "validation_and_test_separate": True,
        "new_training": False,
        "new_test_evaluation": False,
        "visual_validation_pending": manifest["visual_validation_pending"],
        "validator_sha256": sha256_file(Path(__file__)),
    }
    write_json(root / "validacao.json", validation)
    print(json.dumps({k: v for k, v in validation.items() if k != "figures"}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", type=Path, required=True)
    validate(parser.parse_args().collection)
