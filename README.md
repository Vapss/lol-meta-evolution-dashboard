# LoL Meta Evolution Dashboard

Proyecto para analizar la evolución del meta competitivo de League of Legends a través de parches y ligas (solo queue y competiciones profesionales como LCS, LEC, LCK).

## Propósito
Analizar cómo cambian los campeones más usados y su winrate a lo largo de distintos parches, comparando solo queue y ligas profesionales.

## Estructura del proyecto

```
lol-meta-evolution-dashboard/
├── data/
│   ├── raw/
│   ├── processed/
│   └── examples/
├── notebooks/
│   └── exploration.ipynb
├── src/
│   ├── data_collection.py
│   ├── data_cleaning.py
│   ├── analysis.py
│   ├── visualization.py
│   └── dashboard.py
├── tests/
│   ├── test_data_cleaning.py
│   └── test_analysis.py
├── requirements.txt
├── README.md
├── .gitignore
└── copilot-instructions.md
```

## Stack
- Python 3.10+
- pandas, numpy, requests, plotly, streamlit, scikit-learn, tqdm
- pytest para testing

## Configuración rápida
1. Crear y activar un entorno virtual (venv/conda).
2. Instalar dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Recolección de datos (Riot API)
- Usar variables de entorno para la API key (por ejemplo, `RIOT_API_KEY`).
- Guardar respuestas crudas en `data/raw/`.
- No subir claves ni tokens al repositorio.

## Ejecución rápida
- Para ejecutar la app Streamlit (cuando esté lista):

```powershell
streamlit run src\dashboard.py
```

## Contribuir
- Abrir issues o PRs con cambios pequeños.
- Mantener datos grandes fuera del repo (ej. subir a almacenamiento externo).
