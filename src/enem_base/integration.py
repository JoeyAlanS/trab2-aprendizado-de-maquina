"""Junção opcional de indicadores de 2023 com cardinalidade controlada."""

import pandas as pd


def merge_context(
    participants: pd.DataFrame,
    context: pd.DataFrame,
    *,
    key: str,
    source: str,
    reference_year: int,
    geography: str,
) -> tuple[pd.DataFrame, dict]:
    if reference_year != 2023 or not source.strip() or not geography.strip():
        raise ValueError("Declare fonte, significado territorial e referência 2023.")
    if context[key].isna().any() or context[key].duplicated().any():
        raise ValueError("A tabela externa exige chave única e não ausente.")
    if participants[key].dtype != context[key].dtype:
        raise ValueError("Normalize os tipos das chaves explicitamente antes da junção.")
    overlap = set(participants).intersection(context) - {key}
    if overlap or "_merge" in participants or "_merge" in context:
        raise ValueError(f"Colunas ambíguas ou reservadas na junção: {sorted(overlap)}")
    merged = participants.merge(context, on=key, how="left", validate="many_to_one", indicator=True)
    matched = int(merged["_merge"].eq("both").sum())
    return merged.drop(columns="_merge"), {
        "source": source,
        "reference_year": reference_year,
        "geography": geography,
        "key": key,
        "rows_before": len(participants),
        "rows_after": len(merged),
        "matched_rows": matched,
        "unmatched_rows": len(merged) - matched,
        "coverage": matched / len(merged) if len(merged) else None,
    }
