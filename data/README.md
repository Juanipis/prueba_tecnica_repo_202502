# ETL Inseguridad Alimentaria Colombia

Proceso ETL para normalización de datos de inseguridad alimentaria en Colombia. Convierte datos de archivos Excel a una base de datos SQLite normalizada siguiendo las mejores prácticas de modelado de datos.

## 📊 Descripción del Proyecto

Este proyecto implementa un proceso **Extract-Transform-Load (ETL)** completo que:

- **Extrae** datos de archivos Excel (Regional, Departamental, Municipal)
- **Transforma** los datos a un esquema normalizado (3NF)
- **Carga** los datos en una base de datos SQLite optimizada

### Datos de Entrada

- `raw/Regional.xlsx` - 18 registros regionales (2015)
- `raw/Departamental.xlsx` - 66 registros departamentales (2022-2023)
- `raw/Municipal.xlsx` - 3,366 registros municipales (2022-2024)

### Indicadores Procesados

1. **Inseguridad Alimentaria Grave** (Departamental)
2. **Inseguridad Alimentaria Moderado o Grave** (Municipal)
3. **Prevalencia de hogares en inseguridad alimentaria** (Regional)

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python 3.9+
- Poetry

### Instalación

```bash
# Navegar a la carpeta data
cd data

# Instalar dependencias con Poetry
poetry install

# Activar el entorno virtual (opcional)
poetry shell
```

## 🔧 Uso

### Ejecutar ETL Completo

```bash
# Asegurate de estar en la carpeta data
cd data

# Proceso ETL completo (Extract + Transform + Load)
# Genera automáticamente archivos con timestamp
poetry run python -m etl_inseguridad.main

# Con opciones personalizadas
poetry run python -m etl_inseguridad.main --data-path raw --skip-quality
```

### Ejecutar Etapas Individuales

```bash
# Solo extracción
poetry run etl-extract

# Solo transformación
poetry run etl-transform

# Solo carga
poetry run etl-load
```

### Consultas de Ejemplo

```bash
# Ejecutar consultas de demostración
poetry run python -m etl_inseguridad.queries
```

## 📁 Estructura del Proyecto ETL

```
data/
├── raw/                              # Archivos Excel originales
│   ├── Regional.xlsx
│   ├── Departamental.xlsx
│   └── Municipal.xlsx
├── curated/                          # Datos curados (limpios, CSV con timestamp) - GITIGNORED
│   ├── regional_curated_YYYYMMDD_HHMMSS.csv
│   ├── departamental_curated_YYYYMMDD_HHMMSS.csv
│   └── municipal_curated_YYYYMMDD_HHMMSS.csv
├── processed/                        # Datos procesados (normalizados, CSV con timestamp) - GITIGNORED
│   ├── geografia_processed_YYYYMMDD_HHMMSS.csv
│   ├── indicadores_processed_YYYYMMDD_HHMMSS.csv
│   └── datos_medicion_processed_YYYYMMDD_HHMMSS.csv
├── sqlite_databases/                 # Bases de datos SQLite
│   ├── inseguridad_alimentaria_YYYYMMDD_HHMMSS.db  # (gitignored)
│   └── inseguridad_alimentaria_latest.db  # ← En repo (para la app)
├── src/etl_inseguridad/             # Paquete Python principal
│   ├── __init__.py
│   ├── extract.py                   # Módulo de extracción
│   ├── transform.py                 # Módulo de transformación
│   ├── load.py                      # Módulo de carga
│   ├── main.py                      # Orquestador principal
│   └── queries.py                   # Consultas de ejemplo
├── pyproject.toml                   # Configuración Poetry
├── poetry.lock                      # Lock de dependencias
├── etl.md                          # Documentación técnica detallada
├── .gitignore                      # Control de versiones específico para data/
└── README.md                       # Este archivo
```

## 🗄️ Esquema de Base de Datos

### Tablas Creadas

#### 1. `geografia`

- **id_geografia** (PK): Identificador único
- **nivel**: Nacional/Regional/Departamental/Municipal
- **nombre**: Nombre de la entidad geográfica
- **id_padre** (FK): Relación jerárquica
- **codigo_dane**: Código DANE (opcional)

#### 2. `indicadores`

- **id_indicador** (PK): Identificador único
- **nombre_indicador**: Nombre completo del indicador
- **tipo_dato**: Tipo de valor (Porcentaje, etc.)
- **tipo_de_medida**: Metodología (Prevalencia, etc.)

#### 3. `datos_medicion`

- **id_medicion** (PK): Identificador único
- **id_geografia** (FK): Referencia a geografia
- **id_indicador** (FK): Referencia a indicadores
- **año**: Año de la medición
- **valor**: Valor numérico del indicador

### Integridad de Datos

- ✅ Claves foráneas implementadas
- ✅ Constraints de unicidad
- ✅ Índices para optimización
- ✅ Validación de integridad referencial

## 📈 Resultados del Proceso

### Estadísticas Finales

- **Total entidades geográficas**: 1,162
  - Nacional: 1
  - Regional: 6
  - Departamental: 33
  - Municipal: 1,122
- **Indicadores procesados**: 3
- **Mediciones totales**: 1,131
- **Años cubiertos**: 2005-2024

### Limpieza de Datos Aplicada

- ⚠️ **2,244 registros municipales** con valores NULL filtrados
- ⚠️ **83 registros duplicados** eliminados
- ✅ **100% integridad referencial** mantenida

## 🔍 Consultas de Ejemplo

El módulo `queries.py` incluye consultas predefinidas:

```python
# Datos nacionales por año
query_nacional_por_año()

# Departamentos por indicador
query_departamentos_por_indicador("Inseguridad Alimentaria Grave", 2022)

# Top municipios por departamento
query_municipios_top_por_departamento("Antioquia", "Inseguridad Alimentaria Moderado o Grave", 2022)

# Comparación regional
query_comparacion_regional("Prevalencia de hogares en inseguridad alimentaria", 2015)

# Evolución temporal
query_evolucion_temporal("Colombia", "Inseguridad Alimentaria Grave")
```

## 🎯 Insights Destacados

### Nivel Nacional (2022)

- **Inseguridad Alimentaria Grave**: 4.86%
- **Inseguridad Alimentaria Moderado o Grave**: 28.08%

### Departamentos más Afectados (2022)

1. **La Guajira**: 17.50% (Grave)
2. **Arauca**: 11.02% (Grave)
3. **Chocó**: 10.43% (Grave)
4. **Sucre**: 10.41% (Grave)
5. **Magdalena**: 10.41% (Grave)

### Comparación Regional (2015)

- **Región Atlántica**: 65.0% (+10.8% vs nacional)
- **Región Orinoquía-Amazonía**: 65.0% (+10.8% vs nacional)
- **Bogotá**: 50.2% (-4.0% vs nacional)

## 🛠️ Tecnologías Utilizadas

- **Python 3.9+**: Lenguaje principal
- **Poetry**: Gestión de dependencias
- **Pandas**: Manipulación de datos
- **OpenPyXL**: Lectura de archivos Excel
- **SQLite**: Base de datos embebida
- **Poetry Scripts**: Comandos CLI

## 📚 Dependencias

```toml
[tool.poetry.dependencies]
python = "^3.9"
pandas = "^2.0.0"
openpyxl = "^3.1.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
black = "^23.0.0"
isort = "^5.12.0"
flake8 = "^6.0.0"
```

## 🏗️ Arquitectura del ETL

### Flujo de Datos por Capas

```
RAW → CURATED → PROCESSED → SQLite
```

### 1. Extract (Extracción)

- Lectura de archivos Excel desde `raw/`
- Verificación de estructura y columnas esperadas
- Validación de integridad de datos
- Manejo de errores y logging

### 2. Transform (Transformación y Curado)

**Capa Curated:**

- Limpieza de datos (filtrado de NULL)
- Guardado en `curated/` como CSV con timestamp
- Preservación de estructura original mejorada

**Capa Processed:**

- Normalización a 3NF (Tercera Forma Normal)
- Creación de tablas geografía e indicadores
- Eliminación de duplicados
- Guardado en `processed/` como CSV con timestamp
- Mapeo de relaciones jerárquicas

### 3. Load (Carga)

- Creación de SQLite con timestamp único
- Inserción con manejo de transacciones
- Creación de enlace `_latest.db` automático
- Verificaciones de calidad de datos
- Índices para optimización de consultas

### 4. Versionado Automático

- **Timestamp format:** `YYYYMMDD_HHMMSS`
- **Archivos generados por ejecución:**
  - 3 archivos curated CSV
  - 3 archivos processed CSV
  - 1 base de datos SQLite
  - 1 enlace `_latest.db` actualizado

## 🔬 Verificaciones de Calidad

- ✅ Integridad referencial
- ✅ Ausencia de valores NULL críticos
- ✅ Eliminación de duplicados
- ✅ Consistencia de tipos de datos
- ✅ Distribución por niveles geográficos

## 🚨 Solución de Problemas

### Problema: "Module not found"

```bash
# Asegurate de estar en la carpeta data y tener el entorno activado
cd data
poetry shell
poetry install
```

### Problema: "Archivo not found"

```bash
# Verifica que los archivos Excel estén en la ubicación correcta
ls raw/
# Deberías ver: Regional.xlsx, Departamental.xlsx, Municipal.xlsx
```

### Problema: "Database locked"

```bash
# Elimina las bases de datos existentes si hay problemas
rm sqlite_databases/*.db
# Vuelve a ejecutar el ETL (genera nuevas con timestamp)
poetry run python -m etl_inseguridad.main
```

## 🗂️ Control de Versiones

### Archivos incluidos en el repositorio:

```
✅ INCLUIDOS EN GIT:
├── raw/                              # Datos originales Excel
├── src/                              # Código fuente Python
├── pyproject.toml & poetry.lock      # Configuración del proyecto
├── README.md & etl.md               # Documentación
├── .gitignore                       # Configuración git específica
└── sqlite_databases/
    └── inseguridad_alimentaria_latest.db  # Solo la DB más reciente
```

### Archivos generados (ignorados por git):

```
❌ GITIGNORED (generados automáticamente):
├── curated/                          # Todos los CSV curados
├── processed/                        # Todos los CSV procesados
├── sqlite_databases/
│   └── inseguridad_alimentaria_YYYYMMDD_HHMMSS.db  # DBs con timestamp
└── src/**/__pycache__/              # Cache de Python
```

### Justificación:

- **Archivos generados**: Se ignoran porque se regeneran automáticamente con cada ejecución del ETL
- **latest.db preservado**: Necesario para que aplicaciones backend/frontend funcionen sin configuración adicional
- **Versionado por timestamp**: Permite rastrear ejecuciones históricas localmente sin saturar el repositorio
- **Tamaño optimizado**: El repo se mantiene liviano incluyendo solo código y configuración

## 🔗 Enlaces Relacionados

- **Documentación técnica detallada**: `etl.md`
- **Repositorio principal**: `../README.md`
- **Base de datos para aplicaciones**: `sqlite_databases/inseguridad_alimentaria_latest.db`
- **Control de versiones**: `.gitignore` (específico para data/)

---

⚡ **Proceso ETL optimizado para datos de inseguridad alimentaria en Colombia** ⚡
