"""Catálogo completo de relações descritivas e relatório técnico em PDF."""

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from enem_base.dashboard import MISSING
from enem_base.dashboard_ui import (
    GRAY,
    PROJECT_ROOT,
    TEAL,
    base_chart,
    category_label,
    chart,
    dashboard_data,
    download_table,
    number,
    relations_data,
)
from enem_base.relations import LABELS, pair_cells

data = dashboard_data()
st.header("Relações e relatório", anchor=False)
st.caption(
    "Desenvolvimento completo · filtros laterais não se aplicam a esta página. "
    "As relações são descritivas e não estabelecem causalidade."
)
try:
    relations = relations_data(data)
except (OSError, ValueError, KeyError) as error:
    st.warning("As análises de relações ainda não estão disponíveis ou não correspondem ao painel.")
    st.code(
        "python -m enem_base relations --study configs/ciencias_natureza.toml "
        "--output resultados/ciencias_natureza/relacoes-v1",
        language="powershell",
    )
    st.caption(str(error))
    st.stop()

with st.container(horizontal=True):
    st.metric(
        "Variáveis relacionadas à nota",
        str(relations.manifest["n_variables"]),
        border=True,
        width=260,
    )
    st.metric(
        "Pares de variáveis analisados", str(relations.manifest["n_pairs"]), border=True, width=260
    )
    st.metric(
        "Participantes no desenvolvimento",
        number(relations.manifest["n_development"]),
        border=True,
        width=285,
    )

mode = (
    st.segmented_control(
        "Análise",
        [
            "Relações com a nota",
            "Cruzamentos de perfis",
            "Associações entre entradas",
            "Relatório PDF",
        ],
        default="Relações com a nota",
        key="relations_mode",
    )
    or "Relações com a nota"
)
features = relations.manifest["features"]


def field_label(name: str) -> str:
    return f"{name} · {LABELS.get(name, name)}"


def ordered_codes(codes: list[str]) -> list[str]:
    return sorted(
        codes,
        key=lambda code: (
            code == MISSING,
            not code.isdecimal(),
            int(code) if code.isdecimal() else code,
        ),
    )


if mode == "Relações com a nota":
    field = st.selectbox(
        "Variável de perfil",
        features,
        index=features.index("Q006") if "Q006" in features else 0,
        format_func=field_label,
        key="relation_field",
    )
    st.markdown(data.dictionary["columns"][field]["description"])
    profile = relations.profiles.loc[relations.profiles.variable.eq(field)].copy()
    minimum = st.number_input(
        "Mínimo de participantes no gráfico",
        min_value=1,
        max_value=3000000,
        value=30,
        key="relation_minimum",
    )
    selected = profile.loc[profile.n.ge(minimum)].copy()
    selected = (
        selected.set_index("code").reindex(ordered_codes(selected.code.tolist())).reset_index()
    )
    selected["display"] = selected.code + " · " + selected.label.str.slice(0, 65)
    if not selected.empty:
        fig = go.Figure(
            go.Bar(
                y=selected.display,
                x=selected["mean"],
                orientation="h",
                marker_color=[GRAY if code == MISSING else TEAL for code in selected.code],
                customdata=selected[["n", "std", "zeros"]].to_numpy(),
                hovertemplate=(
                    "%{y}<br>Média: %{x:.2f}<br>n: %{customdata[0]:,.0f}"
                    "<br>Desvio: %{customdata[1]:.2f}"
                    "<br>Zeros: %{customdata[2]:,.0f}<extra></extra>"
                ),
            )
        )
        fig.update_xaxes(title="Nota média de Ciências da Natureza", rangemode="tozero")
        fig.update_yaxes(autorange="reversed")
        chart(
            base_chart(fig, max(330, len(selected) * 29)),
            "relation_profile",
            f"Nota média por alternativa de {LABELS.get(field, field)}, com contagens",
        )
    else:
        st.info("Nenhum grupo atende ao mínimo escolhido. Reduza o limite para visualizar.")
    row = relations.target.set_index("variable").loc[field]
    st.caption(
        f"Eta² entre grupos observados: {number(row.eta_squared, 4)} · "
        f"Cobertura: {number(row.n_observed)} de {number(row.n)} participantes."
    )
    if field in relations.manifest["numeric_features"]:
        st.caption(
            f"Pearson: {number(row.pearson, 4)} · Spearman: {number(row.spearman, 4)}. "
            "Somente a entrada numérica recebe essas correlações."
        )
    st.caption(
        "Eta² mede diferenças entre médias de grupos; não é R² de previsão. "
        "Ausências não entram no efeito principal e aparecem como grupo próprio na tabela. "
        "O mínimo limita apenas o gráfico; a tabela preserva todos os grupos."
    )
    st.dataframe(
        profile.rename(
            columns={
                "code": "Código",
                "label": "Alternativa",
                "n": "Participantes",
                "mean": "Nota média",
                "std": "Desvio",
                "zeros": "Zeros",
            }
        ),
        hide_index=True,
        width="stretch",
        alt="Estatísticas de todas as alternativas da variável selecionada",
    )
    download_table(
        profile, "Baixar perfil desta variável", f"perfil_{field}.csv", "download_profile"
    )
    with st.expander("Comparação das 40 entradas com a nota", on_change="rerun") as detail:
        if detail.open:
            st.dataframe(
                relations.target.sort_values("eta_squared", ascending=False),
                hide_index=True,
                width="stretch",
                alt="Todas as entradas, efeito Eta², cobertura e sensibilidade a ausências",
            )
    download_table(
        relations.target,
        "Baixar todas as relações com a nota",
        "relacoes_nota_cn.csv",
        "download_target_relations",
    )

elif mode == "Cruzamentos de perfis":
    a = st.selectbox(
        "Primeira variável",
        features,
        index=features.index("Q006") if "Q006" in features else 0,
        format_func=field_label,
        key="joint_a",
    )
    options = [field for field in features if field != a]
    b = st.selectbox(
        "Segunda variável",
        options,
        index=options.index("TP_ESCOLA") if "TP_ESCOLA" in options else 0,
        format_func=field_label,
        key="joint_b",
    )
    indicator = st.segmented_control(
        "Valor nas células",
        ["Nota média", "Participantes"],
        default="Nota média",
        key="joint_indicator",
    )
    minimum = st.number_input(
        "Mínimo de participantes por célula no gráfico", 1, 3000000, 30, key="joint_minimum"
    )
    cells = pair_cells(relations, a, b)
    column = "n" if indicator == "Participantes" else "mean"
    cells["visible_value"] = cells[column].where(cells.n.ge(minimum))
    rows, columns = (
        ordered_codes(cells.code_a.unique().tolist()),
        ordered_codes(cells.code_b.unique().tolist()),
    )
    z = cells.pivot(index="code_a", columns="code_b", values="visible_value").reindex(
        index=rows, columns=columns
    )
    counts = cells.pivot(index="code_a", columns="code_b", values="n").reindex(
        index=rows, columns=columns
    )
    fig = go.Figure(
        go.Heatmap(
            z=z.to_numpy(),
            x=columns,
            y=rows,
            customdata=counts.to_numpy(),
            colorscale="Teal",
            colorbar=dict(title=indicator or "Nota média"),
            hovertemplate=(
                f"{a}: %{{y}}<br>{b}: %{{x}}<br>Valor: %{{z:.2f}}"
                "<br>n: %{customdata:,.0f}<extra></extra>"
            ),
        )
    )
    fig.update_xaxes(title=field_label(b), type="category")
    fig.update_yaxes(title=field_label(a), type="category", autorange="reversed")
    chart(
        base_chart(fig, max(440, len(rows) * 26)),
        "joint_heatmap",
        f"{indicator or 'Nota média'} no cruzamento de {a} com {b}",
    )
    st.caption(
        "Células vazias não existem no recorte ou têm menos participantes que o mínimo. "
        "O cruzamento inteiro usa somente desenvolvimento. Categorias ausentes são mantidas."
    )
    export = cells.drop(columns="visible_value")
    export["label_a"] = export.code_a.map(lambda code: category_label(data, a, code))
    export["label_b"] = export.code_b.map(lambda code: category_label(data, b, code))
    st.dataframe(
        export,
        hide_index=True,
        width="stretch",
        alt="Todas as células do cruzamento com códigos, rótulos e contagens",
    )
    download_table(
        export, "Baixar cruzamento completo", f"cruzamento_{a}_{b}.csv", "download_joint"
    )

elif mode == "Associações entre entradas":
    st.markdown(
        "**V de Cramér** mede associação entre variáveis categóricas (0 a 1, sem direção). "
        "Nos pares com Q005, **Eta²** mede a variação de pessoas na residência entre grupos. "
        "As duas medidas têm interpretações diferentes e não formam um ranking único."
    )
    categorical = [name for name in features if name not in relations.manifest["numeric_features"]]
    preferred = [
        name
        for name in (
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
        )
        if name in categorical
    ]
    selected = st.multiselect(
        "Variáveis na matriz categórica",
        categorical,
        default=preferred,
        format_func=field_label,
        key="association_variables",
    )
    selected = selected or categorical
    matrix = pd.DataFrame(np.nan, index=selected, columns=selected)
    for row in relations.pairs.loc[relations.pairs.metric.eq("cramers_v")].itertuples():
        if row.variable_a in selected and row.variable_b in selected:
            matrix.loc[row.variable_a, row.variable_b] = row.value
            matrix.loc[row.variable_b, row.variable_a] = row.value
    fig = go.Figure(
        go.Heatmap(
            z=matrix.to_numpy(),
            x=selected,
            y=selected,
            zmin=0,
            zmax=1,
            colorscale="Teal",
            colorbar=dict(title="V de Cramér"),
            hovertemplate="%{y} × %{x}<br>V: %{z:.4f}<extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed")
    chart(
        base_chart(fig, max(480, len(selected) * 23)),
        "associations_heatmap",
        "Matriz de associação V de Cramér entre as variáveis categóricas selecionadas",
    )
    st.caption(
        "Sem seleção, a matriz mostra todas as categóricas. Diagonal omitida. "
        "Efeitos principais usam pares observados; cobertura e versão com ausências estão no CSV."
    )
    metric = st.selectbox(
        "Medida na tabela",
        ["cramers_v", "eta_squared"],
        format_func=lambda x: (
            "V de Cramér · categóricas"
            if x == "cramers_v"
            else "Eta² · entrada numérica por categoria"
        ),
        key="pair_metric",
    )
    table = relations.pairs.loc[relations.pairs.metric.eq(metric)].sort_values(
        "value", ascending=False
    )
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        alt="Associações entre entradas com medida e cobertura de cada par",
    )
    download_table(
        relations.pairs,
        "Baixar os 780 pares completos",
        "associacoes_entradas.csv",
        "download_pairs",
    )

else:
    st.subheader("Relatório técnico em LaTeX", anchor=False)
    st.markdown(
        "O relatório documenta a origem dos dados, limpeza, partições, "
        "varredura das relações, resultados iniciais dos modelos, funcionamento do frontend "
        "e limites do estudo. O teste permanece reservado."
    )
    pdf = PROJECT_ROOT / "output/pdf/relatorio_ciencias_natureza.pdf"
    if pdf.exists():
        st.download_button(
            "Baixar relatório em PDF",
            pdf.read_bytes(),
            file_name=pdf.name,
            mime="application/pdf",
            icon=":material/picture_as_pdf:",
            on_click="ignore",
            key="download_report",
        )
        st.caption("Fonte editável e figuras na pasta relatorio/ do projeto.")
    else:
        st.info(
            "Relatório em geração. "
            "As análises completas já podem ser consultadas nas outras opções."
        )
    package = BytesIO()
    # Reexportar os DataFrames já validados, sem consultar linhas de participantes.
    with ZipFile(package, "w", compression=ZIP_DEFLATED) as archive:
        for name, frame in (
            ("alvo.csv", relations.target),
            ("pares.csv", relations.pairs),
            ("perfis.csv", relations.profiles),
            ("cruzamentos.csv", relations.cells),
        ):
            archive.writestr(
                name, frame.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
            )
        archive.writestr(
            "LEIA-ME.txt",
            "Somente desenvolvimento. Teste reservado. "
            "Efeitos principais excluem ausências por par; perfis e cruzamentos as preservam. "
            "Códigos seguem o dicionário oficial ENEM 2023. Separador ; e decimal vírgula.",
        )
    st.download_button(
        "Baixar todas as tabelas (ZIP)",
        package.getvalue(),
        file_name="relacoes_enem_cn.zip",
        mime="application/zip",
        icon=":material/download:",
        on_click="ignore",
        key="download_relations_zip",
    )
