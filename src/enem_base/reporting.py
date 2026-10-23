"""Figuras e tabelas LaTeX geradas dos agregados verificáveis, sem novos ajustes."""

from pathlib import Path
from textwrap import fill

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from enem_base.dashboard import DashboardData, load_dashboard
from enem_base.provenance import write_json
from enem_base.relations import LABELS, RelationData, load_relations, pair_cells

TEAL, NAVY, GOLD = "#087f8c", "#2b5278", "#db9642"


def tex(value: object) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "_": r"\_",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
    }
    return "".join(replacements.get(char, char) for char in str(value))


def br(value: float | int, decimals: int = 0) -> str:
    return f"{value:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _save(fig, path: Path) -> None:
    fig.savefig(path, dpi=210, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _profile(data: RelationData, name: str, *, missing: bool = False) -> pd.DataFrame:
    rows = data.profiles.loc[data.profiles.variable.eq(name)].copy()
    if not missing:
        rows = rows.loc[rows.code.ne("__MISSING__")]
    rows["order"] = rows.code.map(lambda code: f"{int(code):03}" if code.isdecimal() else code)
    return rows.sort_values("order")


def _bars(ax, rows: pd.DataFrame, title: str, *, full_labels: bool = False) -> None:
    labels = [fill(str(label), 9) for label in (rows.label if full_labels else rows.code)]
    ax.bar(np.arange(len(rows)), rows["mean"], color=TEAL, width=0.7)
    ax.set_xticks(np.arange(len(rows)), labels)
    ax.set(title=title, ylabel="Nota média CN", ylim=(0, max(650, rows["mean"].max() * 1.1)))
    ax.tick_params(axis="x", labelsize=8)
    if full_labels:
        ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.16)


def create_figures(data: RelationData, dashboard: DashboardData, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "figure.constrained_layout.use": True,
        }
    )
    # Distribuição: contagens completas, sem amostra visual de participantes.
    counts = dashboard.cube.groupby("score_bin")["count"].sum()
    fig, ax = plt.subplots(figsize=(6.3, 2.1))
    ax.bar(counts.index * 25 + 12.5, counts, width=23, color=TEAL)
    ax.axvline(dashboard.eda["target_summary"]["mean"], color=NAVY, linestyle="--")
    ax.set(
        xlabel="Nota de Ciências da Natureza",
        ylabel="Participantes",
        title="Distribuição no desenvolvimento (intervalos de 25 pontos)",
    )
    ax.text(
        0.99,
        0.95,
        f"n = {br(dashboard.eda['rows'])}\nZeros = {br(dashboard.eda['zeros'])}",
        transform=ax.transAxes,
        ha="right",
        va="top",
    )
    _save(fig, directory / "distribuicao.png")

    fig, axes = plt.subplots(2, 2, figsize=(6.3, 4.0))
    for ax, name, title in zip(
        axes.flat,
        ["Q006", "Q001", "Q024", "Q025"],
        [
            "Renda familiar (Q006)",
            "Escolaridade do pai (Q001)",
            "Computadores em casa (Q024)",
            "Internet em casa (Q025)",
        ],
        strict=True,
    ):
        _bars(ax, _profile(data, name), title)
        ax.set_xlabel("Alternativa do questionário de 2023")
    _save(fig, directory / "socioeconomico.png")

    fig, axes = plt.subplots(2, 2, figsize=(6.3, 3.8))
    for ax, name, title in zip(
        axes.flat[:3],
        ["TP_ESCOLA", "TP_DEPENDENCIA_ADM_ESC", "TP_LOCALIZACAO_ESC"],
        [
            "Tipo de escola (TP_ESCOLA)",
            "Dependência administrativa (observados)",
            "Localização da escola (observados)",
        ],
        strict=True,
    ):
        _bars(ax, _profile(data, name), title, full_labels=True)
    missing = data.target.loc[data.target.missing.gt(0)].sort_values("missing")
    axes[1, 1].barh(missing.variable, missing.missing / missing.n * 100, color=GOLD)
    axes[1, 1].set(xlabel="Ausência (%)", xlim=(0, 100), title="Cobertura das variáveis escolares")
    axes[1, 1].tick_params(axis="y", labelsize=8)
    _save(fig, directory / "escola.png")

    cells = pair_cells(data, "TP_ESCOLA", "Q006")
    matrix = cells.pivot(index="code_a", columns="code_b", values="mean").sort_index(axis=1)
    n = cells.pivot(index="code_a", columns="code_b", values="n").reindex_like(matrix)
    matrix = matrix.where(n >= 30)
    fig, ax = plt.subplots(figsize=(6.3, 1.9))
    image = ax.imshow(matrix, cmap="YlGnBu", aspect="auto", vmin=400, vmax=650)
    ax.set_xticks(range(len(matrix.columns)), matrix.columns)
    ax.set_yticks(range(len(matrix)), ["Não respondeu", "Pública", "Privada"])
    for i in range(len(matrix)):
        for j in range(len(matrix.columns)):
            value = matrix.iloc[i, j]
            if pd.notna(value):
                ax.text(
                    j,
                    i,
                    f"{value:.0f}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white" if value > 550 else "#142b40",
                )
    ax.set(
        xlabel="Renda familiar: alternativas A a Q",
        title="Nota média no cruzamento escola × renda (n por célula ≥ 30)",
    )
    fig.colorbar(image, ax=ax, label="Nota média CN", shrink=0.9)
    _save(fig, directory / "escola_renda.png")

    fig, axes = plt.subplots(2, 2, figsize=(6.3, 3.2))
    for ax, name, title in zip(
        axes.flat,
        ["TP_FAIXA_ETARIA", "TP_SEXO", "TP_COR_RACA", "IN_TREINEIRO"],
        [
            "Faixa etária (códigos oficiais)",
            "Sexo informado",
            "Cor/raça (códigos oficiais)",
            "Condição de treineiro",
        ],
        strict=True,
    ):
        _bars(ax, _profile(data, name), title, full_labels=name in ("TP_SEXO", "IN_TREINEIRO"))
        if name == "TP_FAIXA_ETARIA":
            age = _profile(data, name)
            ax.set_xticks(np.arange(0, len(age), 3), age.code.iloc[::3])
    _save(fig, directory / "demografia.png")

    ufs = _profile(data, "SG_UF_PROVA").sort_values("mean")
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 3.5))
    for ax, section in zip(axes, [ufs.iloc[:14], ufs.iloc[14:]], strict=True):
        ax.barh(np.arange(len(section)), section["mean"], color=TEAL)
        ax.set_yticks(
            np.arange(len(section)),
            [f"{row.code} | n={br(row.n)}" for row in section.itertuples()],
            fontsize=8,
        )
        ax.set(xlabel="Nota média CN", xlim=(0, 700))
        ax.tick_params(axis="x", labelsize=8)
        for y, row in enumerate(section.itertuples()):
            ax.text(row.mean + 4, y, f"{row.mean:.1f}", va="center", fontsize=8)
    _save(fig, directory / "ufs.png")

    names = [
        "Q006",
        "Q001",
        "Q002",
        "Q003",
        "Q004",
        "TP_ESCOLA",
        "TP_ST_CONCLUSAO",
        "TP_COR_RACA",
        "Q008",
        "Q010",
        "Q024",
        "Q025",
    ]
    matrix = pd.DataFrame(np.nan, index=names, columns=names)
    for row in data.pairs.loc[data.pairs.metric.eq("cramers_v")].itertuples():
        if row.variable_a in names and row.variable_b in names:
            matrix.loc[row.variable_a, row.variable_b] = row.value
            matrix.loc[row.variable_b, row.variable_a] = row.value
    fig, ax = plt.subplots(figsize=(6.3, 3.5))
    image = ax.imshow(matrix, vmin=0, vmax=1, cmap="YlGnBu")
    ax.set_xticks(range(len(names)), names, rotation=40, ha="right", fontsize=9)
    ax.set_yticks(range(len(names)), names, fontsize=9)
    ax.set_title("V de Cramér: seleção ilustrativa de 12 entradas categóricas")
    fig.colorbar(image, ax=ax, label="Associação (sem direção)", shrink=0.85)
    _save(fig, directory / "associacoes.png")

    cv = dashboard.cv.sort_values("rmse_mean")
    fig, axes = plt.subplots(1, 3, figsize=(6.3, 2.4))
    model_names = {"ridge": "Ridge", "linear": "Linear", "arvore": "Árvore", "baseline": "Média"}
    for ax, metric, title in zip(axes, ("rmse", "mae", "r2"), ("RMSE", "MAE", "R²"), strict=True):
        ax.barh(
            cv.model.map(model_names),
            cv[f"{metric}_mean"],
            xerr=cv[f"{metric}_std"],
            color=TEAL,
            capsize=3,
        )
        ax.set(title=title + " (média ± DP)", xlabel="Pontos" if metric != "r2" else "Coeficiente")
    _save(fig, directory / "modelos.png")


def create_tables(data: RelationData, dashboard: DashboardData, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    header = (
        r"\begin{tabularx}{\linewidth}{@{}Xrrr@{}}\toprule "
        r"Variável & $\eta^2$ & $n$ observado & Ausência\ (\%)\\\midrule" + "\n"
    )
    lines = []
    for row in data.target.sort_values("eta_squared", ascending=False).itertuples():
        label = LABELS.get(row.variable, row.variable)
        lines.append(
            f"{tex(label)} & {br(row.eta_squared, 4)} & {br(row.n_observed)} "
            f"& {br(row.missing / row.n * 100, 2)} " + r"\\"
        )
    (directory / "todas_entradas.tex").write_text(
        header + "\n".join(lines) + r"\bottomrule\end{tabularx}", encoding="utf-8"
    )
    pairs = (
        data.pairs.loc[data.pairs.metric.eq("cramers_v")]
        .sort_values("value", ascending=False)
        .head(7)
    )
    header = (
        r"\begin{tabularx}{\linewidth}{@{}XXrr@{}}\toprule "
        r"Entrada A & Entrada B & $V$ & $n$ observado\\\midrule" + "\n"
    )
    lines = [
        f"{tex(LABELS[row.variable_a])} & {tex(LABELS[row.variable_b])} "
        f"& {br(row.value, 3)} & {br(row.n_observed)} " + r"\\"
        for row in pairs.itertuples()
    ]
    (directory / "pares.tex").write_text(
        header + "\n".join(lines) + r"\bottomrule\end{tabularx}", encoding="utf-8"
    )
    header = (
        r"\begin{tabularx}{\linewidth}{@{}Xrrrr@{}}\toprule "
        r"Modelo & RMSE $\pm$ DP & MAE $\pm$ DP & $R^2$ $\pm$ DP & Tempo (s)\\\midrule" + "\n"
    )
    names = {"baseline": "Média", "linear": "Linear", "ridge": "Ridge", "arvore": "Árvore"}
    lines = [
        f"{names[row.model]} & {br(row.rmse_mean, 2)} $\\pm$ {br(row.rmse_std, 2)} "
        f"& {br(row.mae_mean, 2)} $\\pm$ {br(row.mae_std, 2)} "
        f"& {br(row.r2_mean, 4)} $\\pm$ {br(row.r2_std, 4)} "
        f"& {br(row.elapsed_seconds, 2)} " + r"\\"
        for row in dashboard.cv.sort_values("rmse_mean").itertuples()
    ]
    (directory / "modelos.tex").write_text(
        header + "\n".join(lines) + r"\bottomrule\end{tabularx}", encoding="utf-8"
    )
    profiles = data.profiles.set_index(["variable", "code"])

    def mean(name, code):
        return float(profiles.loc[(name, code), "mean"])

    q005 = data.target.set_index("variable").loc["Q005"]
    macros = {
        "RendaA": mean("Q006", "A"),
        "RendaQ": mean("Q006", "Q"),
        "DiferencaRenda": mean("Q006", "Q") - mean("Q006", "A"),
        "InternetNao": mean("Q025", "A"),
        "InternetSim": mean("Q025", "B"),
        "ComputadorNao": mean("Q024", "A"),
        "ComputadorQuatro": mean("Q024", "E"),
        "EscolaPublica": mean("TP_ESCOLA", "2"),
        "EscolaPrivada": mean("TP_ESCOLA", "3"),
        "DiferencaEscola": mean("TP_ESCOLA", "3") - mean("TP_ESCOLA", "2"),
        "PearsonPessoas": q005.pearson,
        "SpearmanPessoas": q005.spearman,
    }
    macro_lines = []
    for key, value in macros.items():
        decimals = 4 if key in ("PearsonPessoas", "SpearmanPessoas") else 2
        macro_lines.append(f"\\newcommand{{\\{key}}}{{{br(value, decimals)}}}")
    (directory / "valores.tex").write_text("\n".join(macro_lines) + "\n", encoding="utf-8")


def prepare_report(relations_dir: Path, dashboard_dir: Path, project: Path) -> dict:
    dashboard = load_dashboard(dashboard_dir)
    data = load_relations(relations_dir, dashboard.manifest)
    create_figures(data, dashboard, project / "images")
    create_tables(data, dashboard, project / "tables")
    report = {
        "source_sha256": data.manifest["source_sha256"],
        "splits_sha256": data.manifest["splits_sha256"],
        "test_evaluated": False,
        "n_development": data.manifest["n_development"],
        "n_variables": data.manifest["n_variables"],
        "n_pairs": data.manifest["n_pairs"],
        "note": (
            "TeX and figures generated from verified aggregate snapshots; "
            "compile main.tex separately"
        ),
    }
    write_json(project / "dados_relatorio.json", report)
    return report
