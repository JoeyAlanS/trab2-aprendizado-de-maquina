"""Executar somente o checkpoint 1, preservando rodadas concluídas e falhas."""

import argparse
import gc
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

from enem_base.evidence import comparison_rows
from enem_base.modeling import estimator_spec, model_catalog
from enem_base.provenance import runtime_metadata, sha256_file, write_json
from enem_base.study import load_study
from enem_base.workflow import current_provenance

MODELS = ("svm", "bagging", "pasting", "random_forest", "boosting", "stacking", "knn")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    config = load_study(args.study)
    provenance = current_provenance(config)
    args.output.mkdir(parents=True, exist_ok=True)
    status_path = args.output / "execucao.json"
    if status_path.exists() and args.resume:
        previous = json.loads(status_path.read_text(encoding="utf-8"))
        history = args.output / "execucoes_anteriores"
        write_json(history / f"execucao-{len(list(history.glob('*.json'))) + 1:03d}.json", previous)
    status = {
        **runtime_metadata(),
        **provenance,
        "checkpoint": 1,
        "status": "running",
        "requested_models": args.models,
        "completed": [],
        "next_checkpoint_started": False,
    }
    write_json(status_path, status)
    try:
        for name in args.models:
            output = args.output / name
            expected = estimator_spec(model_catalog(config)[name])
            complete = False
            if output.exists():
                from enem_base.checkpointing import run_lock

                while True:
                    try:
                        with run_lock(output):
                            break
                    except ValueError:
                        logging.info("%s está ativo em outro processo; aguardando conclusão", name)
                        time.sleep(10)
                existing = json.loads((output / "manifesto.json").read_text(encoding="utf-8"))
                complete = existing.get("status") == "completed"
                if not complete and not args.resume:
                    raise ValueError(f"Comparação parcial: use --resume para retomar {output}")
            if complete:
                _, manifest = comparison_rows(output, provenance)
                if manifest["models"] != [name] or manifest["parameters"][name] != expected:
                    raise ValueError(f"Configuração da rodada existente incompatível: {output}")
                logging.info("%s já concluído e verificado; preservando execução", name)
            else:
                logging.info("Iniciando %s com toda a população de desenvolvimento", name)
                # Processo próprio libera a memória e captura o código vigente de cada rodada.
                log_path = args.output / f"{name}.log"
                with log_path.open("a" if args.resume else "x", encoding="utf-8") as stream:
                    if args.resume:
                        stream.write(
                            "\nRetomada explícita: preservar dobras e blocos verificados.\n"
                        )
                        stream.flush()
                    subprocess.run(
                        [
                            sys.executable,
                            "-u",
                            "-m",
                            "enem_base",
                            "--verbose",
                            "compare",
                            "--study",
                            str(args.study),
                            "--models",
                            name,
                            "--output",
                            str(output),
                            *(["--resume"] if args.resume else []),
                        ],
                        stdout=stream,
                        stderr=subprocess.STDOUT,
                        check=True,
                    )
                comparison_rows(output, provenance)
            status["completed"].append(
                {"model": name, "manifest_sha256": sha256_file(output / "manifesto.json")}
            )
            write_json(status_path, status)
            gc.collect()
        status["status"] = "completed"
    except Exception as error:
        status.update(status="failed", failure_type=type(error).__name__, message=str(error))
        write_json(status_path, status)
        raise
    write_json(status_path, status)
    print(json.dumps(status, ensure_ascii=False))


if __name__ == "__main__":
    main()
