"""Barreiras comuns às cinco possibilidades de alvo do enunciado."""

ENEM_TARGETS = (
    "NU_NOTA_MT",
    "NU_NOTA_CN",
    "NU_NOTA_CH",
    "NU_NOTA_LC",
    "NU_NOTA_REDACAO",
)


def validate_features(columns: list[str], *, identifier: str, target: str | None = None) -> None:
    if len(columns) != len(set(columns)) or not columns:
        raise ValueError("Declare uma lista de features não vazia e sem repetições.")
    forbidden = []
    for column in columns:
        key = column.upper()
        if (
            column in {identifier, target}
            or key in {"NU_INSCRICAO", "NU_ANO", "TP_STATUS_REDACAO"}
            or key.startswith(
                (
                    "NU_NOTA_",
                    "TX_RESPOSTAS_",
                    "TX_GABARITO_",
                    "TP_PRESENCA_",
                    "CO_PROVA_",
                )
            )
        ):
            forbidden.append(column)
    if forbidden:
        raise ValueError(f"Features bloqueadas por controle ou risco de vazamento: {forbidden}")


def require_target(target: str | None, *, kind: str) -> str:
    if not target:
        raise ValueError("O alvo ainda não foi definido. Registre a escolha antes desta etapa.")
    if kind not in {"synthetic", "enem2023"}:
        raise ValueError("Tipo de fonte desconhecido.")
    if kind == "enem2023" and target not in ENEM_TARGETS:
        raise ValueError("O alvo deve ser uma das cinco notas previstas no enunciado.")
    return target
