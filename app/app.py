"""Iniciar da raiz: python -m streamlit run app/app.py."""

import streamlit as st

from enem_base.dashboard_ui import dashboard_data, sidebar_filters

st.set_page_config(
    page_title="Ciências da Natureza | ENEM 2023",
    page_icon=":material/science:",
    layout="wide",
    initial_sidebar_state="auto",
)

page = st.navigation(
    [
        st.Page(
            "app_pages/visao_geral.py",
            title="Visão geral",
            icon=":material/dashboard:",
            default=True,
        ),
        st.Page("app_pages/explorar.py", title="Explorar dados", icon=":material/query_stats:"),
        st.Page("app_pages/relacoes.py", title="Relações e relatório", icon=":material/hub:"),
        st.Page("app_pages/modelos.py", title="Modelos", icon=":material/model_training:"),
        st.Page("app_pages/metodo.py", title="Qualidade e método", icon=":material/fact_check:"),
    ],
    position="top",
)

st.caption("PROJETO 2 · APRENDIZADO DE MÁQUINA · ENEM 2023")
st.title("Ciências da Natureza", anchor=False)
st.markdown("Perfil socioeconômico, contexto escolar e desempenho no exame.")
with st.container(horizontal=True):
    st.badge("Dados oficiais do Inep", color="green", icon=":material/verified:")
    st.badge("Estudo em andamento", color="blue")

try:
    data = dashboard_data()
except (OSError, ValueError, KeyError) as error:
    st.error("Os dados do painel estão ausentes ou não passaram na verificação de integridade.")
    st.markdown(
        "Prepare o snapshot seguindo `docs/frontend.md`. "
        "Nenhum dado fictício é usado como substituto."
    )
    with st.expander("Detalhe para diagnóstico"):
        st.code(str(error), language=None)
    st.stop()

sidebar_filters(data)
page.run()

st.divider()
st.caption(
    "Fonte: microdados do ENEM 2023 · Inep. Exploração restrita ao desenvolvimento. "
    "Associações descritivas não demonstram causalidade."
)
