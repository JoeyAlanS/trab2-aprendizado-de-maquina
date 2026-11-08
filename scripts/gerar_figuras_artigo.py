"""Gerar figuras somente a partir de dados e métricas persistidos e verificados."""

import argparse
import json
from pathlib import Path

from enem_base.exports import generate_figures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dashboard", type=Path, required=True)
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--search", type=Path)
    parser.add_argument("--curve", type=Path)
    parser.add_argument("--final", type=Path)
    args = parser.parse_args()
    try:
        result = generate_figures(
            args.dashboard,
            args.runs,
            args.output,
            search=args.search,
            curve=args.curve,
            final=args.final,
        )
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"Erro: {error}\n")


if __name__ == "__main__":
    main()
