import pandas as pd
from src.data_cleaning import clean_match_dataframe


def test_clean_match_dataframe_minimal():
    df = pd.DataFrame({
        'champion': ['Aatrox', None, 'Ahri'],
        'patch': ['13.1', '13.1', None],
        'player_tier': ['GOLD','SILVER','PLATINUM'],
        'result': [1, 0, 1]
    })

    cleaned = clean_match_dataframe(df)
    # Aseguramos que no queden filas sin champion o patch
    assert cleaned['champion'].notna().all()
    assert cleaned['patch'].notna().all()
