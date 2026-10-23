"""Qualidade, dicionário, rastreabilidade e limites da análise."""

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from enem_base.dashboard_ui import GOLD, base_chart, chart, dashboard_data, number

data = dashboard_data()
st.header("Qualidade e método", anchor=False)
st.caption("Diagnósticos globais. Os filtros laterais não alteram esta página.")
quality = data.quality
with st.container(horizontal=True, vertical_alignment="distribute"):
    st.metric("Registros preparados", number(quality["rows"]), border=True, width=240)
    st.metric("Colunas preservadas", str(quality["column_count"]), border=True, width=210)
    st.metric("IDs duplicados", number(quality["duplicate_identifiers"]), border=True, width=210)
    st.metric(
        "Erros de conversão",
        number(sum(quality["invalid_numeric"].values())),
        border=True,
        width=210,
    )
st.success(
    "A importação nacional passou nas validações, com zero linhas removidas. "
    "Ausências e notas zero foram preservadas.",
    icon=":material/check_circle:",
)

missing = pd.DataFrame(
    [
        {"Variável": name, "Ausências": count, "Percentual": count / data.eda["rows"] * 100}
        for name, count in data.eda["missing"].items()
    ]
).sort_values("Percentual", ascending=False)
with st.container(border=True):
    st.subheader("Ausências nas variáveis de entrada", anchor=False)
    nonzero = missing.loc[missing.Ausências.gt(0)].sort_values("Percentual")
    fig = go.Figure(
        go.Bar(
            y=nonzero.Variável,
            x=nonzero.Percentual,
            orientation="h",
            marker_color=GOLD,
            customdata=nonzero[["Ausências"]].values,
            hovertemplate=(
                "%{y}<br>%{x:.2f}% ausentes<br>%{customdata[0]:,.0f} registros<extra></extra>"
            ),
        )
    )
    fig.update_xaxes(title="Ausências no desenvolvimento (%)", range=[0, 100])
    chart(
        base_chart(fig, 300),
        "quality_missing",
        "Percentual de ausência nas quatro variáveis incompletas",
    )
    st.caption(
        "Somente desenvolvimento. As demais variáveis de entrada não apresentam ausência. "
        "Alternativas como “Não respondeu” são categorias e não foram convertidas em nulo."
    )

st.subheader("Dicionário das variáveis", anchor=False)
query = st.text_input(
    "Buscar nome ou descrição", placeholder="Ex.: renda, escola, Q006…", key="dictionary_search"
)
dictionary = data.dictionary["columns"]
entries = [
    {
        "Variável": name,
        "Descrição": item["description"],
        "Uso": "Alvo" if name == data.manifest["target"] else "Entrada",
        "Tratamento": "Numérica" if name in ("Q005", data.manifest["target"]) else "Categórica",
    }
    for name, item in dictionary.items()
    if not query or query.casefold() in f"{name} {item['description']}".casefold()
]
if entries:
    st.dataframe(
        pd.DataFrame(entries),
        hide_index=True,
        width="stretch",
        alt="Variáveis e descrições do dicionário oficial",
    )
    selected = st.selectbox(
        "Consultar alternativas", [entry["Variável"] for entry in entries], key="dictionary_field"
    )
    categories = dictionary[selected].get("categories", {})
    if categories:
        st.dataframe(
            pd.DataFrame({"Código": list(categories), "Alternativa": list(categories.values())}),
            hide_index=True,
            width="stretch",
            alt=f"Alternativas oficiais da variável {selected}",
        )
    else:
        st.caption("Variável sem alternativas categóricas no dicionário.")
else:
    st.info("Nenhuma variável encontrada. Tente outro termo.")

st.subheader("Como o estudo foi organizado", anchor=False)
with st.container(border=True):
    st.markdown(
        "**1. Fonte nacional → preparação**\n\n"
        "CSV oficial, importação em lotes, Parquet e validação de integridade por SHA-256. "
        "Não houve remoção de participantes por perfil ou por nota zero.\n\n"
        "**2. Alvo observado → divisão 80/20**\n\n"
        "NU_NOTA_CN é o alvo. Apenas sua ausência impede entrada na regressão. "
        "A partição é fixa, com semente 42 e teste reservado.\n\n"
        "**3. Desenvolvimento → validação em três dobras**\n\n"
        "Imputação numérica pela mediana, padronização e codificação one-hot são ajustadas "
        "no treino de cada dobra. Notas de outras áreas, respostas, presença e identificadores "
        "não entram como preditores.\n\n"
        "**4. Dashboard → agregados do desenvolvimento**\n\n"
        "Filtros combinam contagens, somas e somas dos quadrados das notas originais. "
        "As médias são ponderadas pelo número de participantes. O histograma usa intervalos "
        "de 25 pontos; não é usado para aproximar as médias ou o desvio padrão."
    )

with st.expander("Etapas ainda pendentes"):
    st.markdown(
        "- Ampliar e comparar as famílias de modelos exigidas.\n"
        "- Executar seleção de variáveis, PCA, buscas e análises complementares.\n"
        "- Consolidar hipóteses e curvas de aprendizagem.\n"
        "- Congelar a seleção, avaliar o teste uma única vez e analisar os erros.\n"
        "- Concluir o artigo e a apresentação com os resultados finais."
    )
with st.expander("Rastreabilidade e downloads"):
    st.caption(
        f"Snapshot gerado em {data.manifest['created_at_utc']}. "
        "Arquivos agregados e resultados conferidos por hash na leitura."
    )
    st.json(
        {
            key: data.manifest[key]
            for key in (
                "source_sha256",
                "splits_sha256",
                "study_sha256",
                "dictionary_sha256",
                "test_evaluated",
            )
        }
    )
    st.download_button(
        "Baixar manifesto do painel",
        json.dumps(data.manifest, ensure_ascii=False, indent=2),
        file_name="manifesto_dashboard_enem_cn.json",
        mime="application/json",
        icon=":material/download:",
        on_click="ignore",
        key="download_manifest",
    )
st.caption(
    "Limites: estudo observacional, respostas autodeclaradas, ausências expressivas nas variáveis "
    "escolares e seleção de quem realizou o exame. As comparações não permitem conclusões causais."
)
