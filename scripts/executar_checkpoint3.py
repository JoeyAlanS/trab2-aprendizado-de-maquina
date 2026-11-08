"""Preparar e executar as curvas nacionais; não inicia outros checkpoints."""

import argparse
import logging
from pathlib import Path

from enem_base.learning_curves import curve_model, prepare_curves
from enem_base.study import load_study


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--forest-jobs", type=int, default=2)
    parser.add_argument(
        "--models",
        nargs="+",
        choices=("svm", "random_forest", "stacking"),
        default=["svm", "random_forest", "stacking"],
    )
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    config = load_study(args.study)
    if args.prepare_only:
        prepare_curves(config, args.selection, args.output, args.forest_jobs)
        logging.info("Protocolo de 45 ajustes preparado e validado")
    else:
        if not (args.output / "protocolo.json").exists():
            parser.error("Prepare o protocolo com --prepare-only antes de executar os modelos.")
        for name in args.models:
            curve_model(config, args.selection, args.output, name, resume=args.resume)
            logging.info("%s: quinze pontos concluídos e persistidos", name)


if __name__ == "__main__":
    main()
