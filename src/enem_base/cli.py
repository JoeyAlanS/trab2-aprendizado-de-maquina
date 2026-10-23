"""Interface de linha de comando da fase de preparação."""

import argparse
import json
import logging
import subprocess
import sys
import zipfile
from pathlib import Path

from enem_base.acquisition import collect
from enem_base.config import load_config
from enem_base.ingestion import prepare
from enem_base.quality import DataQualityError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Projeto 2 - preparação e estudo de Ciências da Natureza."
    )
    parser.add_argument("--verbose", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("prepare", help="Validar CSV completo e gerar Parquet em lotes")
    ingest.add_argument("--config", type=Path, required=True)
    acquire = commands.add_parser(
        "collect", help="Copiar fonte local ou baixar URL HTTPS explícita"
    )
    acquire.add_argument("--source", required=True)
    acquire.add_argument("--destination", type=Path, required=True)
    acquire.add_argument("--sha256")
    acquire.add_argument("--max-bytes", type=int, default=8 * 1024**3)
    chart = commands.add_parser("plot-quality", help="Figura de qualidade de dados fictícios")
    chart.add_argument("--report", type=Path, required=True)
    chart.add_argument("--output", type=Path, required=True)
    official = commands.add_parser("fetch-enem", help="Obter e extrair o pacote oficial de 2023")
    official.add_argument("--raw", type=Path, default=Path("dados/raw"))
    split = commands.add_parser(
        "split", help="Reservar teste e persistir dobras para o alvo definido"
    )
    split.add_argument("--study", type=Path, required=True)
    dashboard = commands.add_parser(
        "dashboard-data", help="Gerar snapshot agregado do desenvolvimento para o frontend"
    )
    dashboard.add_argument("--study", type=Path, required=True)
    dashboard.add_argument("--output", type=Path, required=True)
    dashboard.add_argument("--eda", type=Path, required=True)
    dashboard.add_argument("--cv", type=Path, required=True)
    for command, help_text in (
        ("eda", "Explorar somente o desenvolvimento"),
        ("compare", "Comparar modelos no desenvolvimento, sem avaliar teste"),
    ):
        sub = commands.add_parser(command, help=help_text)
        sub.add_argument("--study", type=Path, required=True)
        sub.add_argument("--output", type=Path, required=True)
        if command == "compare":
            sub.add_argument(
                "--models", nargs="+", default=["baseline", "linear", "ridge", "arvore"]
            )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s: %(message)s"
    )
    try:
        if args.command == "prepare":
            result = prepare(load_config(args.config))
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "rows": result["rows"],
                        "synthetic": result["synthetic"],
                        "target": None,
                    },
                    ensure_ascii=False,
                )
            )
        elif args.command == "collect":
            print(
                json.dumps(
                    collect(args.source, args.destination, args.sha256, args.max_bytes),
                    ensure_ascii=False,
                )
            )
        elif args.command == "plot-quality":
            from enem_base.visualization import plot_missing

            print(plot_missing(args.report, args.output))
        elif args.command == "fetch-enem":
            from enem_base.official import obtain_official

            print(json.dumps(obtain_official(args.raw), ensure_ascii=False))
        else:
            from enem_base.study import create_study_splits, load_study

            study = load_study(args.study)
            if args.command == "split":
                result = create_study_splits(study)
            elif args.command == "dashboard-data":
                from enem_base.dashboard import build_dashboard

                result = build_dashboard(study, args.output, args.eda, args.cv)
            elif args.command == "eda":
                from enem_base.exploration import explore_development

                result = explore_development(study, args.output)
            else:
                from enem_base.modeling import compare_models

                result = compare_models(study, args.output, tuple(args.models))
            print(json.dumps(result, ensure_ascii=False))
    except DataQualityError as error:
        # Apenas contagens e nomes de colunas: não expor linhas de participantes.
        print(json.dumps(error.report, ensure_ascii=False), file=sys.stderr)
        return 2
    except (
        ValueError,
        OSError,
        TypeError,
        KeyError,
        subprocess.CalledProcessError,
        zipfile.BadZipFile,
    ) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2
    return 0
