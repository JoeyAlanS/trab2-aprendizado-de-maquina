"""Selecionar os três melhores entre os sete algoritmos validados no Checkpoint 1."""

import argparse
import json
from pathlib import Path

from enem_base.selection import select_checkpoint2
from enem_base.study import load_study


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--checkpoint1", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--references", type=Path, help="Rodada original das quatro referências")
    args = parser.parse_args()
    result = select_checkpoint2(
        load_study(args.study), args.checkpoint1, args.output, references=args.references
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "selected_models": result["selected_models"],
                "output": str(args.output),
                "test_evaluated": result["test_evaluated"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
