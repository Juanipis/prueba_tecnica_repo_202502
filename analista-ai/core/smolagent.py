"""
Agente SmolAgents para análisis de datos de inseguridad alimentaria.

Este módulo configura un CodeAgent que puede:
- Consultar la base de datos SQLite usando SQL directo
- Realizar análisis estadísticos con pandas y numpy
- Autocorregirse si las consultas son incorrectas
- Iterar hasta obtener resultados correctos
- Crear visualizaciones con matplotlib
"""

import os
from typing import Dict, Any, List
from smolagents import CodeAgent, LiteLLMModel
from .settings import get_settings
from .sql_tools import (
    sql_query,
    get_database_schema,
    analyze_data_pandas,
    get_top_entities,
    compare_years,
    calculate_statistics,
    create_formatted_table,
    get_available_years,
    get_available_indicators,
    get_entities_by_level,
    quick_summary,
    create_chart_visualization,
    create_multiple_charts,
    analyze_and_visualize
)


class InseguridadAlimentariaAgent:
    """
    Agente especializado en análisis de datos de inseguridad alimentaria en Colombia.
    
    Utiliza SmolAgents con LiteLLM para conectar con Gemini y generar análisis
    inteligentes usando consultas SQL directas y análisis estadísticos.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.agent = None
        self._initialize_model()
        self._initialize_agent()
    
    def _initialize_model(self):
        """Inicializa el modelo LiteLLM con Gemini usando configuración tipada."""
        api_config = self.settings.api
        
        if not api_config.gemini_api_key or api_config.gemini_api_key == "TU_API_KEY_DE_GEMINI_AQUI":
            print("⚠️ Advertencia: GEMINI_API_KEY no configurada correctamente")
            print("🔧 Configura tu API key en el archivo .env")
            # Usar modelo por defecto para testing
            self.model = LiteLLMModel(model_id=api_config.gemini_model)
        else:
            self.model = LiteLLMModel(
                model_id=api_config.gemini_model,
                api_key=api_config.gemini_api_key,
                temperature=api_config.gemini_temperature,
                max_tokens=api_config.gemini_max_tokens
            )
    
    def _initialize_agent(self):
        """Inicializa el CodeAgent con todas las herramientas disponibles."""
        tools = [
            sql_query,
            get_database_schema,
            analyze_data_pandas,
            get_top_entities,
            compare_years,
            calculate_statistics,
            create_formatted_table,
            get_available_years,
            get_available_indicators,
            get_entities_by_level,
            quick_summary,
            create_chart_visualization,
            create_multiple_charts,
            analyze_and_visualize
        ]
        
        agent_config = self.settings.agent
        
        self.agent = CodeAgent(
            tools=tools,
            model=self.model,
            additional_authorized_imports=agent_config.authorized_imports,
            max_steps=agent_config.max_steps,
            verbosity_level=agent_config.verbosity_level
        )
    
    def analyze_question(self, question: str) -> str:
        """
        Analiza una pregunta en lenguaje natural sobre inseguridad alimentaria.
        
        El agente:
        1. Interpreta la pregunta
        2. Decide qué herramientas usar
        3. Escribe código Python para consultar los datos
        4. Analiza los resultados
        5. Se autocorrige si algo está mal
        6. Genera una respuesta en Markdown
        
        Args:
            question: Pregunta del usuario en lenguaje natural
            
        Returns:
            Análisis completo en formato Markdown
        """
        try:
            # Preparar el prompt con contexto específico
            enhanced_question = self._enhance_question_with_context(question)
            
            # Ejecutar el agente
            result = self.agent.run(enhanced_question)
            
            return self._format_response(result, question)
            
        except Exception as e:
            error_message = f"Error ejecutando análisis: {str(e)}"
            print(f"❌ {error_message}")
            
            return self._generate_error_response(error_message, question)
    
    def _enhance_question_with_context(self, question: str) -> str:
        """
        Mejora la pregunta del usuario con contexto sobre la base de datos y capacidades.
        """
        context = """
Eres un analista experto en datos de inseguridad alimentaria en Colombia. 

CONTEXTO DE LA BASE DE DATOS:
- Tienes acceso a datos normalizados de inseguridad alimentaria en Colombia
- Los datos incluyen información nacional, regional, departamental y municipal
- Período: principalmente 2022-2024, con algunos datos de 2015
- 3 indicadores principales:
  1. "Inseguridad Alimentaria Grave" 
  2. "Inseguridad Alimentaria Moderado o Grave"
  3. "Prevalencia de hogares en inseguridad alimentaria"

HERRAMIENTAS DISPONIBLES:
- sql_query: Para consultas SQL directas
- get_database_schema: Para explorar la estructura de datos
- analyze_data_pandas: Para análisis estadísticos avanzados
- get_top_entities: Para rankings de entidades
- compare_years: Para análisis temporal
- calculate_statistics: Para estadísticas descriptivas
- create_chart_visualization: Para crear gráficas individuales con matplotlib
- create_multiple_charts: Para crear múltiples gráficas
- analyze_and_visualize: Para análisis completo con gráficas automáticas

INSTRUCCIONES PARA VISUALIZACIONES:
1. SIEMPRE incluye gráficas cuando sea apropiado para mostrar datos
2. Usa create_chart_visualization para gráficas específicas
3. Usa analyze_and_visualize para análisis completos con visualizaciones automáticas
4. Los tipos de gráficas disponibles son: bar, line, pie, scatter, histogram
5. Las herramientas son TOKEN-EFICIENTES: solo retornan confirmaciones cortas
6. Las gráficas se almacenan temporalmente y aparecen automáticamente en el frontend
7. NO esperes recibir imágenes base64 en las respuestas de las herramientas
8. Incluye títulos descriptivos y especifica columnas para mejor visualización

INSTRUCCIONES GENERALES:
1. SIEMPRE empieza explorando la base de datos si no estás seguro del esquema
2. Usa consultas SQL precisas y bien estructuradas
3. Si una consulta falla, analiza el error y corrígela
4. Proporciona análisis estadísticos relevantes
5. Presenta los resultados en formato Markdown estructurado
6. Incluye contexto y interpretación de los datos
7. Si los datos son limitados, menciona las limitaciones
8. TODAS LAS PREGUNTAS DEBEN SER ENFOCADAS EN EL ANÁLISIS DE INSEGURIDAD ALIMENTARIA EN COLOMBIA,  NO SE DEBEN HACER PREGUNTAS QUE NO SEAN RELACIONADAS CON LA INSEGURIDAD ALIMENTARIA EN COLOMBIA. SI HACES UNA PREGUNTA QUE NO SEA RELACIONADA CON LA INSEGURIDAD ALIMENTARIA EN COLOMBIA, SE RECHAZA LA PREGUNTA.
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
Este análisis fue generado usando consultas SQL directas sobre la base de datos normalizada de inseguridad alimentaria de Colombia, con análisis estadísticos usando pandas y numpy.

---
*Generado por el Analista AI especializado en datos de inseguridad alimentaria, puede cometer errores, por favor verifica la respuesta y corrige los errores.*
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
3. **Revisar la base de datos**: Los datos están disponibles principalmente para 2022-2024

## Ejemplos de Preguntas Válidas
- "¿Cuál es la situación de inseguridad alimentaria en Colombia?"
- "¿Qué departamentos tienen mayor inseguridad alimentaria grave en 2022?"
- "¿Cómo evolucionó la inseguridad alimentaria en Antioquia?"
- "¿Cuáles son las estadísticas descriptivas de inseguridad alimentaria moderada en 2023?"


---
*Por favor, verifica la configuración e intenta nuevamente*
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
            "errors": []
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
                
        except Exception as e:
            status["errors"].append(f"Error en verificación: {str(e)}")
        
        return status


# Instancia global del agente
try:
    food_security_agent = InseguridadAlimentariaAgent()
    print("✅ Agente SmolAgents inicializado correctamente")
except Exception as e:
    print(f"❌ Error inicializando agente: {e}")
    food_security_agent = None 