"""Comparações descritivas usando estatísticas exatas de grupos."""

import json

import streamlit as st

from enem_base.dashboard_ui import (
    chart,
    cohort_caption,
    comparison_chart,
    current_cube,
    dashboard_data,
    download_table,
    group_table,
    histogram,
    metric_row,
    show_table,
)

data = dashboard_data()
cube = current_cube(data)
st.header("Explorar dados", anchor=False)
cohort_caption(data, cube)
metric_row(cube)

dimensions = {
    "UF da prova": "SG_UF_PROVA",
    "Tipo de escola": "TP_ESCOLA",
    "Renda familiar": "Q006",
    "Sexo informado": "TP_SEXO",
    "Treineiro": "IN_TREINEIRO",
}
with st.container(horizontal=True, vertical_alignment="bottom"):
    choice = st.selectbox("Comparar por", list(dimensions), key="explore_dimension", width=260)
    indicator = st.segmented_control(
        "Indicador", ["Nota média", "Participantes"], default="Nota média", key="explore_indicator"
    )
field = dimensions[choice]
table = group_table(data, cube, field)
value = "participantes" if indicator == "Participantes" else "nota_media"
if field == "Q006":
    table = table.sort_values(field)
    # Códigos mantêm ordem ordinal; os rótulos completos ficam na tabela e no dicionário.
    plot_table = table.assign(grupo=table.Q006)
else:
    table = table.sort_values(value, ascending=False)
    plot_table = table.sort_values(value)

with st.container(border=True):
    st.subheader(f"{indicator or 'Nota média'} por {choice.lower()}", anchor=False)
    chart(
        comparison_chart(
            plot_table,
            horizontal=field != "Q006",
            value=value,
            height=max(340, len(table) * 23) if field != "Q006" else 370,
        ),
        "explore_group",
        f"{indicator or 'Nota média'} por {choice.lower()} no recorte selecionado",
    )
    if field == "Q006":
        st.caption(
            "A–Q são as alternativas de renda familiar do questionário de 2023, em ordem. "
            "Consulte seus valores na tabela abaixo. Não representam renda individual."
        )
    elif field == "SG_UF_PROVA":
        st.caption(
            "UF onde a prova foi aplicada. Os resultados não são rankings de qualidade da educação."
        )
    else:
        st.caption(
            "Comparação descritiva. As médias não controlam diferenças entre os perfis dos grupos."
        )

st.subheader("Tabela do recorte", anchor=False)
show_table(table, key="explore_table", alt="Contagem, nota média e notas zero por grupo")
export = table.assign(
    conjunto="development",
    alvo=data.manifest["target"],
    filtros=json.dumps(st.session_state.get("dashboard_filters", {}), ensure_ascii=False),
    snapshot_utc=data.manifest["created_at_utc"],
)
download_table(export, "Baixar tabela do recorte", "enem_cn_recorte.csv", "download_cohort")
st.caption(
    "CSV com separador ponto e vírgula e decimal com vírgula. "
    "Contém somente estatísticas agregadas."
)

with st.expander("Distribuição das notas neste recorte", on_change="rerun") as detail:
    if detail.open:
        chart(histogram(cube), "explore_hist", "Histograma de notas CN após os filtros")
