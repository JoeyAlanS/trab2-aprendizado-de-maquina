"""Resumo do estudo e recorte interativo."""

import streamlit as st

from enem_base.dashboard_ui import (
    NAVY,
    TEAL,
    chart,
    cohort_caption,
    comparison_chart,
    current_cube,
    dashboard_data,
    group_table,
    histogram,
    metric_row,
    number,
)

data = dashboard_data()
cube = current_cube(data)
st.header("Visão geral", anchor=False)
cohort_caption(data, cube)
metric_row(cube)

left, right = st.columns([1.5, 1], gap="medium")
with left, st.container(border=True):
    st.subheader("Como as notas se distribuem", anchor=False)
    chart(histogram(cube), "overview_hist", "Histograma das notas CN no recorte de desenvolvimento")
    st.caption("Intervalos de 25 pontos. A linha indica a média das notas originais.")
with right, st.container(border=True):
    st.subheader("Nota por tipo de escola", anchor=False)
    schools = group_table(data, cube, "TP_ESCOLA").sort_values("nota_media")
    school_fig = comparison_chart(schools)
    school_fig.update_traces(
        marker_color=[NAVY if code == "1" else TEAL for code in schools.TP_ESCOLA]
    )
    chart(school_fig, "overview_school", "Nota média por tipo de escola no recorte")
    st.caption("“Não respondeu” permanece como categoria própria. Os grupos têm perfis diferentes.")

st.subheader("Da base nacional ao estudo", anchor=False)
st.caption("Contagens do protocolo completo, independentes dos filtros laterais.")
population = data.manifest["population"]
with st.container(horizontal=True, vertical_alignment="distribute"):
    for label, field, description in (
        ("Base nacional", "source_rows", "Registros preservados na importação."),
        ("Com nota CN", "eligible", "Elegíveis, incluindo notas zero."),
        ("Desenvolvimento · 80%", "development", "Exploração e validação em três dobras."),
        ("Teste reservado · 20%", "test", "Ainda sem avaliação de modelos."),
    ):
        with st.container(border=True, width=245, height="stretch"):
            st.caption(label)
            st.subheader(number(population[field]), anchor=False)
            st.caption(description)
st.caption(
    f"{number(population['missing_target'])} registros sem nota CN permanecem no diagnóstico "
    "da base, fora da regressão. O alvo não foi imputado."
)

with st.container(border=True):
    st.subheader("Uma primeira leitura dos modelos", anchor=False)
    best = data.cv.sort_values("rmse_mean").iloc[0]
    baseline = data.cv.loc[data.cv.model.eq("baseline"), "rmse_mean"].iloc[0]
    improvement = (baseline - best.rmse_mean) / baseline * 100
    st.markdown(
        f"Linear e Ridge apresentaram resultados praticamente iguais na validação inicial: "
        f"**RMSE de {number(best.rmse_mean, 2)} pontos**, cerca de "
        f"**{number(improvement, 1)}%** abaixo da referência pela média."
    )
    st.caption(
        "Resultados globais de validação cruzada; os filtros não recalculam modelos. "
        "Ainda não há um modelo final selecionado."
    )
    st.page_link(
        "app_pages/modelos.py", label="Ver comparação dos modelos", icon=":material/arrow_forward:"
    )

# Pequeno resumo textual acessível complementa os gráficos.
with st.expander("Ler os valores por escola"):
    st.dataframe(
        schools[["grupo", "participantes", "nota_media"]]
        .rename(
            columns={
                "grupo": "Tipo de escola",
                "participantes": "Participantes",
                "nota_media": "Nota média",
            }
        )
        .assign(**{"Nota média": lambda df: df["Nota média"].round(2)}),
        hide_index=True,
        alt="Valores do gráfico de notas por escola",
    )
