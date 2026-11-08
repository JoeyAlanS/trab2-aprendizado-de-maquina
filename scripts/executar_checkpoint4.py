"""Concluir uma etapa explícita do Checkpoint 4, preservando as etapas anteriores."""

import argparse
import logging
from pathlib import Path

from enem_base.final_evaluation import evaluate_frozen, fit_final_models, validate_final_results
from enem_base.final_selection import freeze_recipes, load_frozen
from enem_base.frozen_curves import curve_model, validate_curves
from enem_base.study import load_study


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=["freeze", "curves", "fit", "test", "validate"], required=True
    )
    parser.add_argument("--models", nargs="+")
    parser.add_argument("--variants", nargs="+", type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    config = load_study(args.study)
    if args.stage == "freeze":
        if not args.variants:
            parser.error("O congelamento exige --variants com todas as comparações exigidas.")
        frozen = freeze_recipes(config, args.output, args.variants)
        for label, recipe in frozen["recipes"].items():
            logging.info(
                "Receita %s: %s %s; RMSE CV %.9f",
                label,
                recipe["model"],
                recipe["parameters"],
                recipe["rmse_mean"],
            )
        logging.info("Solução acadêmica: %s", frozen["academic_solution"])
    elif args.stage == "curves":
        frozen = load_frozen(config, args.output)
        for label in args.models or frozen["curve_models"]:
            curve_model(config, args.output, label)
    elif args.stage == "fit":
        fit_final_models(config, args.output, args.models)
    elif args.stage == "test":
        evaluate_frozen(config, args.output)
    else:
        validate_curves(config, args.output)
        validate_final_results(config, args.output)
        logging.info("Curvas e avaliação final verificadas.")


if __name__ == "__main__":
    main()
