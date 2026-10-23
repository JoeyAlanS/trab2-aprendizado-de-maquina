"""Resultados globais já executados; nenhum treinamento nesta interface."""

import plotly.graph_objects as go
import streamlit as st

from enem_base.dashboard_ui import (
    GRAY,
    MODEL_LABELS,
    TEAL,
    base_chart,
    chart,
    dashboard_data,
    download_table,
    number,
)

data = dashboard_data()
st.header("Comparação inicial de modelos", anchor=False)
st.caption(
    "Brasil · desenvolvimento completo · 3 dobras · semente 42. "
    "Os filtros laterais não se aplicam aos resultados desta página."
)
st.info(
    "O teste de 20% continua reservado. Esta comparação apoia o desenvolvimento; "
    "a seleção e a avaliação final ainda estão pendentes.",
    icon=":material/lock:",
)
metric = st.segmented_control(
    "Métrica de avaliação", ["RMSE", "MAE", "R²"], default="RMSE", key="cv_metric"
)
prefix = {"RMSE": "rmse", "MAE": "mae", "R²": "r2"}.get(metric, "rmse")
cv = data.cv.sort_values(f"{prefix}_mean", ascending=prefix != "r2").copy()
cv["Modelo"] = cv.model.map(MODEL_LABELS).fillna(cv.model)
with st.container(border=True):
    st.subheader(f"{metric or 'RMSE'} na validação cruzada", anchor=False)
    fig = go.Figure(
        go.Bar(
            y=cv.Modelo,
            x=cv[f"{prefix}_mean"],
            orientation="h",
            error_x=dict(type="data", array=cv[f"{prefix}_std"], visible=True, color="#182c40"),
            marker_color=[GRAY if model == "baseline" else TEAL for model in cv.model],
            customdata=cv[[f"{prefix}_std"]].values,
            hovertemplate=(
                "%{y}<br>Média: %{x:.4f}"
                "<br>Desvio entre dobras: %{customdata[0]:.4f}<extra></extra>"
            ),
        )
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title=metric or "RMSE", rangemode="tozero")
    chart(
        base_chart(fig, 310),
        "cv_chart",
        f"Média e desvio padrão de {metric or 'RMSE'} dos quatro modelos",
    )
    st.caption(
        "Barras de erro = ±1 desvio padrão populacional entre as três dobras; "
        "não são intervalos de confiança. RMSE/MAE menores são melhores; R² maior é melhor."
    )

with st.container(horizontal=True, vertical_alignment="distribute"):
    st.metric("Modelos comparados", str(len(cv)), border=True, width=220)
    st.metric("Dobras por modelo", "3", border=True, width=220)
    st.metric("Variáveis de entrada", str(len(data.manifest["features"])), border=True, width=220)
    st.metric(
        "Participantes no desenvolvimento",
        number(data.manifest["n_development"]),
        border=True,
        width=280,
    )

st.markdown(
    "**Linear e Ridge têm desempenho praticamente igual.** A diferença de RMSE "
    "é inferior a 0,001 ponto, menor que a variação entre as dobras. "
    "A referência prevê a média do treino; a árvore foi avaliada com profundidade limitada."
)
results = cv.rename(
    columns={
        "rmse_mean": "RMSE",
        "rmse_std": "Desvio RMSE",
        "mae_mean": "MAE",
        "mae_std": "Desvio MAE",
        "r2_mean": "R²",
        "r2_std": "Desvio R²",
        "elapsed_seconds": "Duração (s)",
    }
)
st.dataframe(
    results[["Modelo", "RMSE", "Desvio RMSE", "MAE", "R²", "Duração (s)"]],
    hide_index=True,
    width="stretch",
    alt="Resultados da validação cruzada por modelo",
    column_config={
        name: st.column_config.NumberColumn(format="%.4f")
        for name in ("RMSE", "Desvio RMSE", "MAE", "R²", "Duração (s)")
    },
)
download_table(
    data.cv, "Baixar resultados completos", "enem_cn_validacao_cruzada.csv", "download_cv"
)

with st.expander("Entender as métricas"):
    st.markdown(
        "**RMSE:** erro quadrático médio em pontos de nota, com maior peso para erros grandes.\n\n"
        "**MAE:** erro absoluto médio em pontos.\n\n"
        "**R²:** proporção da variação capturada em relação à média. Pode ser negativo. "
        "Um R² de 0,243 não significa 24,3% de acertos."
    )
with st.expander("Consultar as três dobras de um modelo", on_change="rerun") as detail:
    if detail.open:
        model = st.selectbox(
            "Modelo", data.cv.model.tolist(), format_func=MODEL_LABELS.get, key="fold_model"
        )
        st.dataframe(
            data.folds.loc[data.folds.model.eq(model)].rename(
                columns={"fold": "Dobra (0–2)", "n_train": "Treino", "n_evaluated": "Validação"}
            ),
            hide_index=True,
            width="stretch",
            alt="Métricas e tamanhos das três dobras do modelo",
        )
