"""Componentes compartilhados da interface Streamlit e gráficos do estudo."""

import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from enem_base.dashboard import (
    ASSETS,
    BIN_WIDTH,
    MISSING,
    DashboardData,
    filter_cube,
    grouped_statistics,
    load_dashboard,
    statistics,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE = PROJECT_ROOT / "resultados/ciencias_natureza/dashboard-v1"
TEAL = "#087f8c"
NAVY = "#2b5278"
GOLD = "#db9642"
GRAY = "#718395"
MODEL_LABELS = {
    "baseline": "Referência: média",
    "linear": "Regressão linear",
    "ridge": "Ridge",
    "arvore": "Árvore de decisão",
}


def number(value: float | int | None, decimals: int = 0) -> str:
    if value is None:
        return "—"
    return f"{value:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")


@st.cache_data(max_entries=2, ttl=3600, show_spinner="Conferindo os dados do painel…")
def _cached_data(path: str, signature: tuple) -> DashboardData:
    return load_dashboard(Path(path))


def dashboard_data() -> DashboardData:
    path = Path(os.environ.get("ENEM_DASHBOARD_DIR", DEFAULT_BUNDLE))
    # Invalidar também se um ativo muda sem alteração no manifesto.
    signature = tuple(
        (name, (path / name).stat().st_mtime_ns, (path / name).stat().st_size)
        for name in ("manifesto.json", *ASSETS)
    )
    return _cached_data(str(path), signature)


def category_label(data: DashboardData, field: str, code: str) -> str:
    if code == MISSING:
        return "Ausente"
    return data.dictionary["columns"][field].get("categories", {}).get(code, code)


def clear_filters() -> None:
    for name, value in {
        "filter_uf": [],
        "filter_school": "Todas",
        "filter_sex": "Todos",
        "filter_training": "Todos",
    }.items():
        st.session_state[name] = value


def sidebar_filters(data: DashboardData) -> None:
    with st.sidebar:
        st.header("ENEM / 2023", anchor=False)
        st.caption("Ciências da Natureza e suas Tecnologias")
        st.divider()
        st.subheader("Seu recorte", anchor=False)
        st.caption("Filtros da visão geral e da exploração.")
        ufs = st.multiselect(
            "UF de aplicação da prova",
            sorted(data.cube.SG_UF_PROVA.unique()),
            placeholder="Todas as UFs",
            key="filter_uf",
            help="Local da prova. Não representa necessariamente o local de residência.",
        )
        school = st.selectbox(
            "Tipo de escola",
            ["Todas", "1", "2", "3"],
            key="filter_school",
            format_func=lambda x: x if x == "Todas" else category_label(data, "TP_ESCOLA", x),
        )
        sex = st.selectbox(
            "Sexo informado",
            ["Todos", "F", "M"],
            key="filter_sex",
            format_func=lambda x: x if x == "Todos" else category_label(data, "TP_SEXO", x),
        )
        training = st.selectbox(
            "Participação como treineiro",
            ["Todos", "1", "0"],
            key="filter_training",
            format_func=lambda x: {"Todos": "Todos", "1": "Treineiro", "0": "Não treineiro"}[x],
        )
        st.button(
            "Limpar filtros",
            icon=":material/restart_alt:",
            on_click=clear_filters,
            width="stretch",
            key="reset_filters",
        )
        filters = {
            "SG_UF_PROVA": ufs,
            "TP_ESCOLA": [] if school == "Todas" else [school],
            "TP_SEXO": [] if sex == "Todos" else [sex],
            "IN_TREINEIRO": [] if training == "Todos" else [training],
        }
        st.session_state["dashboard_filters"] = filters
        current = statistics(filter_cube(data.cube, filters))["count"]
        st.divider()
        st.markdown(f"**{number(current)} participantes** no recorte")
        st.caption("Sem seleção de UF = todas. Somente desenvolvimento; notas zero preservadas.")
        st.badge("Teste reservado", color="blue", icon=":material/lock:")


def current_cube(data: DashboardData) -> pd.DataFrame:
    cube = filter_cube(data.cube, st.session_state.get("dashboard_filters", {}))
    if cube.empty:
        st.info(
            "Nenhum participante atende a esta combinação. "
            "Ajuste ou limpe os filtros na barra lateral.",
            icon=":material/filter_alt_off:",
        )
        st.stop()
    return cube


def cohort_caption(data: DashboardData, cube: pd.DataFrame) -> None:
    count = statistics(cube)["count"]
    total = data.manifest["n_development"]
    filters = st.session_state.get("dashboard_filters", {})
    pieces = []
    for field, codes in filters.items():
        if codes:
            pieces.extend(category_label(data, field, code) for code in codes)
    label = " · ".join(pieces) if pieces else "Brasil · todos os perfis"
    st.caption(f"{label} | {number(count / total * 100, 1)}% do desenvolvimento")


def metric_row(cube: pd.DataFrame) -> None:
    values = statistics(cube)
    with st.container(horizontal=True, vertical_alignment="distribute"):
        st.metric(
            "Participantes no recorte",
            number(values["count"]),
            border=True,
            width=230,
            help="Participantes com nota CN observada na partição de desenvolvimento.",
        )
        st.metric("Nota média de CN", number(values["mean"], 1), border=True, width=210)
        st.metric(
            "Desvio padrão da nota",
            number(values["std"], 1),
            border=True,
            width=210,
            help="Desvio padrão amostral das notas originais do recorte.",
        )
        st.metric(
            "Notas zero",
            number(values["zeros"]),
            border=True,
            width=200,
            help="Zero é uma nota observada e permanece no estudo.",
        )


def base_chart(fig: go.Figure, height: int = 330) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=18, t=20, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif", size=13, color="#182c40"),
        separators=",.",
        showlegend=False,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, automargin=True)
    fig.update_yaxes(gridcolor="#e8eef3", zeroline=False, automargin=True)
    return fig


def chart(fig: go.Figure, key: str, alt: str) -> None:
    st.plotly_chart(
        fig,
        width="stretch",
        key=key,
        theme=None,
        alt=alt,
        config={
            "displaylogo": False,
            "scrollZoom": False,
            "toImageButtonOptions": {"format": "png", "scale": 2},
        },
    )


def histogram(cube: pd.DataFrame) -> go.Figure:
    counts = cube.groupby("score_bin")["count"].sum()
    counts = counts.reindex(range(int(cube.score_bin.max()) + 1), fill_value=0)
    left = counts.index.to_numpy() * BIN_WIDTH
    fig = go.Figure(
        go.Bar(
            x=left + BIN_WIDTH / 2,
            y=counts.values,
            width=BIN_WIDTH - 2,
            marker_color=TEAL,
            customdata=[[f"{a} a menos de {a + BIN_WIDTH}"] for a in left],
            hovertemplate="%{customdata[0]} pontos<br>%{y:,.0f} participantes<extra></extra>",
        )
    )
    mean = statistics(cube)["mean"]
    fig.add_vline(
        x=mean,
        line_dash="dot",
        line_color=NAVY,
        annotation_text=f"Média {number(mean, 1)}",
        annotation_position="top right",
    )
    fig.update_xaxes(title="Nota de Ciências da Natureza", range=[0, max(left) + BIN_WIDTH])
    fig.update_yaxes(title="Participantes", tickformat="~s")
    return base_chart(fig)


def group_table(data: DashboardData, cube: pd.DataFrame, field: str) -> pd.DataFrame:
    table = grouped_statistics(cube, field)
    table["grupo"] = table[field].map(lambda code: category_label(data, field, code))
    return table[[field, "grupo", "participantes", "nota_media", "zeros"]]


def comparison_chart(
    table: pd.DataFrame, *, horizontal: bool = True, value: str = "nota_media", height: int = 330
) -> go.Figure:
    labels = table["grupo"]
    values = table[value]
    fig = go.Figure(
        go.Bar(
            x=values if horizontal else labels,
            y=labels if horizontal else values,
            orientation="h" if horizontal else "v",
            marker_color=TEAL,
            customdata=table[["participantes", "nota_media"]].values,
            hovertemplate=("%{y}" if horizontal else "%{x}")
            + (
                "<br>Média: %{customdata[1]:.1f}"
                "<br>Participantes: %{customdata[0]:,.0f}<extra></extra>"
            ),
        )
    )
    axis_title = "Nota média de CN" if value == "nota_media" else "Participantes"
    if horizontal:
        fig.update_xaxes(title=axis_title, rangemode="tozero")
    else:
        fig.update_yaxes(title=axis_title, rangemode="tozero")
    return base_chart(fig, height)


def show_table(table: pd.DataFrame, *, key: str, alt: str) -> None:
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        alt=alt,
        key=key,
        column_config={
            "nota_media": st.column_config.NumberColumn("Nota média", format="%.2f"),
            "participantes": st.column_config.NumberColumn("Participantes", format="localized"),
            "zeros": st.column_config.NumberColumn("Notas zero", format="localized"),
            "grupo": st.column_config.TextColumn("Grupo"),
        },
    )


def download_table(table: pd.DataFrame, label: str, filename: str, key: str) -> None:
    st.download_button(
        label,
        table.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        icon=":material/download:",
        on_click="ignore",
        key=key,
    )
