"""Análise exploratória exclusivamente dos participantes do desenvolvimento."""

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from enem_base.provenance import write_json
from enem_base.study import StudyConfig, load_development


def _save(fig, destination: Path, *, synthetic: bool = False) -> None:
    fig.text(
        0.015,
        0.015,
        (
            "DADOS FICTÍCIOS - teste técnico; sem interpretação sobre o ENEM."
            if synthetic
            else "Fonte: Inep, ENEM 2023. Somente desenvolvimento; teste reservado."
        ),
        fontsize=9,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(destination, dpi=160)
    plt.close(fig)


def plot_development_missing(report: dict, destination: Path, *, synthetic: bool = False) -> None:
    all_missing = pd.Series(report["missing"])
    missing = all_missing[all_missing.gt(0)].sort_values().tail(20)
    fig, ax = plt.subplots(figsize=(11, max(4, len(missing) * 0.45 + 2)))
    percentages = 100 * missing.values / report["rows"]
    if len(missing):
        bars = ax.barh(missing.index, percentages, color="#216477")
        ax.bar_label(
            bars, labels=[f"{value:.2f}%".replace(".", ",") for value in percentages], padding=5
        )
        ax.set_xlim(0, max(percentages) * 1.14)
    else:
        ax.text(
            0.5,
            0.5,
            "Nenhuma ausência nas features candidatas",
            transform=ax.transAxes,
            ha="center",
        )
    ax.set(
        title=(
            "Features com células ausentes no desenvolvimento\n"
            f"Demais features sem células ausentes: {int(all_missing.eq(0).sum())}"
        ),
        xlabel="Ausência (%)",
    )
    _save(fig, destination, synthetic=synthetic)


def explore_development(config: StudyConfig, output: Path) -> dict:
    if output.exists():
        raise FileExistsError("A análise já existe; escolha um novo diretório de saída.")
    frame, provenance = load_development(config)
    target = frame[config.target].astype(float)
    report = {
        **provenance,
        "evaluated_set": "development",
        "rows": len(frame),
        "zeros": int(target.eq(0).sum()),
        "target_summary": {
            str(k): float(v)
            for k, v in target.describe(
                percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
            ).items()
        },
        "missing": {name: int(frame[name].isna().sum()) for name in config.features},
        "types": {name: str(frame[name].dtype) for name in config.features},
        "categories": {
            name: {
                str(k): int(v) for k, v in frame[name].fillna("__MISSING__").value_counts().items()
            }
            for name in config.categorical
        },
    }
    output.mkdir(parents=True)
    write_json(output / "diagnostico_desenvolvimento.json", report)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(target, bins=45, color="#216477", edgecolor="white")
    ax.set(
        title=f"Ciências da Natureza - distribuição no desenvolvimento (n={len(frame):,})",
        xlabel="Nota observada de Ciências da Natureza",
        ylabel="Participantes",
    )
    ax.text(
        0.98, 0.95, f"Notas zero: {report['zeros']:,}", transform=ax.transAxes, ha="right", va="top"
    )
    _save(fig, output / "distribuicao_nota_cn.png", synthetic=config.kind == "synthetic")
    plot_development_missing(
        report, output / "ausencias_features.png", synthetic=config.kind == "synthetic"
    )
    group = (
        frame.assign(nota=target)
        .groupby("TP_ESCOLA", dropna=False)
        .nota.agg(["count", "mean", "median", "std"])
        .reset_index()
    )
    group["TP_ESCOLA"] = group.TP_ESCOLA.fillna("__MISSING__")
    school_labels = {"1": "Não respondeu", "2": "Pública", "3": "Privada", "__MISSING__": "Ausente"}
    group["tipo_escola"] = group.TP_ESCOLA.map(school_labels).fillna(group.TP_ESCOLA)
    group.to_csv(output / "nota_por_tipo_escola.csv", index=False, lineterminator="\n")
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(group))
    ax.bar(x, group["mean"], color="#216477")
    ax.set_xticks(x, group.tipo_escola)
    ax.set(
        title="Nota média por código de tipo de escola - desenvolvimento",
        xlabel="Tipo de escola do Ensino Médio (dicionário do Inep, 2023)",
        ylabel="Nota média",
    )
    for index, row in group.iterrows():
        ax.text(index, row["mean"] + 5, f"n={int(row['count']):,}", ha="center", fontsize=9)
    ax.set_ylim(0, max(group["mean"]) * 1.18)
    _save(fig, output / "nota_por_tipo_escola.png", synthetic=config.kind == "synthetic")
    return report


def plot_cv_summary(summary: pd.DataFrame, destination: Path, *, synthetic: bool = False) -> None:
    ordered = summary.sort_values("rmse_mean")
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    labels = ordered.model.tolist()
    names = {"baseline": "Média", "linear": "Linear", "ridge": "Ridge", "arvore": "Árvore"}
    for ax, metric, title in zip(axes, ("rmse", "mae", "r2"), ("RMSE", "MAE", "R²"), strict=True):
        ax.barh(
            [names.get(name, name) for name in labels],
            ordered[metric + "_mean"],
            xerr=ordered[metric + "_std"],
            color="#216477",
            capsize=4,
        )
        ax.set_title(title + " - média ± desvio (3 dobras)", fontsize=11)
        ax.set_xlabel("Pontos da nota" if metric != "r2" else "R²")
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Ciências da Natureza - comparação inicial no desenvolvimento", fontsize=15)
    _save(fig, destination, synthetic=synthetic)
