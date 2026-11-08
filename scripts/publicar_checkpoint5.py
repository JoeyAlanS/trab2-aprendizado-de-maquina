"""Organizar gráficos reais em uma coleção local; nunca ajustar ou avaliar modelos."""

import argparse
import html
import json
import shutil
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import FuncFormatter, MaxNLocator

from enem_base.provenance import runtime_metadata, sha256_file, verify_sha256, write_json

BASE = Path("resultados/ciencias_natureza")
CP4 = BASE / "checkpoint-4-2026-11-07"
LABELS = {
    "stacking": "Stacking",
    "svm": "SVM linear",
    "random_forest": "Random Forest",
    "knn": "KNN",
    "bagging": "Bagging",
    "pasting": "Pasting",
    "boosting": "Gradient Boosting",
    "baseline": "Baseline (média)",
    "linear": "Linear",
    "ridge": "Ridge",
    "arvore": "Árvore",
}
COLORS = {"stacking": "#087f8c", "svm": "#a65400", "random_forest": "#7b3a96"}
CV_NOTE = (
    "Fonte: Inep, ENEM 2023 · desenvolvimento, n=2.153.941 · média ± DP de três dobras (não IC)."
)


def pt(value, precision=3):
    return f"{value:,.{precision}f}".replace(",", "@ ").replace(".", ",").replace("@ ", ".")


class Collection:
    def __init__(self, output):
        self.output = output
        self.inputs = {}
        self.figures = []

    def source(self, path, expected=None):
        path = Path(path)
        if expected:
            verify_sha256(path, expected, "Fonte da coleção alterada")
        self.inputs[str(path)] = sha256_file(path)
        return path

    def manifest(self, directory):
        directory = Path(directory)
        data = json.loads(self.source(directory / "manifesto.json").read_text())
        if data["status"] != "completed":
            raise ValueError(f"Fonte incompleta: {directory}")
        for name, digest in data["assets"].items():
            self.source(directory / name, digest)
        return data

    def table(self, name, frame):
        frame.to_csv(self.output / "tabelas" / f"{name}.csv", index=False)
        return f"tabelas/{name}.csv"

    def register(self, stem, title, stage, caption, tables, origin):
        self.figures.append(
            dict(
                id=stem,
                title=title,
                stage=stage,
                caption=caption,
                tables=tables,
                origin=origin,
                png=f"figuras/{stem}.png",
                svg=f"figuras/{stem}.svg",
            )
        )

    def save(self, fig, stem, title, stage, caption, tables, note=CV_NOTE):
        fig.suptitle(title, fontsize=15)
        fig.get_layout_engine().set(rect=(0, 0.13, 1, 0.80))
        fig.text(0.01, 0.015, note, fontsize=8)
        for ext in ("png", "svg"):
            fig.savefig(self.output / "figuras" / f"{stem}.{ext}", dpi=300, bbox_inches="tight")
        plt.close(fig)
        self.register(stem, title, stage, caption, tables, "Gerado de tabelas verificadas")

    def copy(self, directory, name, stem, title, stage, caption, tables):
        for ext in ("png", "svg"):
            src = self.source(directory / f"{name}.{ext}")
            shutil.copy2(src, self.output / "figuras" / f"{stem}.{ext}")
        self.register(stem, title, stage, caption, tables, str(directory / name))


def comparisons(c, seven, selected, summaries):
    table = c.table("comparacao_sete", seven)
    ordered = seven.sort_values("rmse_mean")
    fig, axes = plt.subplots(1, 3, figsize=(15, 6.7), layout="constrained")
    for ax, metric, label in zip(
        axes, ["rmse", "mae", "r2"], ["RMSE (pontos) ↓", "MAE (pontos) ↓", "R² ↑"], strict=True
    ):
        y = np.arange(len(ordered))
        ax.barh(
            y,
            ordered[metric + "_mean"],
            xerr=ordered[metric + "_std"],
            color=[COLORS.get(m, "#5d7186") for m in ordered.model],
            capsize=3,
        )
        ax.set(yticks=y, yticklabels=ordered.label, xlabel=label, ylabel="Algoritmo")
        ax.invert_yaxis()
        maximum = ordered[metric + "_mean"].max()
        for i, row in enumerate(ordered.itertuples()):
            value = getattr(row, metric + "_mean")
            ax.text(
                value + maximum * 0.025,
                i,
                pt(value, 4 if metric == "r2" else 3),
                va="center",
                fontsize=8,
            )
        ax.set_xlim(0, maximum * 1.25)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: pt(x, 2)))
    c.save(
        fig,
        "02_sete_algoritmos",
        "Comparação nacional dos sete algoritmos — configurações iniciais",
        "Desenvolvimento",
        "Mesmas três dobras e 40 entradas. Barras de erro: DP populacional "
        "entre dobras; não intervalos de confiança.",
        [table],
    )

    table = c.table("trio_selecionado_inicial", selected)
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 5.3), layout="constrained")
    for ax, metric, label in zip(
        axes, ["rmse", "mae", "r2"], ["RMSE (pontos) ↓", "MAE (pontos) ↓", "R² ↑"], strict=True
    ):
        for i, row in enumerate(selected.itertuples()):
            value, std = getattr(row, metric + "_mean"), getattr(row, metric + "_std")
            ax.errorbar(
                value,
                i,
                xerr=std,
                fmt="o",
                capsize=5,
                color=COLORS[row.model],
                label=LABELS[row.model],
            )
            ax.annotate(
                pt(value, 4 if metric == "r2" else 3),
                (value, i),
                xytext=(0, 12),
                textcoords="offset points",
                ha="center",
                fontsize=9,
            )
        ax.set(yticks=range(3), yticklabels=selected.label, xlabel=label, ylim=(2.5, -0.6))
        ax.margins(x=0.22)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.xaxis.set_major_formatter(
            FuncFormatter(lambda v, _, metric=metric: pt(v, 3 if metric == "r2" else 1))
        )
    c.save(
        fig,
        "03_trio_selecionado",
        "Três selecionados na validação — detalhe das diferenças",
        "Desenvolvimento",
        "Seleção do Checkpoint 2 entre os sete. Eixos ampliados, sem barras "
        "partindo de zero; a seleção não usa o teste.",
        [table],
        CV_NOTE
        + "\nEixos ampliados para leitura; diferenças não demonstram significância estatística.",
    )

    table = c.table("comparacoes_cv_completas", summaries)
    original = summaries.loc[summaries.variant.eq("original")].sort_values("rmse")
    variants = summaries.loc[~summaries.variant.eq("original")].sort_values("rmse")
    variants_labels = {
        "engineered": "Engenharia",
        "selected": "Seleção",
        "pca": "PCA",
        "weighted": "Ponderação",
        "without_socio": "Sem socioeconômicas",
        "without_uf": "Sem UF",
    }
    fig, axes = plt.subplots(1, 2, figsize=(13, 8), layout="constrained")
    for ax, frame, title in zip(
        axes,
        [original, variants],
        ["Catálogo inicial e baseline", "Representações e ablações"],
        strict=True,
    ):
        labels = [
            LABELS.get(r.model, r.model)
            + (f" · {variants_labels.get(r.variant, r.variant)}" if r.variant != "original" else "")
            for r in frame.itertuples()
        ]
        ax.barh(labels, frame.rmse, xerr=frame.rmse_std, color="#3566a0", capsize=3)
        ax.set(
            title=title,
            xlabel="RMSE (pontos) ↓",
            ylabel="Modelo / representação",
            xlim=(0, frame.rmse.max() * 1.17),
        )
        ax.invert_yaxis()
        for i, row in enumerate(frame.itertuples()):
            ax.text(row.rmse + 1, i, pt(row.rmse), va="center", fontsize=8)
    c.save(
        fig,
        "04_catalogo_variantes",
        "Referências, engenharia de atributos e variantes — validação cruzada",
        "Desenvolvimento",
        "Inclui baseline e resultados sem melhoria. As variantes são "
        "comparações do modelo indicado, não novas buscas sobre o teste. Tempos "
        "completos estão na tabela.",
        [table],
    )


def development_histogram(c):
    root = Path("dados/processed/enem2023-v1")
    manifest = json.loads(c.source(root / "manifesto.json").read_text())
    split_path = c.source(
        Path("dados/splits/ciencias-natureza-v1/particoes.parquet"),
        "02b7f7a866e6a8ad40dd82711007b883bd4f5a6898d5cd84b9602059e9667873",
    )
    split = pd.read_parquet(split_path)
    ids = pd.Index(split.loc[split.partition.eq("development"), "NU_INSCRICAO"].astype("string"))
    if len(ids) != 2153941 or not ids.is_unique:
        raise ValueError("IDs de desenvolvimento incorretos")
    frames = []
    for part in manifest["parts"]:
        path = c.source(root / part["file"], part["sha256"])
        frame = pd.read_parquet(path, columns=["NU_INSCRICAO", "NU_NOTA_CN"])
        frame["NU_INSCRICAO"] = frame.NU_INSCRICAO.astype("string")
        frames.append(frame)
    frame = pd.concat(frames, ignore_index=True)
    frame = frame.loc[frame.NU_INSCRICAO.isin(ids)].reset_index(drop=True)
    if (
        len(frame) != len(ids)
        or frame.NU_INSCRICAO.duplicated().any()
        or frame.NU_NOTA_CN.isna().any()
    ):
        raise ValueError("Cobertura da distribuição incorreta")
    values = frame.NU_NOTA_CN.to_numpy()
    counts, edges = np.histogram(
        values, bins=np.arange(0, max(1000, np.ceil(values.max() / 25) * 25) + 25, 25)
    )
    table = c.table(
        "distribuicao_desenvolvimento",
        pd.DataFrame({"limite_inferior": edges[:-1], "limite_superior": edges[1:], "n": counts}),
    )
    zero = int((values == 0).sum())
    if counts.sum() != 2153941 or zero != 13236:
        raise ValueError("Contagens de distribuição incorretas")
    c.table(
        "populacao",
        pd.DataFrame(
            [
                {
                    "n_source": 3933955,
                    "n_missing_target": 1241528,
                    "n_eligible": 2692427,
                    "n_development": len(values),
                    "n_zero_development": zero,
                    "n_test": 538486,
                    "n_zero_test": 3311,
                }
            ]
        ),
    )
    fig, ax = plt.subplots(figsize=(10, 5.5), layout="constrained")
    ax.bar(
        edges[:-1],
        counts,
        width=25,
        align="edge",
        color="#3566a0",
        edgecolor="white",
        linewidth=0.3,
        label="Notas observadas",
    )
    ax.bar(0, zero, width=25, align="edge", color="#a65400", label=f"Notas zero: {pt(zero, 0)}")
    ax.set(xlabel="Nota de Ciências da Natureza (pontos)", ylabel="Participantes", xlim=(0, 1000))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pt(v, 0)))
    ax.legend(loc="upper right")
    c.save(
        fig,
        "01_distribuicao",
        "Distribuição da nota alvo no desenvolvimento",
        "Desenvolvimento",
        "Todos os 2.153.941 participantes do desenvolvimento; 13.236 notas zero "
        "preservadas. Ausência de nota não foi convertida em zero. Intervalos "
        "de 25 pontos.",
        [table, "tabelas/populacao.csv"],
        "Fonte: Inep, ENEM 2023 · desenvolvimento, n=2.153.941 · histograma de "
        "25 pontos; zeros identificados.",
    )


def pca_plot(c):
    directory = BASE / "pca-v2"
    c.manifest(directory)
    rows = pd.read_csv(directory / "experimentos.csv")
    records = []
    fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
    for row in rows.itertuples():
        learned = json.loads(row.diagnostics_json)
        values = np.cumsum(learned["pca_explained_variance_ratio"])
        k = int(learned["pca_components"])
        if k > len(values) or values[k - 1] < 0.8 or values[k - 2] >= 0.8:
            raise ValueError("Critério PCA inconsistente")
        records.extend(
            {
                "model": row.model,
                "fold": int(row.fold),
                "component": j + 1,
                "cumulative_variance": v,
                "selected_components": k,
            }
            for j, v in enumerate(values)
        )
        ax.plot(
            np.arange(1, len(values) + 1),
            values,
            label=f"{LABELS[row.model]} · dobra {int(row.fold) + 1} · k={k}",
            linestyle="-" if row.model == "ridge" else "--",
            alpha=0.8,
        )
    ax.axhline(0.8, color="#a65400", ls=":", label="Limiar: 80%")
    ax.axvline(45, color="#888888", ls=":")
    ax.set(
        xlabel="Número de componentes",
        ylabel="Variância explicada acumulada",
        ylim=(0, 1),
        xlim=(1, len(values)),
    )
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.legend(loc="lower right", fontsize=9)
    table = c.table("pca_variancia", pd.DataFrame(records))
    c.save(
        fig,
        "05_pca",
        "PCA — número de componentes escolhido em cada treino",
        "Desenvolvimento",
        "PCA centrado, ajustado apenas no treino de cada dobra. Ridge e árvore "
        "retiveram 45 componentes para alcançar pelo menos 80% da variância; as "
        "seis curvas quase coincidem.",
        [table],
        "Fonte: Inep, ENEM 2023 · treino de três dobras, dois regressores · "
        "limiar predefinido: variância ≥80%.",
    )


def residual_plot(c):
    path = c.source(CP4 / "avaliacao_final/previsoes_teste.csv")
    frame = pd.read_csv(path, usecols=["nota_observada", "previsao_stacking"])
    x = frame.previsao_stacking.to_numpy()
    residual = frame.nota_observada.to_numpy() - x
    if len(x) != 538486 or not np.isfinite(residual).all():
        raise ValueError("Previsões inválidas")
    fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
    cells = ax.hexbin(
        x, residual, gridsize=65, mincnt=1, norm=LogNorm(), cmap="viridis", rasterized=True
    )
    fig.colorbar(cells, ax=ax, label="Participantes por célula (escala log)")
    ax.axhline(0, color="#bc3030", ls="--", label="Resíduo zero")
    ax.set(
        xlabel="Nota prevista pelo Stacking (pontos)", ylabel="Nota observada − prevista (pontos)"
    )
    ax.legend(loc="upper right")
    offsets = cells.get_offsets()
    counts = cells.get_array()
    if int(counts.sum()) != len(x):
        raise ValueError("Hexbin não cobre todo o teste")
    table = c.table(
        "residuos_stacking_celulas",
        pd.DataFrame(
            {
                "predicted_center": offsets[:, 0],
                "residual_center": offsets[:, 1],
                "n": counts.astype(int),
            }
        ),
    )
    c.save(
        fig,
        "17_residuos_previsto",
        "Resíduos do Stacking em função da nota prevista",
        "Teste",
        "Todos os 538.486 participantes agregados em células, sem amostra ou "
        "corte de extremos. Resíduo negativo: superestimação. A dispersão "
        "remanescente limita a precisão individual.",
        [table],
        "Fonte: Inep, ENEM 2023 · teste, n=538.486 · resíduos = observado − "
        "previsto · todos os participantes.",
    )


def gallery(c):
    cards = []
    for f in sorted(c.figures, key=lambda f: f["id"]):
        links = " · ".join(
            f'<a href="{html.escape(p)}">{html.escape(Path(p).stem)}</a>' for p in f["tables"]
        )
        cards.append(
            f'<article data-stage="{f["stage"]}">'
            f'<p class="tag">{f["stage"]}</p>'
            f"<h2>{html.escape(f['title'])}</h2>"
            f'<a href="{f["svg"]}">'
            f'<img loading="lazy" src="{f["png"]}" alt="{html.escape(f["title"])}">'
            f"</a>"
            f"<p>{html.escape(f['caption'])}</p>"
            f"<p>"
            f'<a href="{f["png"]}" download>PNG · 300 dpi</a> · '
            f'<a href="{f["svg"]}" download>SVG</a>'
            f"</p>"
            f'<p class="tables">Tabelas: {links}</p>'
            f"</article>"
        )
    page = """<!doctype html>
<html lang="pt-BR">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ENEM 2023 — coleção de gráficos</title>
<style>
body{margin:0;
background:#f3f5f7;
color:#172d3c;
font:17px/1.6 system-ui,sans-serif}
header,main{max-width:1150px;
margin:auto;
padding:30px}
h1{font-size:36px;
line-height:1.2}
h2{font-size:23px}
article{background:white;
border:1px solid #d7dfe4;
border-radius:12px;
padding:24px;
margin:26px 0}
img{width:100%;
height:auto}
a{color:#146075}
button{font:inherit;
border:1px solid #146075;
color:#146075;
background:white;
padding:8px 18px;
border-radius:6px;
cursor:pointer}
button[aria-pressed=true]{background:#146075;
color:white}
.tag{font-size:14px;
font-weight:700;
color:#595959}
.tables{font-size:14px;
overflow-wrap:anywhere}
[hidden]{display:none}
nav{display:flex;
gap:10px;
flex-wrap:wrap}
@media print{nav{display:none}
article{break-inside:avoid;
border:0}
body{background:white}
}

</style>
<header>
<p>CHECKPOINT 5 · CIÊNCIAS DA NATUREZA</p>
<h1>Comparação nacional de modelos<br>ENEM 2023</h1>
<p>17 figuras com tabelas de apoio. Desenvolvimento: 2.153.941 participantes · Teste: 538.486.</p>
<p>As configurações foram fixadas antes do teste. DP entre dobras não é intervalo de confiança.
A comparação é de regressão; resíduos e erros por grupo são as visualizações adequadas.</p>
<p>
<a href="catalogo.json">Catálogo e fontes</a> · <a href="README.md">Guia da coleção</a>
</p>
<nav aria-label="Filtrar por etapa">"""
    for stage in ["Todos", "Desenvolvimento", "Teste"]:
        pressed = str(stage == "Todos").lower()
        page += (
            f'<button type="button" data-filter="{stage}" aria-pressed="{pressed}">{stage}</button>'
        )
    page += (
        '</nav><p id="count" aria-live="polite">17 figuras</p></header><main>'
        + "".join(cards)
        + """</main><script>
const buttons=[...document.querySelectorAll('button[data-filter]')];
buttons.forEach(b=>b.addEventListener('click',()=>{buttons.forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
let n=0;
document.querySelectorAll('article').forEach(a=>{a.hidden=b.dataset.filter!=='Todos'&&a.dataset.stage!==b.dataset.filter;
if(!a.hidden)n++}
);
document.querySelector('#count').textContent=n+' figuras';
}
));

</script></html>"""
    )
    (c.output / "index.html").write_text(page)
    write_json(
        c.output / "catalogo.json",
        {
            "figures": sorted(c.figures, key=lambda f: f["id"]),
            "source": "Inep / ENEM 2023",
            "new_training": False,
            "new_test_evaluation": False,
        },
    )
    rows = [
        "# Coleção final de gráficos — Checkpoint 5",
        "",
        "Abrir `index.html` em um navegador. PNGs em 300 dpi e SVGs com texto "
        "editável; densidades mantêm células rasterizadas para controlar o "
        "tamanho. Tabelas CSV preservam a precisão numérica. Nenhum treinamento "
        "ou nova avaliação do teste foi executado.",
        "",
        "| Figura | Etapa | Interpretação |",
        "|---|---|---|",
    ]
    rows += [
        f"| [{f['id']}]({f['png']}) | {f['stage']} | {f['caption']} |"
        for f in sorted(c.figures, key=lambda f: f["id"])
    ]
    rows += [
        "",
        "As figuras 01, 04+06, 05, 08, 11+17 e 13+14 cobrem os seis grupos de "
        "evidências visuais do enunciado. A comparação dos sete está em 02; a "
        "seleção do trio em 03; o teste em 09–17. Tabelas de CV e teste "
        "permanecem separadas. A diagramação no artigo e os PDFs pertencem aos "
        "Checkpoints 6 e 7.",
        "",
        "O CSV bruto `MICRODADOS_ENEM_2023.csv` e o pacote original "
        "`microdados_enem_2023.zip` estão ausentes nesta cópia. Os experimentos "
        "usam a base limpa recuperada e verificada. Este pacote de gráficos não "
        "contém os microdados individuais.",
    ]
    (c.output / "README.md").write_text("\n".join(rows) + "\n")


def publish(output):
    if output.exists():
        raise FileExistsError("Preservar a coleção anterior; escolher nova saída.")
    c = Collection(output)
    for n in [1, 2, 3, 4]:
        checkpoint = BASE / f"checkpoint-{n}-2026-11-{'07' if n == 4 else '06'}" / "checkpoint.json"
        marker = json.loads(c.source(checkpoint).read_text())
        if marker["status"] != "completed":
            raise ValueError("Checkpoint anterior incompleto")
        c.source(marker["report"], marker["report_sha256"])
    cp1 = BASE / "checkpoint-1-2026-11-06/publicacao-v2"
    cp2 = BASE / "checkpoint-2-2026-11-06"
    for directory in [
        cp1,
        cp2,
        CP4 / "publicacao-v2",
        CP4 / "publicacao_buscas-v2",
        CP4 / "avaliacao_final",
    ]:
        c.manifest(directory)
    marker = json.loads((CP4 / "checkpoint.json").read_text())
    c.source(CP4 / "publicacao-v2/manifesto.json", marker["publication_manifest_sha256"])
    c.source(CP4 / "avaliacao_final/manifesto.json", marker["final_manifest_sha256"])
    c.source(CP4 / "validacao_final.json", marker["validation_sha256"])
    consolidated = c.source(
        Path("resultados/experimentos.csv"),
        "8afdabe91cd0f675329c82a49d031cf0f69205fa27fc267af82cc7a51c86924f",
    )
    experiments = pd.read_csv(consolidated)
    summaries = experiments.loc[experiments.row_type.eq("summary")].copy()
    if (
        len(experiments) != 72
        or len(summaries) != 18
        or not experiments.test_evaluated.eq(False).all()
    ):
        raise ValueError("Consolidado inicial incompatível")
    for _, s in summaries.iterrows():
        folds = experiments.loc[
            experiments.experiment_id.eq(s.experiment_id) & experiments.row_type.eq("fold")
        ]
        if len(folds) != 3:
            raise ValueError("Dobras incompletas")
        for metric in ["rmse", "mae", "r2"]:
            np.testing.assert_allclose(
                [s[metric], s[metric + "_std"]],
                [folds[metric].mean(), folds[metric].std(ddof=0)],
                rtol=0,
                atol=1e-9,
            )
    (output / "figuras").mkdir(parents=True)
    (output / "tabelas").mkdir()
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.fonttype": "none",
            "axes.grid": True,
            "grid.alpha": 0.15,
        }
    )
    comparisons(
        c,
        pd.read_csv(cp1 / "comparacao_sete_modelos.csv"),
        pd.read_csv(cp2 / "tres_selecionados.csv"),
        summaries,
    )
    development_histogram(c)
    pca_plot(c)
    search = CP4 / "publicacao_buscas-v2"
    final = CP4 / "publicacao-v2"
    for folder, name in [
        (search, "antes_depois"),
        (search, "todas_configuracoes"),
        (final, "comparacao_teste"),
        (final, "validacao_e_teste"),
        (final, "curvas_resumo"),
        (final, "curvas_por_dobra"),
        (final, "erros_grupos"),
    ]:
        shutil.copy2(folder / f"{name}.csv", output / "tabelas" / f"{name}.csv")
    c.copy(
        search,
        "comparacao_antes_depois",
        "06_buscas",
        "Modelos antes e depois das buscas",
        "Desenvolvimento",
        "Cinco modelos, 12 configurações por modelo. Inclui o trio solicitado e "
        "os três melhores do catálogo ampliado.",
        ["tabelas/antes_depois.csv"],
    )
    c.copy(
        search,
        "magnitude_melhorias",
        "07_ganhos_buscas",
        "Magnitude das melhorias nas buscas",
        "Desenvolvimento",
        "Ganhos muito pequenos; a mudança do Stacking não demonstrou relevância "
        "prática ou estatística.",
        ["tabelas/antes_depois.csv", "tabelas/todas_configuracoes.csv"],
    )
    mappings = [
        (
            "curvas_configuracoes_finais",
            "08_curvas_finais",
            "Curvas das configurações finais",
            "Desenvolvimento",
            "Treino e validação em cinco tamanhos, nas três dobras; receitas "
            "fixadas antes do teste.",
            ["curvas_resumo", "curvas_por_dobra"],
        ),
        (
            "comparacao_teste",
            "09_teste",
            "Comparação final no teste",
            "Teste",
            "Trio, baseline e linear nos mesmos 538.486 participantes. A linear "
            "tem RMSE menor que SVM e Random Forest.",
            ["comparacao_teste"],
        ),
        (
            "validacao_versus_teste",
            "10_cv_teste",
            "Validação versus teste",
            "Teste",
            "CV em três dobras e teste em modelos reajustados no "
            "desenvolvimento completo; populações de treino distintas.",
            ["validacao_e_teste"],
        ),
        (
            "observado_versus_previsto",
            "11_observado_previsto",
            "Notas observadas versus previstas",
            "Teste",
            "Todos os participantes; mesma escala de células e linha da "
            "previsão perfeita para o trio.",
            ["comparacao_teste"],
        ),
        (
            "distribuicao_residuos",
            "12_distribuicao_residuos",
            "Distribuição dos resíduos",
            "Teste",
            "Intervalos comuns e todos os resíduos; a média global não descreve os erros extremos.",
            ["comparacao_teste"],
        ),
        (
            "erros_faixa_nota",
            "13_faixas",
            "Erros por faixa de nota",
            "Teste",
            "Faixas fixadas no desenvolvimento e tamanhos dos grupos. Erros "
            "maiores nas notas extremas.",
            ["erros_grupos"],
        ),
        (
            "erros_tp_escola",
            "14_escola",
            "Erros por tipo de escola",
            "Teste",
            "Códigos de TP_ESCOLA e contagens; associação observacional, sem inferência causal.",
            ["erros_grupos"],
        ),
        (
            "erros_sg_uf_prova",
            "15_uf",
            "Erros por UF de aplicação",
            "Teste",
            "UF da prova não é necessariamente residência; contagens por UF na tabela.",
            ["erros_grupos"],
        ),
        (
            "erros_q006",
            "16_renda",
            "Erros por faixa de renda",
            "Teste",
            "Categorias de Q006; contagens na tabela. Diferenças não determinam "
            "a capacidade individual.",
            ["erros_grupos"],
        ),
    ]
    for source, stem, title, stage, caption, tables in mappings:
        c.copy(final, source, stem, title, stage, caption, [f"tabelas/{t}.csv" for t in tables])
    residual_plot(c)
    gallery(c)
    if len(c.figures) != 17:
        raise ValueError("Coleção incompleta")
    write_json(
        output / "manifesto.json",
        {
            **runtime_metadata(),
            "checkpoint": 5,
            "status": "generated",
            "visual_validation_pending": True,
            "figures": 17,
            "new_training": False,
            "new_test_evaluation": False,
            "inputs": c.inputs,
            "script_sha256": sha256_file(Path(__file__)),
            "assets": {
                str(p.relative_to(output)): sha256_file(p)
                for p in sorted(output.rglob("*"))
                if p.is_file()
            },
        },
    )
    print(f"Geradas 17 figuras PNG/SVG em {output}; revisão visual pendente.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    publish(parser.parse_args().output)
