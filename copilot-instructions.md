# 🤖 Copilot Instructions — LoL Meta Evolution Dashboard

## Propósito del proyecto
Este repositorio busca analizar la evolución del meta competitivo de League of Legends.  
Copilot debe priorizar la legibilidad, la consistencia del estilo de código y el análisis reproducible.

---

## 🧩 Convenciones de código
- Usa **Python 3.10+** y sigue PEP8.
- Prefiere `pandas` y `numpy` para manipular datos.
- Visualiza con `plotly.express` o `plotly.graph_objects`.
- Documenta todas las funciones con **docstrings tipo Google**:
  ```python
  def calcular_winrate(df: pd.DataFrame) -> pd.DataFrame:
      """
      Calcula el winrate por campeón y parche.

      Args:
          df (pd.DataFrame): DataFrame con columnas ['champion', 'patch', 'result'].

      Returns:
          pd.DataFrame: Tabla con columnas ['champion', 'patch', 'win_rate'].
      """
  ```

Los nombres de variables deben ser explícitos (champion_data, no cd).

📁 Organización esperada

src/data_collection.py: funciones para llamar Riot API (requests.get) y guardar respuestas JSON.

src/data_cleaning.py: limpieza y transformación, manejo de NaN y columnas.

src/analysis.py: agregaciones y cálculos estadísticos.

src/visualization.py: generación de gráficos y dashboards.

dashboard.py: app principal en Streamlit.

🧠 Instrucciones a Copilot

Propón funciones auxiliares antes de bloques monolíticos.

Genera type hints en todas las funciones.

Sugiere comentarios contextuales explicando el propósito del código.

Evita dependencias innecesarias.

Mantén nombres coherentes entre notebooks y scripts.

Propón unit tests básicos con pytest para cada módulo nuevo.

En notebooks, usa markdown cells con títulos descriptivos (nivel 2 o 3).

🎨 Estilo de visualización

Gráficos minimalistas, fondos blancos, tipografía legible.

Incluye títulos y labels en español o inglés según el contexto.

Preferir plotly interactivo sobre matplotlib.

🧾 Buenas prácticas adicionales

Los datasets grandes deben ir en data/raw/ y no subirse al repo.

Usa .env o variables de entorno para las claves de Riot API.

Cada script debe ser ejecutable desde la raíz del proyecto.

No incluir claves ni tokens en notebooks o scripts.

🧠 Tono del código

Profesional, limpio, con explicaciones breves y precisas.

Evita abreviaturas y comentarios triviales.

Prioriza el entendimiento del flujo analítico sobre la microoptimización.

No uses emojis en el código. 
