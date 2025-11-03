"""Funciones para limpiar y normalizar datos recolectados.

Incluye manejo de NaNs, transformación de tipos y export a `data/processed/`.
"""
from __future__ import annotations
import pandas as pd
from typing import Tuple


def clean_match_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia un DataFrame de partidas (ejemplo).

    Args:
        df (pd.DataFrame): DataFrame crudo con datos de partidas.

    Returns:
        pd.DataFrame: DataFrame limpio y normalizado.
    """
    # Ejemplo: asegurar columnas mínimas
    expected_cols = ["champion", "patch", "player_tier", "result"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = pd.NA

    # Normalizaciones básicas
    df["patch"] = df["patch"].astype(str)
    df = df.dropna(subset=["champion", "patch"], how="any")

    return df


# TODO: Añadir funciones para transformar formatos provenientes de distintas fuentes
