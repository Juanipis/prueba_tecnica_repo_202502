"""
Agente SmolAgents para análisis de datos de inseguridad alimentaria.

Este módulo configura un CodeAgent que puede:
- Consultar la base de datos SQLite usando SQL directo y flexible
- Explorar la estructura de la base de datos dinámicamente
- Realizar análisis estadísticos con pandas y numpy
- Autocorregirse si las consultas son incorrectas
- Iterar hasta obtener resultados correctos
- Crear visualizaciones con matplotlib
- Buscar información complementaria en internet usando DuckDuckGo
- Acceder a documentos especializados usando RAG (Retrieval-Augmented Generation)
"""

import os
from typing import Dict, Any
from smolagents import CodeAgent, LiteLLMModel, WebSearchTool
from .settings import get_settings
from .sql_tools import (
    sql_query,
    get_database_schema,
    analyze_data_pandas,
    create_formatted_table,
    create_formatted_markdown_table,
    create_chart_visualization,
    create_multiple_charts,
    analyze_and_visualize,
    format_web_citation,
    create_sources_section,
)
from .rag_tools import search_food_security_documents, get_rag_system_status


class InseguridadAlimentariaAgent:
    """
    Agente especializado en análisis de datos de inseguridad alimentaria en Colombia.

    Utiliza SmolAgents con LiteLLM para conectar con Gemini y generar análisis
    inteligentes usando consultas SQL flexibles, análisis estadísticos, y búsquedas web.

    El agente puede crear sus propias consultas SQL para cualquier análisis requerido,
    lo que lo hace flexible y adaptable a cambios en la estructura de la base de datos.
    """

    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.agent = None
        self.web_search_tool = None
        self._initialize_web_search()
        self._initialize_model()
        self._initialize_agent()

    def _initialize_web_search(self):
        """Inicializa la herramienta de búsqueda web con DuckDuckGo."""
        try:
            self.web_search_tool = WebSearchTool()
            print("✅ Herramienta de búsqueda web DuckDuckGo inicializada")
        except Exception as e:
            print(f"⚠️ Error inicializando búsqueda web: {e}")
            self.web_search_tool = None

    def _initialize_model(self):
        """Inicializa el modelo LiteLLM con Gemini usando configuración tipada."""
        api_config = self.settings.api

        if (
            not api_config.gemini_api_key
            or api_config.gemini_api_key == "TU_API_KEY_DE_GEMINI_AQUI"
        ):
            print("⚠️ Advertencia: GEMINI_API_KEY no configurada correctamente")
            print("🔧 Configura tu API key en el archivo .env")
            # Usar modelo por defecto para testing
            self.model = LiteLLMModel(model_id=api_config.gemini_model)
        else:
            self.model = LiteLLMModel(
                model_id=api_config.gemini_model,
                api_key=api_config.gemini_api_key,
                temperature=api_config.gemini_temperature,
                max_tokens=api_config.gemini_max_tokens,
            )

    def _initialize_agent(self):
        """Inicializa el CodeAgent con las herramientas esenciales y flexibles."""
        # Herramientas esenciales - flexibles y adaptables
        tools = [
            # Herramientas principales para acceso a datos
            sql_query,  # Consultas SQL flexibles
            get_database_schema,  # Exploración de estructura
            analyze_data_pandas,  # Análisis estadístico avanzado
            # Herramientas de presentación y formato
            create_formatted_table,  # Tablas básicas
            create_formatted_markdown_table,  # Tablas Markdown correctas
            # Herramientas de visualización
            create_chart_visualization,  # Gráficas individuales
            create_multiple_charts,  # Múltiples gráficas
            analyze_and_visualize,  # Análisis completo con gráficas
            # Herramientas de fuentes y documentación
            format_web_citation,  # Formateo de citas
            create_sources_section,  # Sección de fuentes
            # Herramientas RAG (Retrieval-Augmented Generation)
            search_food_security_documents,  # Búsqueda en documentos especializados
            get_rag_system_status,  # Estado del sistema RAG
        ]

        # Agregar herramienta de búsqueda web si está disponible
        if self.web_search_tool:
            tools.append(self.web_search_tool)
            print("🔍 Búsqueda web habilitada en el agente")

        # Verificar estado del RAG
        if self.settings.rag.enable_rag:
            print("📚 Sistema RAG habilitado - Documentos especializados disponibles")
        else:
            print("⚠️ Sistema RAG deshabilitado en configuración")

        agent_config = self.settings.agent

        self.agent = CodeAgent(
            tools=tools,
            model=self.model,
            additional_authorized_imports=agent_config.authorized_imports,
            max_steps=agent_config.max_steps,
            verbosity_level=agent_config.verbosity_level,
        )

        print(f"🤖 Agente inicializado con {len(tools)} herramientas esenciales")

    def analyze_question(self, question: str, session_id: str = None) -> str:
        """
        Analiza una pregunta en lenguaje natural sobre inseguridad alimentaria.

        El agente:
        1. Interpreta la pregunta
        2. Explora la estructura de la base de datos si es necesario
        3. Crea consultas SQL flexibles según lo requiera
        4. Analiza los resultados con pandas
        5. Se autocorrige si algo está mal
        6. Genera visualizaciones apropiadas
        7. Complementa con búsquedas web si es útil
        8. Produce una respuesta completa en Markdown con palabras clave inteligentes

        Args:
            question: Pregunta del usuario en lenguaje natural

        Returns:
            Análisis completo en formato Markdown
        """
        try:
            # Establecer el contexto del session_id para las herramientas
            from .sql_tools import set_current_session_id

            if session_id:
                set_current_session_id(session_id)

            # Preparar el prompt con contexto específico
            enhanced_question = self._enhance_question_with_context(
                question, session_id
            )

            # Ejecutar el agente
            result = self.agent.run(enhanced_question)

            return self._format_response(result, question)

        except Exception as e:
            error_message = f"Error ejecutando análisis: {str(e)}"
            print(f"❌ {error_message}")

            return self._generate_error_response(error_message, question)

    def _enhance_question_with_context(
        self, question: str, session_id: str = None
    ) -> str:
        """
        Mejora la pregunta del usuario con contexto sobre la base de datos y capacidades.
        """
        from .session_manager import session_manager

        web_search_status = (
            "✅ Disponible" if self.web_search_tool else "❌ No disponible"
        )

        # Obtener contexto específico de la base de datos si está habilitado
        specific_context = ""
        if self.settings.database_context.include_context_in_prompt:
            specific_context = self.settings.database_context.get_context_content()

        # Obtener contexto de conversación previa si hay session_id
        conversation_context = ""
        if session_id:
            conversation_context = session_manager.format_context_for_agent(session_id)

        context = f"""
Eres un analista experto en datos. Eres COMPLETAMENTE FLEXIBLE y DINÁMICO.

{conversation_context}

{specific_context if specific_context else ""}
{"=" * 50 if specific_context else ""}

FILOSOFÍA DE TRABAJO:
- Eres FLEXIBLE y ADAPTABLE: puedes trabajar con CUALQUIER base de datos
- NO asumes NADA sobre la estructura de datos - la descubres dinámicamente
- SIEMPRE exploras la base de datos primero si no conoces su estructura
- Creas análisis personalizados para cada pregunta específica
- Te adaptas a cualquier dominio de datos (alimentaria, salud, economía, etc.)

HERRAMIENTAS DISPONIBLES:

🔍 EXPLORACIÓN Y CONSULTA (Principales):
- sql_query: Tu herramienta MÁS IMPORTANTE - ejecuta cualquier SQL que necesites
- get_database_schema: Explora la estructura completa de CUALQUIER base de datos
- analyze_data_pandas: Análisis estadístico avanzado de cualquier resultado SQL

📊 PRESENTACIÓN Y FORMATO:
- create_formatted_table: Tablas básicas
- create_formatted_markdown_table: Tablas Markdown perfectamente formateadas

📈 VISUALIZACIÓN:
- create_chart_visualization: Gráficas individuales (bar, line, pie, scatter, histogram)
- create_multiple_charts: Múltiples visualizaciones
- analyze_and_visualize: Análisis completo con gráficas automáticas

📚 DOCUMENTACIÓN:
- format_web_citation: Formateo de citas en estilo APA
- create_sources_section: Secciones de fuentes bien formateadas
- WebSearchTool: {web_search_status} - Para información contextual complementaria

🔍 RAG (RETRIEVAL-AUGMENTED GENERATION):
- search_food_security_documents: Búsqueda semántica en documentos especializados sobre seguridad alimentaria
- get_rag_system_status: Verificar estado del sistema RAG y base de datos vectorial

STATUS DEL SISTEMA RAG: {"✅ Habilitado" if self.settings.rag.enable_rag else "❌ Deshabilitado"}

NOTA IMPORTANTE SOBRE RAG:
- Usa search_food_security_documents para obtener información técnica y especializada sobre:
  * Políticas de seguridad alimentaria
  * Marcos normativos y reglamentarios
  * Metodologías de medición de inseguridad alimentaria
  * Programas gubernamentales e intervenciones
  * Estudios especializados y reportes técnicos
  * Conceptos técnicos y definiciones oficiales
- Esta información complementa perfectamente tus análisis de datos cuantitativos
- Combina datos estadísticos (SQL) con conocimiento especializado (RAG) para análisis completos

METODOLOGÍA DE TRABAJO DINÁMICA:

1. 🔍 EXPLORACIÓN INICIAL OBLIGATORIA:
   - SIEMPRE usa get_database_schema PRIMERO si no conoces la estructura
   - NO asumas nombres de tablas, columnas o tipos de datos
   - Identifica tablas disponibles, columnas, tipos de datos y relaciones
   - Detecta patrones temporales, categóricos y numéricos automáticamente

2. 📝 CONSULTAS SQL COMPLETAMENTE DINÁMICAS:
   - Construye consultas basadas SOLO en la información del esquema actual
   - Usa los nombres reales de tablas y columnas que encontraste
   - Aprovecha las claves foráneas detectadas para JOINs apropiados
   - Adapta tu análisis al tipo de datos disponible

3. 📊 ANÁLISIS INTELIGENTE Y CONTEXTUAL:
   - Usa analyze_data_pandas para estadísticas profundas de cualquier dato
   - Interpreta los resultados en el contexto del dominio detectado
   - Identifica patrones, outliers, tendencias sin asumir el tipo de datos

4. 📈 VISUALIZACIÓN APROPIADA:
   - Elige gráficas basándote en el tipo de datos que encontraste
   - Usa columnas reales para ejes X e Y
   - Títulos descriptivos basados en datos reales

5. 🌐 CONTEXTO COMPLEMENTARIO INTELIGENTE:
   - Usa búsquedas web para contexto relevante al dominio detectado
   - Adapta términos de búsqueda al tema de los datos
   - Al final, usa create_sources_section para formatear automáticamente todas las fuentes web

INSTRUCCIONES OBLIGATORIAS:

✅ SIEMPRE EXPLORA PRIMERO:
- Comienza OBLIGATORIAMENTE con get_database_schema
- NO asumas NADA sobre nombres de tablas o columnas
- Basa TODO tu análisis en la información real del esquema

✅ SQL COMPLETAMENTE DINÁMICO:
- Construye consultas usando nombres reales de tablas/columnas
- Usa las relaciones detectadas automáticamente
- Adapta filtros y agrupaciones a los datos disponibles
- Nunca hardcodees nombres de tablas o campos

✅ FORMATO PROFESIONAL:
- Usa create_formatted_markdown_table para datos tabulares importantes
- Incluye visualizaciones apropiadas para el tipo de datos
- Estructura tu respuesta en Markdown claro

✅ CITAS Y FUENTES:
- Si usas búsquedas web, usa SOLO la herramienta create_sources_section al final
- NO crees manualmente secciones "Fuentes Consultadas" - usa la herramienta
- Formato APA automático para todas las fuentes web
- Separa claramente datos locales de información web

✅ PALABRAS CLAVE INTELIGENTES:
- AL FINAL de tu análisis, incluye una sección "## 🏷️ Palabras Clave"
- Genera 5-10 palabras clave relevantes basándote en tu análisis realizado
- Incluye términos reales encontrados en los datos (nombres de tablas, columnas importantes, valores categóricos relevantes)
- Formato: "**Palabras clave:** [palabra1], [palabra2], [palabra3], ..."
- SÉ INTELIGENTE: basa las palabras clave en el contenido real de tu análisis

EJEMPLOS DE METODOLOGÍA DINÁMICA:

🎯 Paso 1 - Exploración:
```
1. get_database_schema() -> descubrir tablas "productos", "ventas", "clientes"
2. Identificar relaciones: ventas.producto_id → productos.id
3. Detectar columnas temporales: ventas.fecha
4. Detectar categóricas: productos.categoria, clientes.region
```

🎯 Paso 2 - Consulta dinámica:
```sql
-- Basado en esquema real descubierto
SELECT p.categoria, SUM(v.monto) as total_ventas
FROM ventas v 
JOIN productos p ON v.producto_id = p.id
WHERE v.fecha >= '2023-01-01'
GROUP BY p.categoria 
ORDER BY total_ventas DESC
```

🎯 Adaptabilidad:
- Si los datos son de salud: busca patrones médicos, usa terminología de salud
- Si son financieros: busca tendencias económicas, usa términos financieros  
- Si son alimentarios: busca patrones nutricionales, usa contexto de seguridad alimentaria
- El agente se adapta automáticamente al dominio de los datos

REGLAS CRÍTICAS:
❌ NUNCA asumas nombres de tablas específicas
❌ NUNCA uses queries hardcodeadas  
❌ NUNCA hagas suposiciones sobre la estructura de datos
❌ NUNCA crees manualmente secciones "Fuentes Consultadas"
✅ SIEMPRE explora primero con get_database_schema
✅ SIEMPRE construye queries dinámicamente
✅ SIEMPRE adapta tu análisis al tipo de datos encontrado
✅ USA create_sources_section para fuentes web (evita duplicados)

PREGUNTA DEL USUARIO:
"""
        return context + question

    def _format_response(self, result: str, original_question: str) -> str:
        """Formatea la respuesta del agente en Markdown estructurado."""

        # Si el resultado ya está bien formateado, devolverlo tal como está
        if result and "# " in result:
            return result

        # Si no, crear estructura básica
        formatted = f"""# Análisis de Inseguridad Alimentaria

## Pregunta
{original_question}

## Respuesta del Agente
{result}

## Metodología
Este análisis fue generado usando consultas SQL flexibles sobre la base de datos de inseguridad alimentaria de Colombia, con análisis estadísticos usando pandas y numpy, y visualizaciones con matplotlib.

---
*Generado por el Analista AI especializado en datos de inseguridad alimentaria. Puede cometer errores, por favor verifica la respuesta.*
"""
        return formatted

    def _generate_error_response(self, error_message: str, question: str) -> str:
        """Genera una respuesta de error estructurada."""
        return f"""# Error en el Análisis

## Pregunta
{question}

## Error Encontrado
```
{error_message}
```

## Posibles Soluciones
1. **Verificar la configuración**: Asegúrate de que GEMINI_API_KEY esté configurada
2. **Reformular la pregunta**: Intenta ser más específico sobre qué datos necesitas
3. **Revisar la base de datos**: Usa get_database_schema para explorar los datos disponibles

## Ejemplos de Preguntas Válidas
- "¿Cuál es la situación actual de inseguridad alimentaria en Colombia?"
- "¿Qué departamentos tienen mayor inseguridad alimentaria grave?"
- "¿Cómo ha evolucionado la inseguridad alimentaria en los últimos años?"
- "¿Cuáles son las estadísticas de inseguridad alimentaria por regiones?"
- "Compara la inseguridad alimentaria entre departamentos de la costa y del interior"

## Capacidades del Agente
- 🔍 Exploración dinámica de la base de datos
- 📊 Consultas SQL flexibles y personalizadas  
- 📈 Análisis estadísticos avanzados
- 📋 Visualizaciones automáticas
- 🌐 Información contextual web complementaria

---
*El agente es flexible y puede adaptarse a cualquier pregunta sobre inseguridad alimentaria*
"""

    def get_database_info(self) -> str:
        """
        Obtiene información básica sobre la base de datos disponible.

        Returns:
            Información sobre esquema y datos disponibles
        """
        try:
            # Usar la herramienta directamente
            return get_database_schema()
        except Exception as e:
            return f"Error obteniendo información de la base de datos: {str(e)}"

    def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión y configuración del agente.

        Returns:
            Estado de los componentes del sistema
        """
        status = {
            "database": False,
            "model": False,
            "agent": False,
            "api_key": False,
            "web_search": False,
            "errors": [],
        }

        try:
            # Verificar base de datos
            db_path = str(self.settings.database.db_path)
            if os.path.exists(db_path):
                status["database"] = True
            else:
                status["errors"].append(f"Base de datos no encontrada: {db_path}")

            # Verificar API key
            api_key = self.settings.api.gemini_api_key
            if api_key and api_key != "TU_API_KEY_DE_GEMINI_AQUI":
                status["api_key"] = True
            else:
                status["errors"].append("GEMINI_API_KEY no configurada")

            # Verificar modelo
            if self.model:
                status["model"] = True
            else:
                status["errors"].append("Modelo LiteLLM no inicializado")

            # Verificar agente
            if self.agent:
                status["agent"] = True
            else:
                status["errors"].append("CodeAgent no inicializado")

            # Verificar búsqueda web
            if self.web_search_tool:
                status["web_search"] = True
            else:
                status["errors"].append("WebSearchTool no disponible")

        except Exception as e:
            status["errors"].append(f"Error en verificación: {str(e)}")

        return status


# Instancia global del agente
try:
    food_security_agent = InseguridadAlimentariaAgent()
    print("✅ Agente SmolAgents flexible inicializado correctamente")
    print("🔧 El agente puede crear consultas SQL dinámicas para cualquier análisis")
except Exception as e:
    print(f"❌ Error inicializando agente: {e}")
    food_security_agent = None
