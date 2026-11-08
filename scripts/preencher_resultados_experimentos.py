"""Consolidar somente resultados reais de execuções completas, sem sobrescrever saídas."""

import argparse
import json
from pathlib import Path

from enem_base.exports import export_experiments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--final", type=Path)
    args = parser.parse_args()
    try:
        print(
            json.dumps(export_experiments(args.runs, args.output, args.final), ensure_ascii=False)
        )
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"Erro: {error}\n")


if __name__ == "__main__":
    main()
