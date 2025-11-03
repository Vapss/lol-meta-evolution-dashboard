"""Funciones para generar gráficos interactivos con plotly."""
from __future__ import annotations
import plotly.express as px
import pandas as pd


def grafico_winrate_por_parche(df: pd.DataFrame, top_n: int = 10):
    """
    Genera un gráfico de líneas con el winrate por parche para los top_n campeones.

    Args:
        df (pd.DataFrame): DataFrame con columnas ['champion','patch','win_rate','games_played'].
        top_n (int): Número de campeones a mostrar por frecuencia.

    Returns:
        plotly.graph_objects.Figure
    """
    # Seleccionar top_n por games_played total
    totals = df.groupby('champion')['games_played'].sum().nlargest(top_n).index
    subset = df[df['champion'].isin(totals)]
    fig = px.line(subset, x='patch', y='win_rate', color='champion', markers=True,
                  title=f'Winrate por parche (Top {top_n} por partidas)')
    fig.update_layout(template='simple_white')
    return fig
