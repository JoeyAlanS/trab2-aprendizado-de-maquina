"""Resumo do estudo e recorte interativo."""

import streamlit as st

from enem_base.dashboard_ui import (
    MODEL_LABELS,
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
    model_results,
    number,
)

data = dashboard_data()
published = model_results(data)
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
        (
            "Teste final · 20%",
            "test",
            "Avaliação final concluída para cinco modelos."
            if published is not None
            else "Resultados finais não carregados nesta instalação.",
        ),
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
    st.subheader("Resultados dos modelos", anchor=False)
    cv = published.cv if published is not None else data.cv
    best = cv.sort_values("rmse_mean").iloc[0]
    baseline = cv.loc[cv.model.eq("baseline"), "rmse_mean"].iloc[0]
    improvement = (baseline - best.rmse_mean) / baseline * 100
    st.markdown(
        f"{MODEL_LABELS.get(best.model, best.model)} apresentou o menor erro nesta validação: "
        f"**RMSE de {number(best.rmse_mean, 2)} pontos**, cerca de "
        f"**{number(improvement, 1)}%** abaixo da referência pela média."
    )
    st.caption(
        "Resultados globais de validação cruzada; os filtros não recalculam modelos. "
        + (
            "O Stacking selecionado no desenvolvimento já foi avaliado no teste: "
            "RMSE de 76,190 pontos. Consulte as métricas finais na página Modelos."
            if published is not None
            else "Somente o resumo inicial está disponível neste painel."
        )
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
