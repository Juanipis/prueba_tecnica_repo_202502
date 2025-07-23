"""
Aplicación FastAPI para el Analista de Datos AI de Inseguridad Alimentaria.

Esta aplicación utiliza SmolAgents para crear un agente inteligente que:
- Analiza preguntas en lenguaje natural
- Escribe consultas SQL dinámicamente  
- Realiza análisis estadísticos
- Se autocorrige si hay errores
- Genera respuestas estructuradas en Markdown
"""

import os
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from core.smolagent import food_security_agent
from core.settings import get_settings, print_settings_summary

# Obtener configuración
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación.
    """
    # Startup
    print("🚀 Iniciando aplicación SmolAgents...")
    if food_security_agent:
        status = food_security_agent.test_connection()
        if status["database"] and status["agent"]:
            print("✅ Agente SmolAgents inicializado y listo")
        else:
            print("⚠️ Agente con problemas:", status["errors"])
    else:
        print("❌ Error: Agente no inicializado")
    
    yield
    
    # Shutdown
    print("🔄 Cerrando aplicación...")


# Crear aplicación FastAPI usando configuración
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.server.debug,
    lifespan=lifespan
)

# Configurar CORS usando configuración
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=settings.server.cors_allow_credentials,
    allow_methods=settings.server.cors_allow_methods,
    allow_headers=settings.server.cors_allow_headers,
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=settings.server.static_directory), name="static")


# Modelos Pydantic
class QuestionRequest(BaseModel):
    question: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "¿Qué departamentos tienen mayor inseguridad alimentaria grave en 2022?"
            }
        }


class AnalysisResponse(BaseModel):
    question: str
    analysis: str
    agent_used: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "¿Qué departamentos tienen mayor inseguridad alimentaria grave en 2022?",
                "analysis": "# Análisis de Inseguridad Alimentaria\n\n## Departamentos con Mayor Inseguridad...",
                "agent_used": "SmolAgent CodeAgent",
                "success": True
            }
        }


# ===== ENDPOINTS PRINCIPALES =====

@app.get("/", response_class=FileResponse)
async def home():
    """Servir el frontend principal."""
    return FileResponse(f'{settings.server.static_directory}/index.html')

@app.get("/api-info", response_class=HTMLResponse)
async def api_info():
    """Página de información sobre la API SmolAgents (versión anterior)."""
    api_key_status = "✅ Configurada" if (
        settings.api.gemini_api_key and 
        settings.api.gemini_api_key != "TU_API_KEY_DE_GEMINI_AQUI"
    ) else "❌ No configurada"
    
    agent_status = "✅ Activo" if food_security_agent else "❌ Error"
    
    web_search_status = "✅ Disponible" if (
        food_security_agent and 
        hasattr(food_security_agent, 'web_search_tool') and 
        food_security_agent.web_search_tool
    ) else "❌ No disponible"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analista AI - Información de la API</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                   margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; min-height: 100vh; }}
            .container {{ max-width: 900px; margin: 0 auto; background: rgba(255,255,255,0.1); 
                        padding: 40px; border-radius: 20px; backdrop-filter: blur(10px);
                        box-shadow: 0 8px 32px rgba(0,0,0,0.2); }}
            h1 {{ color: #fff; border-bottom: 3px solid #4CAF50; padding-bottom: 15px;
                 text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
            h2 {{ color: #E8F5E8; margin-top: 30px; }}
            .status {{ padding: 15px; border-radius: 10px; margin: 20px 0; font-weight: bold; }}
            .success {{ background: rgba(76, 175, 80, 0.3); border: 2px solid #4CAF50; }}
            .warning {{ background: rgba(255, 193, 7, 0.3); border: 2px solid #FFC107; }}
            .error {{ background: rgba(244, 67, 54, 0.3); border: 2px solid #F44336; }}
            .endpoint {{ background: rgba(255,255,255,0.1); padding: 20px; margin: 15px 0; 
                       border-radius: 10px; border-left: 5px solid #4CAF50; }}
            code {{ background: rgba(0,0,0,0.3); padding: 4px 8px; border-radius: 6px; 
                   font-family: 'Courier New', monospace; }}
            .feature {{ background: rgba(255,255,255,0.05); padding: 15px; margin: 10px 0;
                       border-radius: 8px; border-left: 3px solid #2196F3; }}
            a {{ color: #4CAF50; text-decoration: none; font-weight: bold; }}
            a:hover {{ color: #81C784; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
            @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}
            .home-link {{ display: inline-block; margin-bottom: 20px; padding: 10px 20px;
                         background: #4CAF50; color: white; text-decoration: none;
                         border-radius: 8px; transition: all 0.3s; }}
            .home-link:hover {{ background: #45a049; transform: translateY(-2px); }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="home-link">🏠 Volver al Frontend Principal</a>
            
            <h1>🤖 Analista de Datos AI</h1>
            <h2>Información de la API - Powered by SmolAgents + Gemini</h2>
            
            <div class="status {'success' if food_security_agent else 'error'}">
                🚀 <strong>SmolAgent:</strong> {agent_status}
            </div>
            
            <div class="status {'success' if api_key_status.startswith('✅') else 'warning'}">
                🔑 <strong>API Gemini:</strong> {api_key_status}
            </div>
            
            <div class="status {'success' if web_search_status.startswith('✅') else 'warning'}">
                🔍 <strong>Búsqueda Web:</strong> {web_search_status}
            </div>
            
            <h2>🔍 Endpoint Principal</h2>
            <div class="endpoint">
                <strong>POST /analyze</strong><br>
                Realiza análisis inteligente usando SmolAgent con autocorrección
                
                <div style="margin-top: 15px; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px;">
                    <strong>Ejemplo:</strong><br>
                    <code>
                    POST /analyze<br>
                    {{"question": "¿Qué departamentos tienen mayor inseguridad alimentaria en 2022?"}}
                    </code>
                </div>
            </div>
            
            <div class="grid">
                <div>
                    <h2>✨ Características SmolAgents</h2>
                    <div class="feature">
                        <strong>🔄 Autocorrección</strong><br>
                        Si una consulta SQL falla, el agente la corrige automáticamente
                    </div>
                    <div class="feature">
                        <strong>📊 SQL Dinámico</strong><br>
                        Escribe consultas SQL según la pregunta específica
                    </div>
                    <div class="feature">
                        <strong>📈 Análisis Estadístico</strong><br>
                        Integración con pandas/numpy para análisis avanzados
                    </div>
                    <div class="feature">
                        <strong>🔍 Búsqueda Web</strong><br>
                        Complementa análisis con información actualizada de internet
                    </div>
                </div>
                
                <div>
                    <h2>🌐 Otros Endpoints</h2>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin: 10px 0;">📋 <code>GET /schema</code> - Esquema de base de datos</li>
                        <li style="margin: 10px 0;">❤️ <code>GET /health</code> - Estado del sistema</li>
                        <li style="margin: 10px 0;">📊 <code>GET /status</code> - Estado detallado del agente</li>
                        <li style="margin: 10px 0;">📖 <code>GET /docs</code> - Documentación Swagger</li>
                    </ul>
                </div>
            </div>
            
            <h2>💡 Ejemplos de Preguntas</h2>
            <div class="grid">
                <div>
                    <div class="feature">
                        "¿Cuál es la situación de inseguridad alimentaria en Colombia?"
                    </div>
                    <div class="feature">
                        "¿Qué departamentos tienen mayor inseguridad alimentaria grave en 2022?"
                    </div>
                </div>
                <div>
                    <div class="feature">
                        "Compara la evolución entre Antioquia y Cundinamarca"
                    </div>
                    <div class="feature">
                        "Muestra estadísticas descriptivas de inseguridad moderada en 2023"
                    </div>
                </div>
            </div>
            
            <h2>📚 Documentación</h2>
            <p>
                <a href="/docs" target="_blank">📖 Swagger UI</a> - 
                <a href="/redoc" target="_blank">📑 ReDoc</a> -
                <a href="/" target="_blank">🏠 Frontend Principal</a>
            </p>
            
            <hr style="border: 1px solid rgba(255,255,255,0.2); margin: 30px 0;">
            <p style="text-align: center; color: rgba(255,255,255,0.7); font-size: 14px;">
                Powered by FastAPI + SmolAgents + LiteLLM + Gemini AI<br>
                Datos de inseguridad alimentaria de Colombia (2022-2024)
            </p>
        </div>
    </body>
    </html>
    """
    return html_content


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_question(request: QuestionRequest):
    """
    Analiza una pregunta usando el agente SmolAgents.
    
    El agente:
    1. Interpreta la pregunta en lenguaje natural
    2. Escribe código Python con consultas SQL dinámicas
    3. Ejecuta análisis estadísticos si es necesario
    4. Se autocorrige si hay errores
    5. Genera respuesta estructurada en Markdown
    6. Las imágenes se manejan de manera token-eficiente
    """
    if not food_security_agent:
        raise HTTPException(
            status_code=503,
            detail="Agente SmolAgents no disponible. Verifica la configuración."
        )
    
    try:
        # Limpiar almacenamiento de imágenes previo
        from core.sql_tools import clear_stored_images, get_stored_images
        clear_stored_images()
        
        # Ejecutar análisis con el agente
        analysis = food_security_agent.analyze_question(request.question)
        
        # Obtener imágenes generadas durante el análisis
        stored_images = get_stored_images()
        
        # Si hay imágenes, inyectarlas en el markdown
        if stored_images:
            print(f"🖼️ Inyectando {len(stored_images)} imágenes en la respuesta")
            # Crear sección de visualizaciones si no existe
            if "## 📈 Visualizaciones" not in analysis and "📈 Visualizaciones Generadas" not in analysis:
                analysis += "\n\n## 📈 Visualizaciones Generadas\n\n"
            
            # Inyectar cada imagen en el markdown
            for image_id, image_info in stored_images.items():
                title = image_info['title']
                image_data = image_info['data']
                chart_type = image_info['type']
                
                print(f"  📊 {title} ({chart_type}) - {len(image_data)} caracteres")
                
                # Agregar imagen al markdown
                analysis += f"\n### {title}\n"
                analysis += f"![{title}]({image_data})\n\n"
        
        # Limpiar almacenamiento temporal
        clear_stored_images()
        
        web_search_indicator = " + Web Search" if (
            food_security_agent and 
            hasattr(food_security_agent, 'web_search_tool') and 
            food_security_agent.web_search_tool
        ) else ""
        
        return AnalysisResponse(
            question=request.question,
            analysis=analysis,
            agent_used=f"SmolAgent CodeAgent with Gemini{web_search_indicator} (Token-Optimized)",
            success=True
        )
        
    except Exception as e:
        # Limpiar almacenamiento en caso de error
        from core.sql_tools import clear_stored_images
        clear_stored_images()
        
        # En caso de error, aún intentar devolver información útil
        error_analysis = food_security_agent._generate_error_response(str(e), request.question) if food_security_agent else f"Error: {str(e)}"
        
        return AnalysisResponse(
            question=request.question,
            analysis=error_analysis,
            agent_used="SmolAgent (Error Mode)",
            success=False
        )


# ===== ENDPOINTS DE INFORMACIÓN =====

@app.get("/schema")
async def get_database_schema():
    """Obtiene el esquema completo de la base de datos."""
    if not food_security_agent:
        raise HTTPException(
            status_code=503,
            detail="Agente no disponible"
        )
    
    try:
        schema_info = food_security_agent.get_database_info()
        return {"schema": schema_info}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo esquema: {str(e)}"
        )


@app.get("/status")
async def get_agent_status():
    """Obtiene el estado detallado del agente y sus componentes."""
    if not food_security_agent:
        return {
            "agent_available": False,
            "error": "Agente SmolAgents no inicializado",
            "components": {
                "database": False,
                "model": False,
                "agent": False,
                "api_key": False,
                "web_search": False
            }
        }
    
    try:
        status = food_security_agent.test_connection()
        return {
            "agent_available": True,
            "components": {
                "database": status["database"],
                "model": status["model"], 
                "agent": status["agent"],
                "api_key": status["api_key"],
                "web_search": status["web_search"]
            },
            "errors": status["errors"],
            "system_ready": all([
                status["database"],
                status["model"],
                status["agent"]
            ])
        }
    except Exception as e:
        return {
            "agent_available": False,
            "error": f"Error verificando estado: {str(e)}",
            "components": {
                "database": False,
                "model": False,
                "agent": False,
                "api_key": False,
                "web_search": False
            }
        }


@app.get("/health")
async def health_check():
    """Verifica el estado básico del sistema."""
    db_exists = os.path.exists(str(settings.database.db_path))
    api_key_configured = bool(
        settings.api.gemini_api_key and 
        settings.api.gemini_api_key != "TU_API_KEY_DE_GEMINI_AQUI"
    )
    agent_available = food_security_agent is not None
    web_search_available = bool(
        food_security_agent and 
        hasattr(food_security_agent, 'web_search_tool') and 
        food_security_agent.web_search_tool
    )
    
    return {
        "status": "healthy" if (db_exists and agent_available) else "degraded",
        "database": "OK" if db_exists else "ERROR",
        "agent": "OK" if agent_available else "ERROR", 
        "api_key": "OK" if api_key_configured else "NOT_CONFIGURED",
        "web_search": "OK" if web_search_available else "NOT_AVAILABLE",
        "message": "Sistema SmolAgents operativo" if (db_exists and agent_available) else "Revisar configuración"
    }


# ===== ENDPOINTS DE UTILIDAD =====

@app.get("/examples")
async def get_examples():
    """Obtiene ejemplos de preguntas que se pueden hacer al agente."""
    examples = {
        "basicas": [
            "¿Cuál es la situación de inseguridad alimentaria en Colombia?",
            "¿Qué departamentos tienen mayor inseguridad alimentaria en 2022?",
            "¿Cómo está la situación en Antioquia?"
        ],
        "comparativas": [
            "Compara la inseguridad alimentaria entre Antioquia y Cundinamarca",
            "¿Cuál es la diferencia entre inseguridad grave y moderada?",
            "Compara los datos de 2022 vs 2023"
        ],
        "estadisticas_con_tablas": [
            "¿Cuáles son las estadísticas descriptivas de inseguridad moderada en 2023? Muestra los resultados en una tabla",
            "Calcula la media y desviación estándar por departamento y presenta en tabla formateada",
            "¿Cuál es la distribución de inseguridad alimentaria por regiones? Incluye tabla y palabras clave del análisis"
        ],
        "rankings": [
            "Muestra los 10 departamentos con mayor inseguridad alimentaria",
            "¿Cuáles son los 5 municipios más afectados en Antioquia?",
            "Ranking de regiones por prevalencia de inseguridad"
        ],
        "temporales": [
            "¿Cómo ha evolucionado la inseguridad alimentaria en Colombia?",
            "Muestra la tendencia temporal para Bogotá",
            "¿En qué años hubo mayor inseguridad alimentaria?"
        ],
        "visualizaciones": [
            "Crea una gráfica de barras que muestre los 10 departamentos con mayor inseguridad alimentaria grave en 2022",
            "Analiza con gráficas la distribución de inseguridad alimentaria por regiones en Colombia",
            "Haz un análisis completo con visualizaciones de la evolución temporal",
            "Genera múltiples gráficas: una de barras por departamento y otra circular por regiones",
            "Crea un histograma de la distribución de inseguridad moderada en 2023"
        ],
        "contextuales_con_citas": [
            "¿Cuáles son las principales políticas públicas de Colombia para combatir la inseguridad alimentaria y cómo se relacionan con nuestros datos? (incluye fuentes)",
            "Analiza la situación de inseguridad alimentaria en Chocó y complementa con información sobre las causas del conflicto armado con fuentes verificables",
            "Compara nuestros datos con estadísticas internacionales de inseguridad alimentaria en América Latina y cita las fuentes consultadas",
            "¿Qué programas gubernamentales actuales existen para atender la inseguridad alimentaria en las zonas más afectadas? (con referencias web)",
            "Contextualiza los datos de 2022-2024 con eventos recientes que puedan haber afectado la seguridad alimentaria, citando fuentes confiables",
            "Investiga las causas principales de inseguridad alimentaria en Colombia según organizaciones internacionales y contrasta con nuestros datos"
        ]
    }
    
    return {
        "message": "Ejemplos de preguntas para el agente SmolAgents",
        "categories": examples,
        "tip": "El agente puede combinar múltiples tipos de análisis en una sola consulta"
    }


if __name__ == "__main__":
    print("🚀 Iniciando servidor FastAPI con SmolAgents...")
    print_settings_summary()
    print(f"📖 Documentación: http://{settings.server.host}:{settings.server.port}/docs")
    print(f"🏠 Página principal: http://{settings.server.host}:{settings.server.port}")
    print(f"🤖 Análisis AI: POST http://{settings.server.host}:{settings.server.port}/analyze")
    
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        log_level=settings.logging.log_level.lower()
    ) 