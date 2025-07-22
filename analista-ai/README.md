# Analista AI - Backend

Aplicación FastAPI con SmolAgents para análisis inteligente de datos de inseguridad alimentaria en Colombia.

## 🚀 Características

- **SmolAgent Inteligente**: Utiliza SmolAgents con Gemini para análisis autocorrectivo
- **Frontend Integrado**: Interface web completa para consultas interactivas
- **Configuración Tipada**: Sistema de configuración robusto con pydantic-settings
- **SQL Dinámico**: El agente escribe consultas SQL según las preguntas del usuario
- **Análisis Estadístico**: Integración con pandas, numpy y matplotlib
- **Visualizaciones Automáticas**: Genera gráficas con matplotlib integradas en el frontend
- **Autocorrección**: Si una consulta falla, el agente la corrige automáticamente

## 📦 Instalación

### 1. Instalar Dependencias

```bash
# Usando Poetry (recomendado)
poetry install

# O usando pip
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

```bash
# Copiar archivo de configuración
cp .env.example .env

# Editar .env y configurar las variables necesarias
# Como mínimo necesitas: GEMINI_API_KEY=tu_api_key_aqui
```

**Configuración usando pydantic-settings**:

- ✅ **Validación automática** de tipos y valores
- ✅ **Configuración estructurada** en categorías
- ✅ **Valores por defecto** seguros
- ✅ **Documentación integrada** en cada campo

Para obtener tu API key:

1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea un nuevo proyecto o selecciona uno existente
3. Genera una nueva API key
4. Agrégala al archivo `.env` como `GEMINI_API_KEY=tu_key_aqui`

### 3. Verificar Base de Datos

Asegúrate de que la base de datos esté en:

```
../data/sqlite_databases/inseguridad_alimentaria_latest.db
```

## 🎯 Uso

### Iniciar el Servidor

```bash
# Desarrollo
python main.py

# O con uvicorn
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Acceder a la Aplicación

- **Frontend Principal**: http://127.0.0.1:8000
- **API Info**: http://127.0.0.1:8000/api-info
- **Documentación**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 🔧 API Endpoints

### Principales

| Endpoint   | Método | Descripción               |
| ---------- | ------ | ------------------------- |
| `/`        | GET    | Frontend principal (HTML) |
| `/analyze` | POST   | Análisis con SmolAgent    |
| `/status`  | GET    | Estado del sistema        |
| `/schema`  | GET    | Esquema de base de datos  |

### Utilidad

| Endpoint    | Método | Descripción               |
| ----------- | ------ | ------------------------- |
| `/health`   | GET    | Estado básico del sistema |
| `/examples` | GET    | Ejemplos de preguntas     |
| `/api-info` | GET    | Información de la API     |

## 🤖 Capacidades del SmolAgent

### Herramientas Disponibles

- **sql_query**: Consultas SQL directas
- **get_database_schema**: Explorar estructura de datos
- **analyze_data_pandas**: Análisis estadísticos avanzados
- **get_top_entities**: Rankings de entidades
- **compare_years**: Análisis temporal
- **calculate_statistics**: Estadísticas descriptivas
- **create_formatted_table**: Tablas formateadas
- **get_available_years**: Años disponibles
- **get_available_indicators**: Indicadores disponibles
- **get_entities_by_level**: Entidades por nivel geográfico
- **quick_summary**: Resumen rápido

### 📊 Herramientas de Visualización (NUEVO - Token-Eficiente)

- **create_chart_visualization**: Crea gráficas individuales (bar, line, pie, scatter, histogram)
- **create_multiple_charts**: Genera múltiples gráficas en una sola consulta
- **analyze_and_visualize**: Análisis completo con visualizaciones automáticas

**🚀 Sistema Token-Eficiente**: Las herramientas NO retornan imágenes base64 al agente (evita consumir tokens masivamente). Las imágenes se almacenan temporalmente y se inyectan solo en la respuesta final al frontend.

### Ejemplos de Preguntas

```
# Situación general
"¿Cuál es la situación de inseguridad alimentaria en Colombia?"

# Rankings
"¿Qué departamentos tienen mayor inseguridad alimentaria grave en 2022?"

# Comparaciones
"Compara la evolución de inseguridad alimentaria entre Antioquia y Cundinamarca"

# Estadísticas
"¿Cuáles son las estadísticas descriptivas de inseguridad moderada en 2023?"

# Por región
"Muestra los 5 municipios con mayor inseguridad alimentaria en Antioquia"

# Temporal
"¿Cómo ha evolucionado la inseguridad alimentaria en los últimos años?"

# Visualizaciones (NUEVO)
"Crea una gráfica de barras que muestre los 10 departamentos con mayor inseguridad alimentaria grave en 2022"

"Analiza con gráficas la distribución de inseguridad alimentaria por regiones en Colombia"

"Haz un análisis completo con visualizaciones de la evolución temporal de inseguridad alimentaria"

"Genera múltiples gráficas: una de barras por departamento y otra circular por regiones"
```

## 🛠️ Desarrollo

### Estructura del Proyecto

```
backend/
├── core/
│   ├── __init__.py
│   ├── settings.py          # ⭐ Configuración con pydantic-settings
│   ├── smolagent.py         # Configuración del SmolAgent
│   └── sql_tools.py         # Herramientas SQL para el agente
├── static/
│   └── index.html           # Frontend principal
├── main.py                  # Aplicación FastAPI
├── pyproject.toml           # Dependencias
├── requirements.txt         # Dependencias para pip
├── .env.example             # Ejemplo de configuración
└── README.md                # Este archivo
```

### ⭐ Sistema de Configuración (pydantic-settings)

El proyecto usa **pydantic-settings** para configuración tipada y validada:

```python
# core/settings.py
class AppSettings(BaseSettings):
    # Configuraciones anidadas por categoría
    database: DatabaseSettings      # DB_* variables
    api: APISettings                # GEMINI_* variables
    agent: SmolAgentSettings        # AGENT_* variables
    server: ServerSettings          # SERVER_* variables
    logging: LoggingSettings        # LOG_* variables

    # Archivo .env automático
    class Config:
        env_file = ".env"
```

**Ventajas sobre python-dotenv**:

- ✅ Validación automática de tipos
- ✅ Valores por defecto documentados
- ✅ Estructura organizada por categorías
- ✅ Validación de rangos y formatos
- ✅ Autocompletado en IDEs

### Variables de Entorno Disponibles

#### Configuración Básica (Requerida)

```bash
GEMINI_API_KEY=tu_api_key_aqui
```

#### Configuración de Base de Datos

```bash
DB_PATH=../data/sqlite_databases/inseguridad_alimentaria_latest.db
DB_CONNECTION_TIMEOUT=30
DB_MAX_RETRIES=3
```

#### Configuración del SmolAgent

```bash
AGENT_MAX_STEPS=15
AGENT_VERBOSITY_LEVEL=1
AGENT_ENABLE_CODE_EXECUTION=true
```

#### Configuración del Servidor

```bash
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
SERVER_RELOAD=true
SERVER_DEBUG=true
```

#### Configuración de Logging

```bash
LOG_LEVEL=INFO
LOG_TO_FILE=false
```

### Agregar Nuevas Herramientas

1. Crear función en `core/sql_tools.py` con decorador `@tool`
2. Importar en `core/smolagent.py`
3. Agregar a la lista `tools` en `_initialize_agent()`

### Configuración del SmolAgent

```python
# Configuración automática desde settings
agent_config = self.settings.agent

self.agent = CodeAgent(
    tools=tools,
    model=self.model,
    additional_authorized_imports=agent_config.authorized_imports,
    max_steps=agent_config.max_steps,  # Desde AGENT_MAX_STEPS
    verbosity_level=agent_config.verbosity_level  # Desde AGENT_VERBOSITY_LEVEL
)
```

## 🔍 Solución de Problemas

### Error: Agente no inicializado

```bash
# Verificar configuración
python -c "from core.settings import print_settings_summary; print_settings_summary()"

# Verificar archivo .env
cat .env
```

### Error: Configuración inválida

El sistema ahora valida automáticamente la configuración al inicio:

```bash
# Ver validación completa
python core/settings.py
```

### Error: Dependencias faltantes

```bash
# Reinstalar dependencias
poetry install --no-cache

# O con pip
pip install -r requirements.txt --force-reinstall
```

### Error: Importaciones no autorizadas

Las importaciones están configuradas en `AGENT_AUTHORIZED_IMPORTS` o por defecto en settings.py.

### Error: pydantic-settings no encontrado

```bash
pip install pydantic-settings>=2.5.2
# O
poetry add pydantic-settings
```

## 📊 Visualizaciones con Matplotlib

### Cómo Funciona

El SmolAgent ahora puede **generar gráficas automáticamente** usando matplotlib:

1. **Gráficas Automáticas**: Solo pide "analiza con gráficas" y el agente decide qué visualizar
2. **Gráficas Específicas**: Especifica el tipo: "crea una gráfica de barras de..."
3. **Múltiples Gráficas**: Genera varias visualizaciones en una sola consulta
4. **Integración Perfecta**: Las gráficas aparecen directamente en el frontend

### Tipos de Gráficas Disponibles

- **bar**: Gráficas de barras para comparaciones
- **line**: Gráficas de líneas para evolución temporal
- **pie**: Gráficas circulares para proporciones
- **scatter**: Diagramas de dispersión para correlaciones
- **histogram**: Histogramas para distribuciones

### Ejemplos de Uso

```
"Crea una gráfica de barras con los departamentos con mayor inseguridad alimentaria"
"Analiza con histograma la distribución de los valores de inseguridad"
"Haz una gráfica circular que muestre la proporción por regiones"
"Genera un análisis completo con múltiples visualizaciones automáticas"
```

## 📊 Base de Datos

### Esquema

- **geografia**: Entidades geográficas (Nacional, Regional, Departamental, Municipal)
- **indicadores**: Tipos de indicadores de inseguridad alimentaria
- **datos_medicion**: Mediciones por entidad, indicador y año

### Indicadores Principales

1. **Inseguridad Alimentaria Grave**
2. **Inseguridad Alimentaria Moderado o Grave**
3. **Prevalencia de hogares en inseguridad alimentaria**

### Período de Datos

- **Principal**: 2022-2024
- **Adicional**: Algunos datos de 2015

## 🔧 Migración desde python-dotenv

Si estás migrando desde la versión anterior:

1. **Actualizar dependencias**:

   ```bash
   pip uninstall python-dotenv
   pip install pydantic-settings>=2.5.2
   ```

2. **El archivo .env sigue funcionando** igual, pero ahora con validación

3. **Nuevas variables organizadas** por prefijos:
   - `GEMINI_*` para API de Gemini
   - `DB_*` para base de datos
   - `AGENT_*` para SmolAgent
   - `SERVER_*` para servidor FastAPI
   - `LOG_*` para logging

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

Powered by **FastAPI** + **SmolAgents** + **LiteLLM** + **Gemini AI** + **Pydantic Settings**
