"""Produzir relatório Markdown somente a partir da avaliação final validada."""

import argparse
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from publicar_checkpoint4 import LABELS

from enem_base.evidence import read_run
from enem_base.final_evaluation import validate_final_results
from enem_base.final_selection import load_frozen
from enem_base.provenance import verify_sha256
from enem_base.search_cache import read_json
from enem_base.study import load_study


def number(value, precision=3):
    return f"{value:,.{precision}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def report(config, root, publication, output):
    if output.exists():
        raise FileExistsError("Relatório existente: preservar ou indicar outra saída.")
    frozen = load_frozen(config, root)
    metrics = validate_final_results(config, root).set_index("model")
    manifest = read_run(root / "avaliacao_final", frozen, development=False)
    published = read_run(publication, frozen, development=False)
    visual = root / "validacao_visual_teste.json"
    if published.get("visual_validation_pending") is not False:
        raise ValueError("Conferir os gráficos antes de publicar o relatório final.")
    verify_sha256(visual, published["visual_validation_sha256"], "Revisão visual alterada")
    if read_json(visual).get("status") != "passed":
        raise ValueError("Revisão visual não aprovada.")
    split = read_json(config.splits / "manifesto.json")
    groups = pd.read_csv(
        root / "avaliacao_final" / "erros_grupos.csv", dtype={"category": "string"}
    )
    winner = manifest["primary_observed_winner"]
    academic = frozen["academic_solution"]
    primary = frozen["primary_models"]
    ranking = metrics.loc[primary].sort_values(["rmse", "mae", "r2"], ascending=[True, True, False])
    chosen = metrics.loc[winner]
    baseline = metrics.loc["baseline"]
    reduction = 100 * (1 - chosen.rmse / baseline.rmse)
    day = datetime.now(ZoneInfo("America/Fortaleza")).strftime("%d/%m/%Y")

    def link(path):
        return Path(os.path.relpath(path, output.parent)).as_posix()

    lines = [
        "# Checkpoint 4 — avaliação final nacional",
        "",
        f"Resultados executados e validados em {day}. Alvo: nota de Ciências da Natureza "
        "(NU_NOTA_CN), ENEM 2023. As buscas, as curvas finais e os pesos foram fixados "
        "antes de abrir o teste. Não houve nova escolha de hiperparâmetros após o teste.",
        "",
        f"**{LABELS[winner]} teve o menor RMSE entre os três algoritmos selecionados no teste:** "
        f"{number(chosen.rmse)} pontos. A solução acadêmica escolhida anteriormente no "
        f"desenvolvimento é {LABELS[academic]}. A ordenação de teste descreve esta divisão; "
        "não é uma demonstração de superioridade universal ou significância estatística.",
        "",
        "## Dados e protocolo efetivamente usados",
        "",
        f"A fonte recuperada contém {number(split['source_rows'], 0)} participantes. "
        f"Foram excluídos da supervisão {number(split['missing_target'], 0)} sem a nota alvo, "
        f"mantendo {number(split['eligible'], 0)} elegíveis. Notas ausentes não viraram zero.",
        f"O desenvolvimento teve **{number(split['development'], 0)} participantes** e o teste "
        f"reservado, **{number(split['test'], 0)}**. O teste inclui "
        f"{number(manifest['zero_observed_scores'], 0)} notas zero, mantidas na avaliação.",
        "",
        "Foram preservados a divisão 80/20 com semente 42, as três dobras e os IDs "
        "persistidos. Os três modelos e a linear usam as 40 entradas originais de perfil "
        "e questionário. IDs, outras notas, respostas, gabaritos e presença não entram "
        "nos preditores. O baseline aprende somente a média do alvo no desenvolvimento.",
        "",
        "Cada pipeline foi reajustado nos 80% completos antes de carregar o teste. "
        "Todos os modelos previram os mesmos participantes, sem amostragem e sem "
        "limitar artificialmente as previsões à faixa das notas. Uma trava persistente "
        "permite apenas retomar os mesmos pesos e a mesma identidade da avaliação.",
        "",
        "## Pendências metodológicas resolvidas",
        "",
        "- Cinco buscas reais cobriram a união do trio solicitado e do trio do catálogo "
        "ampliado: 60 configurações, 180 avaliações nacionais e zero avisos. "
        "[Resultados e interpretação](checkpoint-4-buscas.md).",
        "- A seleção comparou originais, buscas e variantes obrigatórias, sem usar o teste.",
        "- As curvas das receitas congeladas foram concluídas: 45 pontos, zero avisos e "
        "reprodução da validação em 100%. [Análise e gráficos](checkpoint-4-curvas.md).",
        "- O fluxo agora avalia o trio, o baseline e a linear de referência, com pesos "
        "persistidos e retomada verificada. A solução acadêmica coincide com um dos três, "
        "portanto não foi duplicada como outro modelo.",
        "",
        "## Métricas no teste",
        "",
        "| Modelo | RMSE ↓ | MAE ↓ | R² ↑ | Treino (s) | Previsão (s) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, row in metrics.iterrows():
        lines.append(
            f"| {LABELS[name]} | {number(row.rmse)} | {number(row.mae)} | "
            f"{number(row.r2, 6)} | {number(row.fit_seconds, 2)} | "
            f"{number(row.prediction_seconds, 2)} |"
        )
    lines.extend(
        [
            "",
            "RMSE e MAE estão em pontos; R² é adimensional. Os tempos são de parede "
            "observados sob compartilhamento de recursos, não um benchmark isolado.",
            f"O vencedor do trio reduziu o RMSE em {number(baseline.rmse - chosen.rmse)} pontos "
            f"({number(reduction, 2)}%) frente ao baseline nesta divisão.",
            "",
            "## Validação cruzada e teste",
            "",
            "| Modelo | RMSE médio CV | RMSE teste | Teste − CV |",
            "|---|---:|---:|---:|",
        ]
    )
    for name in ranking.index:
        cv = frozen["recipes"][name]["rmse_mean"]
        test = metrics.loc[name, "rmse"]
        lines.append(f"| {LABELS[name]} | {number(cv)} | {number(test)} | {number(test - cv)} |")
    ahead = [
        LABELS[n]
        for n in primary
        if metrics.loc["linear_reference", "rmse"] < metrics.loc[n, "rmse"]
    ]
    if ahead:
        lines.extend(
            [
                "",
                "A linear de referência teve RMSE menor que "
                + ", ".join(ahead)
                + ". Isso reforça a importância de manter as referências: o ranking do trio "
                "solicitado não é o mesmo que o ranking de todo o catálogo.",
            ]
        )
    lines.extend(
        [
            "",
            "A comparação de CV usa treino de aproximadamente 1,436 milhão por dobra; "
            "o teste usa modelos reajustados em 2,154 milhões. Diferenças entre CV e teste "
            "também refletem composição da partição e tamanho de treino. Não foram calculados "
            "intervalos de confiança nem testes de significância para essas diferenças.",
            "",
            "## Erros por faixa e por grupo",
            "",
            f"A tabela apresenta os erros de {LABELS[winner]}. "
            "Resíduo = nota observada − prevista; "
            "resíduo médio positivo indica subestimação média, e negativo, superestimação.",
            "",
            "| Faixa observada | Participantes | RMSE | MAE | Resíduo médio |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    bands = groups.loc[groups.model.eq(winner) & groups.group.eq("faixa_nota")].sort_values(
        "category"
    )
    for row in bands.itertuples():
        lines.append(
            f"| {row.category} | {number(row.n, 0)} | {number(row.rmse)} | "
            f"{number(row.mae)} | {number(row.mean_residual)} |"
        )
    by_band = bands.set_index("category")
    low, high = by_band.loc["[0,400)"], by_band.loc["[700,+inf)"]
    lines.extend(
        [
            "",
            f"Na faixa abaixo de 400, o resíduo médio foi {number(low.mean_residual)} pontos; "
            f"na faixa a partir de 700, foi {number(high.mean_residual)}. "
            f"Os RMSE dessas faixas foram {number(low.rmse)} e {number(high.rmse)}, "
            f"respectivamente, frente ao RMSE global de {number(chosen.rmse)}. "
            "A média global, portanto, oculta erros maiores nos extremos; o desempenho "
            "não é uniforme entre as faixas de nota.",
        ]
    )
    lines.extend(
        [
            "",
            "Também foram calculados erros por tipo de escola (TP_ESCOLA), UF de aplicação "
            "(SG_UF_PROVA) e renda familiar (Q006), com contagens. Cada estratificação cobre "
            "todo o teste. Os grupos são observacionais; diferenças não demonstram causalidade "
            "nem determinam a capacidade individual dos participantes.",
            "",
            "## Gráficos",
            "",
        ]
    )
    for stem, title in [
        ("comparacao_teste", "Comparação do teste"),
        ("validacao_versus_teste", "Validação e teste"),
        ("observado_versus_previsto", "Observado versus previsto"),
        ("distribuicao_residuos", "Distribuição dos resíduos"),
        ("erros_faixa_nota", "Erros por faixa de nota"),
    ]:
        lines.extend([f"![{title}]({link(publication / (stem + '.png'))})", ""])
    lines.extend(
        [
            "Os gráficos usam todos os participantes avaliados e estão disponíveis em PNG "
            "de 300 dpi e SVG. As densidades de observado versus previsto compartilham "
            "os mesmos limites, células e escala de cores. Por se tratar de regressão, "
            "foram usados resíduos e erros por faixa/grupo em vez de matrizes de confusão.",
            "",
            "## Limites e análise crítica",
            "",
            "As curvas finais apresentam gaps pequenos entre treino e validação, sem sinal "
            "de sobreajuste acentuado nas configurações avaliadas. O erro remanescente e "
            "o R² não comprovam, isoladamente, subajuste: o perfil disponível não contém "
            "toda a informação relacionada ao desempenho. As buscas trouxeram mudanças "
            "muito pequenas; o ajuste do alpha do Stacking não demonstrou ganho prático.",
            "",
            "A avaliação cobre o ENEM 2023 elegível em uma divisão aleatória nacional. "
            "Não demonstra generalização temporal para outro ENEM nem para populações "
            "externas. Uma única partição de teste não mede toda a incerteza da comparação.",
            "",
            "A base limpa SQLite e os 79 Parquets foram conferidos por hashes e preservados. "
            "O CSV bruto e o ZIP original continuam ausentes nesta cópia; a recuperação "
            "usa o banco previamente validado. Essa limitação de proveniência documental "
            "permanece explícita, sem inventar um novo arquivo bruto.",
            "",
            "## Código, evidências e reprodução",
            "",
        ]
    )
    for path, title in [
        (root / "avaliacao_final" / "previsoes_teste.csv", "Previsões reais de todos os modelos"),
        (
            root / "avaliacao_final" / "experimentos.csv",
            "Métricas finais, parâmetros e proveniência",
        ),
        (root / "avaliacao_final" / "erros_grupos.csv", "Todos os erros por grupo e contagens"),
        (root / "congelamento" / "receitas.json", "Receitas fixadas antes do teste"),
        (root / "validacao_teste.json", "Validação das previsões e recomposição das métricas"),
        (root / "validacao_visual_teste.json", "Revisão visual da publicação"),
        (publication, "Todos os gráficos e tabelas finais"),
    ]:
        lines.append(f"- [{title}]({link(path)}).")
    lines.extend(
        [
            "",
            "Executores: [buscas](../scripts/executar_buscas_checkpoint4.py), "
            "[congelamento/curvas/ajustes/teste](../scripts/executar_checkpoint4.py) e "
            "[publicação final](../scripts/publicar_checkpoint4.py). Os comandos e critérios "
            "estão no [protocolo](checkpoint-4-protocolo.md).",
            "",
            "Foram executadas verificações de integridade, cobertura e métricas sobre os "
            "dados reais, além de lint, compilação e conferência do ambiente. Não foram "
            "criados arquivos de testes automatizados ou resultados fictícios. Os arquivos "
            "dos Checkpoints 1–3 permanecem preservados; as 72 linhas do consolidado inicial "
            "não foram misturadas com as buscas e curvas. Os resultados finais estão "
            "identificados separadamente como `test_final`.",
            "",
            "## Próximos checkpoints",
            "",
            "O próximo passo é o Checkpoint 5: organizar a coleção final de visualizações "
            "e sua integração aos entregáveis. Depois vêm o artigo ABNT (Checkpoint 6) "
            "e os PDFs de acompanhamento e pitch (Checkpoint 7). Esses entregáveis ainda "
            "não são declarados concluídos. Não houve commit, push ou publicação externa.",
            "",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--publication", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report(load_study(args.study), args.checkpoint, args.publication, args.output)
