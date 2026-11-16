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
    model_results,
    number,
)

data = dashboard_data()
published = model_results(data)
st.header("Comparação e avaliação dos modelos", anchor=False)
st.caption(
    "Brasil · desenvolvimento completo · 3 dobras · semente 42. "
    "Os filtros laterais não se aplicam aos resultados desta página."
)
if published is None:
    st.info(
        "Esta instalação contém apenas o resumo inicial de desenvolvimento. "
        "Os resultados finais publicados não foram carregados neste painel."
    )
source_cv = published.cv if published is not None else data.cv
source_folds = published.folds if published is not None else data.folds
metric = st.segmented_control(
    "Métrica de avaliação", ["RMSE", "MAE", "R²"], default="RMSE", key="cv_metric"
)
prefix = {"RMSE": "rmse", "MAE": "mae", "R²": "r2"}.get(metric, "rmse")
cv = source_cv.sort_values(f"{prefix}_mean", ascending=prefix != "r2").copy()
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
        base_chart(fig, max(310, len(cv) * 37)),
        "cv_chart",
        f"Média e desvio padrão de {metric or 'RMSE'} dos {len(cv)} modelos/configurações",
    )
    st.caption(
        "Barras de erro = ±1 desvio padrão populacional entre as três dobras; "
        "não são intervalos de confiança. RMSE/MAE menores são melhores; R² maior é melhor."
    )

with st.container(horizontal=True, vertical_alignment="distribute"):
    st.metric("Configurações na CV", str(len(cv)), border=True, width=220)
    st.metric("Dobras por modelo", "3", border=True, width=220)
    st.metric("Variáveis de entrada", str(len(data.manifest["features"])), border=True, width=220)
    st.metric(
        "Participantes no desenvolvimento",
        number(data.manifest["n_development"]),
        border=True,
        width=280,
    )

if published is not None:
    st.markdown(
        "**Três menores RMSE do catálogo completo: Stacking, Ridge e regressão linear.** "
        "No recorte de sete algoritmos, o trio é Stacking, SVM linear e Random Forest. "
        "As buscas cobriram a união dos dois grupos, com cinco modelos e 180 avaliações. "
        "A solução selecionada no desenvolvimento foi o Stacking."
    )
else:
    st.markdown(
        "**Linear e Ridge têm desempenho praticamente igual neste resumo inicial.** "
        "A referência prevê a média do treino; a árvore tem profundidade limitada."
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
download_table(source_cv, "Baixar resultados da CV", "enem_cn_validacao_cruzada.csv", "download_cv")

if published is not None:
    st.subheader("Avaliação final no teste de 20%", anchor=False)
    st.caption(
        f"{number(int(published.test.n_evaluated.iloc[0]))} participantes, "
        "com parâmetros congelados. O teste não participou da escolha dos parâmetros. "
        "Cada linha abaixo é uma avaliação final, sem média ou desvio entre dobras."
    )
    final = published.test.assign(Modelo=lambda frame: frame.model.map(MODEL_LABELS)).rename(
        columns={"rmse": "RMSE", "mae": "MAE", "r2": "R²"}
    )
    st.dataframe(
        final[["Modelo", "RMSE", "MAE", "R²"]],
        hide_index=True,
        width="stretch",
        alt="Resultados finais dos cinco modelos no mesmo teste separado",
        column_config={
            name: st.column_config.NumberColumn(format="%.4f") for name in ("RMSE", "MAE", "R²")
        },
    )
    winner = published.test.loc[published.test.model.eq(published.selected_model)].iloc[0]
    baseline = published.test.loc[published.test.model.eq("baseline")].iloc[0]
    reduction = (1 - winner.rmse / baseline.rmse) * 100
    st.markdown(
        f"**{MODEL_LABELS[published.selected_model]}:** RMSE de "
        f"**{number(winner.rmse, 3)} pontos** no teste e redução de "
        f"**{number(reduction, 2)}%** em relação à média. "
        "Esse foi o menor RMSE observado no teste. Diferenças pequenas entre regressores "
        "não foram submetidas a teste de significância."
    )
    st.caption(
        "Ridge, árvore, KNN, Bagging, Pasting e Boosting têm validação cruzada completa, "
        "mas não previsões no teste final deste protocolo. Não há teste em outro ano do ENEM."
    )
    download_table(
        published.test, "Baixar métricas do teste", "enem_cn_teste_final.csv", "download_test"
    )

with st.expander("Entender as métricas"):
    st.markdown(
        "**RMSE:** raiz do erro quadrático médio em pontos de nota, "
        "com maior peso para erros grandes.\n\n"
        "**MAE:** erro absoluto médio em pontos.\n\n"
        "**R²:** proporção da variação capturada em relação à média. Pode ser negativo. "
        "Um R² de 0,243 não significa 24,3% de acertos."
    )
with st.expander("Consultar as três dobras de um modelo", on_change="rerun") as detail:
    if detail.open:
        model = st.selectbox(
            "Modelo", source_cv.model.tolist(), format_func=MODEL_LABELS.get, key="fold_model"
        )
        st.dataframe(
            source_folds.loc[
                source_folds.model.eq(model),
                ["model", "fold", "rmse", "mae", "r2", "n_train", "n_evaluated"],
            ].rename(
                columns={"fold": "Dobra (0–2)", "n_train": "Treino", "n_evaluated": "Validação"}
            ),
            hide_index=True,
            width="stretch",
            alt="Métricas e tamanhos das três dobras do modelo",
        )
