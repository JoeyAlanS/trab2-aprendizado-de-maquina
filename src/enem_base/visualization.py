"""Visualização técnica do relatório de qualidade, sem exploração do alvo."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def plot_missing(report_path: Path, destination: Path) -> Path:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("kind") != "synthetic":
        raise ValueError(
            "Nesta fase, gráficos globais só são gerados para dados fictícios. "
            "A exploração real deverá usar apenas desenvolvimento após definir o alvo."
        )
    if destination.exists():
        raise FileExistsError("A figura já existe; escolha outro destino.")
    pairs = sorted(report["missing"].items(), key=lambda item: item[1])[-20:]
    fig, ax = plt.subplots(figsize=(10, max(4, len(pairs) * 0.32)))
    ax.barh([p[0] for p in pairs], [p[1] for p in pairs], color="#216477")
    ax.set_xlabel("Células ausentes (contagem)")
    ax.set_title(f"DADOS FICTÍCIOS - diagnóstico técnico ({report['rows']} registros)", loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(
        0.02,
        0.015,
        "Fonte: exemplo sintético do projeto. Sem interpretação sobre o ENEM.",
        fontsize=9,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=150)
    plt.close(fig)
    return destination
