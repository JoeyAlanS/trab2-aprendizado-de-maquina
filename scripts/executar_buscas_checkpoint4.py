"""Preparar ou retomar as buscas nacionais antes de abrir o teste final."""

import argparse
import logging
from pathlib import Path

from enem_base.study import load_study
from enem_base.tuning import MODELS, prepare_search, search_model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--checkpoint2", type=Path)
    parser.add_argument("--checkpoint3", type=Path)
    parser.add_argument("--references", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    config = load_study(args.study)
    if args.prepare_only:
        if not all((args.checkpoint2, args.checkpoint3, args.references)):
            parser.error("Preparação exige --checkpoint2, --checkpoint3 e --references.")
        prepare_search(config, args.checkpoint2, args.checkpoint3, args.references, args.output)
        logging.info("Protocolo: cinco buscas, 12 configurações por modelo, três dobras")
    else:
        for name in args.models:
            search_model(config, args.output, name, resume=args.resume)


if __name__ == "__main__":
    main()
