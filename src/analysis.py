"""Cálculo de métricas: pick rate, win rate y agregaciones por parche y liga."""
from __future__ import annotations
import pandas as pd


def calcular_winrate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el winrate por campeón y parche.

    Args:
        df (pd.DataFrame): DataFrame con columnas ['champion', 'patch', 'result'] donde 'result' es 1 para victoria y 0 para derrota.

    Returns:
        pd.DataFrame: Tabla con columnas ['champion', 'patch', 'win_rate', 'games_played'].
    """
    grouped = df.groupby(["champion", "patch"])['result'].agg(['sum', 'count']).reset_index()
    grouped = grouped.rename(columns={'sum': 'wins', 'count': 'games_played'})
    grouped['win_rate'] = grouped['wins'] / grouped['games_played']
    return grouped[['champion', 'patch', 'win_rate', 'games_played']]


# TODO: funciones para pick rate y comparaciones entre ligas
