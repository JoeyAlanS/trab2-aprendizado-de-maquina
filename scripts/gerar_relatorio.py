"""Atualizar figuras e tabelas do LaTeX; a narrativa em relatorio/main.tex é preservada."""

import json
from pathlib import Path

from enem_base.reporting import prepare_report

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    print(
        json.dumps(
            prepare_report(
                ROOT / "resultados/ciencias_natureza/relacoes-v1",
                ROOT / "resultados/ciencias_natureza/dashboard-v1",
                ROOT / "relatorio",
            ),
            ensure_ascii=False,
        )
    )
