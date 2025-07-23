# 🤖 Analista AI - Inseguridad Alimentaria Colombia

Sistema inteligente de análisis de datos de inseguridad alimentaria en Colombia usando **SmolAgents** + **Gemini AI** + **Búsqueda Web**.

## ✨ Características Principales

### 🧠 Agente Inteligente

- **SmolAgents con Gemini**: Procesamiento de lenguaje natural avanzado
- **Autocorrección**: Se corrige automáticamente si las consultas SQL fallan
- **Análisis Estadístico**: Integración con pandas/numpy para análisis profundos
- **🔍 Búsqueda Web**: Complementa análisis con información actualizada de internet

### 📊 Capacidades de Análisis

- Consultas SQL dinámicas generadas automáticamente
- Estadísticas descriptivas (media, mediana, desviación estándar)
- Rankings y comparaciones entre entidades geográficas
- Análisis temporal y evolución de indicadores
- Visualizaciones automáticas con matplotlib (token-eficientes)

### 🌐 Búsqueda Contextual con Citación

- **DuckDuckGo Integration**: Búsquedas web complementarias
- **Contexto Inteligente**: Combina datos locales con información externa
- **📚 Citación Automática**: Incluye fuentes web en formato APA automáticamente
- **URLs Verificables**: Todas las fuentes incluyen enlaces funcionales
- **Información Actualizada**: Políticas públicas, causas, comparaciones internacionales

### 🎨 Visualizaciones y Tablas

- **Gráficas**: barras, líneas, circular, dispersión e histogramas
- **📊 Tablas Markdown**: Formato correcto garantizado para el frontend
- **🔍 Palabras Clave**: Extracción automática de insights principales
- **Renderizado Perfecto**: CSS optimizado para tablas y elementos visuales
- Almacenamiento temporal token-eficiente

## 🗃️ Datos Disponibles

### Indicadores de Inseguridad Alimentaria

1. **Inseguridad Alimentaria Grave**
2. **Inseguridad Alimentaria Moderado o Grave**
3. **Prevalencia de hogares en inseguridad alimentaria**

### Cobertura Geográfica

- **Nacional**: Colombia
- **Regional**: Regiones de Colombia
- **Departamental**: 32 departamentos
- **Municipal**: Principales municipios

### Período de Datos

- **Principal**: 2022-2024
- **Histórico**: Algunos datos desde 2015

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias

```bash
# Con pip
pip install -r requirements.txt

# Con poetry (recomendado)
poetry install
```

### 2. Configurar API Key de Gemini

```bash
# Crear archivo .env (opcional)
echo "GEMINI_API_KEY=tu_api_key_aqui" > .env

# O configurar como variable de entorno
export GEMINI_API_KEY="tu_api_key_aqui"
```

### 3. Ejecutar Aplicación

```bash
# Desarrollo
python main.py

# Con uvicorn directamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Probar Funcionalidades

```bash
# Ejecutar script de pruebas de citación
python test_citations.py

# Ejecutar script de pruebas de tablas y palabras clave
python test_table_keywords.py

# Verificar todo el sistema está funcionando
python -c "from core.smolagent import food_security_agent; print('✅ Sistema listo' if food_security_agent else '❌ Error')"
```

## 💡 Ejemplos de Uso

### Análisis Básicos

```
¿Cuál es la situación de inseguridad alimentaria en Colombia?
¿Qué departamentos tienen mayor inseguridad alimentaria en 2022?
¿Cómo está la situación en Antioquia?
```

### Análisis Comparativos

```
Compara la inseguridad alimentaria entre Antioquia y Cundinamarca
¿Cuál es la diferencia entre inseguridad grave y moderada?
Compara los datos de 2022 vs 2023
```

### Con Contexto Web y Citas 📚

```
¿Cuáles son las principales políticas públicas de Colombia para combatir
la inseguridad alimentaria y cómo se relacionan con nuestros datos?

Analiza la situación de inseguridad alimentaria en Chocó y complementa
con información sobre las causas del conflicto armado con fuentes verificables

Compara nuestros datos con estadísticas internacionales de inseguridad
alimentaria en América Latina y cita las fuentes consultadas

Investiga las causas principales de inseguridad alimentaria en Colombia
según organizaciones internacionales y contrasta con nuestros datos
```

### Visualizaciones

```
Crea una gráfica de barras que muestre los 10 departamentos con mayor
inseguridad alimentaria grave en 2022

Analiza con gráficas la distribución de inseguridad alimentaria por
regiones en Colombia
```

## 🔧 API Endpoints

### Análisis Principal

- `POST /analyze` - Análisis inteligente con SmolAgent + Web Search
- `GET /examples` - Ejemplos de preguntas

### Información del Sistema

- `GET /status` - Estado detallado del agente y componentes
- `GET /health` - Verificación básica del sistema
- `GET /schema` - Esquema de la base de datos

### Documentación

- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc
- `GET /api-info` - Página de información completa

## 🧪 Arquitectura Técnica

### Backend

- **FastAPI**: Framework web moderno y rápido
- **SmolAgents**: Framework de agentes inteligentes
- **LiteLLM**: Integración con múltiples modelos de IA
- **Gemini AI**: Modelo de lenguaje principal
- **WebSearchTool**: Búsquedas web con DuckDuckGo

### Base de Datos

- **SQLite**: Base de datos normalizada
- **Pandas**: Análisis de datos en memoria
- **NumPy**: Computación numérica eficiente

### Visualizaciones

- **Matplotlib**: Generación de gráficas
- **Sistema Token-Eficiente**: Almacenamiento temporal de imágenes

## 🔍 Flujo de Análisis

1. **Interpretación**: El agente interpreta la pregunta en lenguaje natural
2. **Decisión**: Determina si necesita datos locales, búsqueda web, o ambos
3. **Búsqueda Local**: Genera y ejecuta consultas SQL dinámicamente
4. **Búsqueda Web**: Busca información complementaria si es necesario
5. **Análisis**: Realiza estadísticas con pandas/numpy
6. **Visualización**: Genera gráficas automáticamente si es apropiado
7. **Síntesis**: Combina todos los resultados en respuesta estructurada
8. **Autocorrección**: Se corrige automáticamente si hay errores

## 📚 Sistema de Citación de Fuentes Web

### Formato Automático APA

Cuando el agente utiliza información de fuentes web, automáticamente:

1. **Incluye citas en el texto**: Referencia las fuentes como "Según [Fuente]..." o "(Fuente: [Nombre])"
2. **Genera sección de fuentes**: Crea automáticamente una sección "📚 Fuentes Consultadas"
3. **Formato APA**: Utiliza el estándar académico APA para las citas
4. **URLs funcionales**: Incluye enlaces directos a las fuentes originales

### Ejemplo de Respuesta con Citas

```markdown
# Análisis de Políticas de Seguridad Alimentaria

## Datos de Nuestra Base de Datos

[Análisis de datos locales...]

## Contexto de Políticas Públicas

Según el Ministerio de Salud de Colombia [1], las políticas actuales se enfocan en...
La FAO Colombia [2] reporta que los programas gubernamentales han tenido...

## 📚 Fuentes Consultadas

1. Ministerio de Salud de Colombia. (2024). _Política Nacional de Seguridad Alimentaria_. https://www.minsalud.gov.co/politicas
2. FAO Colombia. (2024). _Programas de Seguridad Alimentaria en Colombia_. https://www.fao.org/colombia/programas

---

_Fuentes consultadas para complementar el análisis de datos locales_
```

### Herramientas de Citación Disponibles

- **format_web_citation**: Formatea citas individuales en estilo APA
- **create_sources_section**: Genera secciones completas de fuentes consultadas

## 📊 Sistema de Tablas Markdown Mejorado

### Formato Correcto Garantizado

El agente ahora genera tablas Markdown con formato perfecto para el frontend según los estándares de [sintaxis Markdown](https://htmlmarkdown.com/syntax/markdown-tables/):

```markdown
| Departamento | Indicador | Año  | Porcentaje |
| ------------ | --------- | ---- | ---------- |
| Chocó        | Grave     | 2022 | 28.5%      |
| La Guajira   | Grave     | 2022 | 24.2%      |
```

### Características del Sistema de Tablas

1. **📏 Formato Consistente**: Todas las columnas alineadas correctamente
2. **🔢 Formateo Automático**: Números y porcentajes con formato apropiado
3. **🎨 CSS Mejorado**: Tablas con hover effects y diseño profesional
4. **📱 Responsivo**: Tablas que se adaptan a diferentes tamaños de pantalla

### Herramientas de Tablas Disponibles

- **create_formatted_markdown_table**: Genera tablas con formato perfecto
- **create_formatted_table**: Tablas básicas (legacy)

## 🔍 Sistema de Palabras Clave Inteligente

### Extracción Automática

El agente automáticamente identifica y extrae:

- **🌍 Términos Geográficos**: Departamentos, municipios, regiones mencionados
- **📊 Conceptos Estadísticos**: Media, mediana, correlación, tendencias
- **📅 Datos Temporales**: Años específicos analizados
- **📈 Insights Cuantitativos**: Presencia de porcentajes y datos numéricos

### Visualización en el Frontend

Las palabras clave aparecen como **tags coloridos** al final del análisis:

- **Azules**: Términos geográficos y conceptos principales
- **Verdes**: Insights estadísticos y metodológicos

### Ejemplo de Palabras Clave Generadas

```
🔍 Palabras Clave del Análisis
[Chocó] [Inseguridad Alimentaria] [📅 Año 2022] [📊 Estadísticas] [📈 Datos Porcentuales]
```

## 🛠️ Configuración Avanzada

### Configuración del Agente

```python
# core/settings.py
class SmolAgentSettings(BaseSettings):
    max_steps: int = 15  # Máximo pasos de autocorrección
    verbosity_level: int = 1  # Nivel de detalle en logs
    enable_code_execution: bool = True  # Ejecución de código Python
```

### Configuración de Búsqueda Web

La búsqueda web se inicializa automáticamente y usa DuckDuckGo sin necesidad de API keys adicionales.

## 📊 Estado del Sistema

Verifica el estado completo en: `GET /status`

```json
{
  "agent_available": true,
  "components": {
    "database": true,
    "model": true,
    "agent": true,
    "api_key": true,
    "web_search": true
  },
  "system_ready": true
}
```

## 🔄 Autocorrección Inteligente

El agente puede:

- Detectar errores de sintaxis SQL y corregirlos
- Adaptar consultas según el esquema real de la base de datos
- Reintentar análisis con diferentes enfoques
- Sugerir consultas alternativas si los datos no están disponibles

## 📈 Mejoras Token-Eficientes

- **Visualizaciones**: Las imágenes se almacenan temporalmente, no se envían como base64
- **Búsquedas Web**: Solo se incluye información relevante y resumida
- **Respuestas**: Formato markdown estructurado y conciso

## 🤝 Contribuir

Este proyecto está diseñado para ser extensible. Puedes agregar:

- Nuevas herramientas al agente
- Indicadores adicionales a la base de datos
- Tipos de visualizaciones personalizadas
- Fuentes de datos externas

## 📄 Licencia

[Incluir información de licencia]

---

**Powered by**: FastAPI + SmolAgents + LiteLLM + Gemini AI + DuckDuckGo Search + APA Citation System + Enhanced Markdown Tables + Smart Keywords
