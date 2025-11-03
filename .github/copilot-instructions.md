# Copilot Instructions — LoL Meta Evolution Dashboard

## Arquitectura del Proyecto

Este proyecto analiza la evolución del meta de League of Legends comparando solo queue y competiciones profesionales a través de parches. La arquitectura sigue un pipeline ETL:

1. **Recolección** (`src/data_collection.py`) → `data/raw/` (JSON)
2. **Limpieza** (`src/data_cleaning.py`) → `data/processed/` (CSV/Parquet)
3. **Análisis** (`src/analysis.py`) → métricas agregadas
4. **Visualización** (`src/visualization.py` + `src/dashboard.py`) → Streamlit dashboard

**Data Dragon Integration**: El proyecto usa Data Dragon (https://ddragon.leagueoflegends.com) para traducir IDs de campeones a nombres. Siempre obtener la versión más reciente y usar datos en español (`es_MX`).

## Riot API: Patrones Específicos

### APIs Principales en Uso
- **Account-V1**: Obtener PUUID desde Riot ID (`/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}`)
- **Match-V5**: Historial y detalles de partidas (usa REGION: americas/europe/asia)
- **League-V4**: Rankings y ligas (usa PLATFORM: la1/na1/euw1/kr)
- **Champion-Mastery-V4**: Estadísticas de maestría por PUUID

### Convención de Regiones
```python
REGION = "americas"   # Para Match-V5, Account-V1
PLATFORM = "la1"      # Para League-V4, Summoner-V4, Champion-Mastery-V4
```

**IMPORTANTE**: Match-V5 y Account-V1 usan routing regional (americas/europe/asia), mientras que otras APIs usan plataformas específicas (la1/na1/euw1).

### Autenticación
Todas las llamadas usan header `X-Riot-Token` con la API key desde `.env`:
```python
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('RIOT_API_KEY')
headers = {"X-Riot-Token": API_KEY}
```

**NUNCA** hacer commit de `.env` (ya está en `.gitignore`). Usar `.env.example` para documentar variables necesarias. y no uses emojis

## Estilo de Código

### Type Hints Obligatorios
```python
def fetch_match_data(endpoint_url: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Docstring estilo Google."""
```

### Docstrings Estilo Google
Todas las funciones públicas requieren:
```python
"""
Descripción breve.

Args:
    param1 (tipo): Descripción.

Returns:
    tipo: Descripción.

Notes:
    Información adicional relevante.
"""
```

### Nombres Explícitos
- ✅ `champion_winrate_df`, `match_ids`, `puuid`
- ❌ `df`, `data`, `temp`, `x`

### Imports
Usar `from __future__ import annotations` para type hints modernos en Python 3.10+.

## Notebooks: Convenciones

- **Celdas Markdown**: Usar `##` o `###` para títulos de sección
- **Exploración**: Notebooks en `notebooks/` son para exploración, NO para producción
- **Variables de Entorno**: Siempre cargar `.env` en la primera celda de código:
  ```python
  from dotenv import load_dotenv
  load_dotenv()
  ```
- **Data Dragon**: Cachear `champion_names` dict para evitar múltiples llamadas
- **Visualización**: Preferir `print(json.dumps(data, indent=2)[:N])` para inspeccionar JSON grandes

## Comandos Clave

### Configuración Inicial (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Ejecutar Dashboard
```powershell
streamlit run src\dashboard.py
```

### Testing
```powershell
pytest tests/
```

## Manejo de Datos

### Estructura de Directorios
- `data/raw/`: JSON crudos de Riot API (ignorados en git si son grandes)
- `data/processed/`: CSVs/Parquet limpios y normalizados
- `data/examples/`: Datasets de ejemplo para testing (SÍ incluir en git)

### Guardado de Respuestas
```python
import json
response_data = fetch_match_data(url)
with open(f"data/raw/matches_{match_id}.json", "w") as f:
    json.dump(response_data, f, indent=2)
```

## Patrones de Error Comunes

### KeyError con Summoner ID
Las APIs modernas usan `puuid` en lugar de `summonerId`. Verificar estructura de respuesta antes de acceder:
```python
if 'puuid' in account_info:
    puuid = account_info['puuid']
```

### Rate Limiting
Riot API tiene límites estrictos. Implementar retry logic con exponential backoff:
```python
import time
from requests.exceptions import HTTPError

for attempt in range(3):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        break
    except HTTPError as e:
        if e.response.status_code == 429:
            time.sleep(2 ** attempt)
```

## Visualización con Plotly

Configuración estándar:
```python
fig.update_layout(
    template='simple_white',  # Fondo blanco minimalista
    title={'font': {'size': 16}},
    xaxis_title="Parche",
    yaxis_title="Win Rate (%)"
)
```

## Dependencias Externas

- **Riot API**: Requiere key personal (registro en https://developer.riotgames.com)
- **Data Dragon**: CDN público, no requiere autenticación
- **Python**: 3.10+ para type hints modernos (`|` en lugar de `Union`)

## Workflows Específicos

### Flujo Completo: Analizar Jugador
1. Obtener PUUID con Account-V1 (`by-riot-id`)
2. Obtener maestría con Champion-Mastery-V4 (por PUUID)
3. Obtener match IDs con Match-V5 (por PUUID)
4. Fetch detalles de cada match
5. Traducir champion IDs con Data Dragon
6. Agregar y visualizar

Ver `notebooks/riot_api_explorer.ipynb` función `analyze_summoner()` para referencia completa.
