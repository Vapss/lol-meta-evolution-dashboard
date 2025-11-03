import pandas as pd
from src.analysis import calcular_winrate


def test_calcular_winrate_basic():
    df = pd.DataFrame({
        'champion': ['Aatrox','Aatrox','Ahri'],
        'patch': ['13.1','13.1','13.1'],
        'result': [1,0,1]
    })
    wr = calcular_winrate(df)
    aatrox = wr[(wr['champion']=='Aatrox') & (wr['patch']=='13.1')]
    assert float(aatrox['win_rate']) == 0.5

