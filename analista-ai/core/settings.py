"""
Configuración de la aplicación usando Pydantic Settings.

Este módulo define toda la configuración de la aplicación de manera tipada,
con validación automática y soporte para múltiples fuentes de configuración.
"""

from pathlib import Path
from typing import Optional, List, Literal
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class DatabaseSettings(BaseSettings):
    """Configuración de base de datos."""

    # Ruta por defecto relativa al backend
    db_path: Path = Field(
        default="../data/sqlite_databases/inseguridad_alimentaria_latest.db",
        description="Ruta a la base de datos SQLite",
    )

    # Configuraciones adicionales para futuras expansiones
    connection_timeout: int = Field(
        default=30, description="Timeout de conexión en segundos"
    )
    max_retries: int = Field(default=3, description="Máximo número de reintentos")

    @validator("db_path")
    def validate_db_exists(cls, v):
        """Valida que la base de datos exista."""
        if not Path(v).exists():
            print(f"⚠️ Advertencia: Base de datos no encontrada en {v}")
        return v


class DatabaseContextSettings(BaseSettings):
    """Configuración del contexto específico de la base de datos."""

    # Ruta al archivo de contexto específico
    context_file_path: Path = Field(
        default=Path(__file__).parent / "database_context.txt",
        description="Ruta al archivo de contexto específico de la base de datos",
    )

    # Configuración de contexto
    include_context_in_prompt: bool = Field(
        default=True, description="Incluir contexto específico en el prompt del agente"
    )

    context_max_length: int = Field(
        default=3000, gt=0, description="Longitud máxima del contexto en caracteres"
    )

    @validator("context_file_path")
    def validate_context_file_exists(cls, v):
        """Valida que el archivo de contexto exista."""
        if not Path(v).exists():
            print(f"⚠️ Advertencia: Archivo de contexto no encontrado en {v}")
        return v

    def get_context_content(self) -> str:
        """
        Lee y retorna el contenido del archivo de contexto.

        Returns:
            Contenido del archivo de contexto truncado según max_length
        """
        try:
            if self.context_file_path.exists():
                content = self.context_file_path.read_text(encoding="utf-8")
                if len(content) > self.context_max_length:
                    content = (
                        content[: self.context_max_length]
                        + "\n\n[... contenido truncado ...]"
                    )
                return content
            else:
                return "⚠️ Archivo de contexto no disponible."
        except Exception as e:
            return f"❌ Error leyendo contexto: {str(e)}"


class APISettings(BaseSettings):
    """Configuración de APIs externas."""

    gemini_api_key: str = Field(
        default="TU_API_KEY_DE_GEMINI_AQUI", description="API Key de Google Gemini"
    )

    # Configuraciones del modelo Gemini
    gemini_model: str = Field(
        default="gemini/gemini-2.5-flash-lite",
        description="Modelo de Gemini a utilizar",
    )

    gemini_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperatura del modelo (0.0 = determinístico, 2.0 = muy creativo)",
    )

    gemini_max_tokens: int = Field(
        default=4000, gt=0, description="Máximo número de tokens en la respuesta"
    )

    @validator("gemini_api_key")
    def validate_gemini_key(cls, v):
        """Valida que la API key de Gemini esté configurada."""
        if not v or v == "TU_API_KEY_DE_GEMINI_AQUI":
            print("⚠️ Advertencia: GEMINI_API_KEY no configurada correctamente")
            print("🔧 Configura tu API key en el archivo .env")
        return v


class SmolAgentSettings(BaseSettings):
    """Configuración específica del SmolAgent."""

    max_steps: int = Field(
        default=15,
        gt=0,
        le=50,
        description="Máximo número de pasos para autocorrección",
    )

    verbosity_level: int = Field(
        default=1,
        ge=0,
        le=3,
        description="Nivel de verbosidad (0=silencioso, 3=muy detallado)",
    )

    authorized_imports: List[str] = Field(
        default=[
            "pandas",
            "numpy",
            "sqlite3",
            "tabulate",
            "subprocess",
            "matplotlib",
            "seaborn",
            "openpyxl",
            "json",
            "csv",
            "pathlib",
            "os",
            "sys",
            "warnings",
        ],
        description="Lista de módulos autorizados para importar",
    )

    enable_code_execution: bool = Field(
        default=True, description="Permitir ejecución de código Python"
    )


class ServerSettings(BaseSettings):
    """Configuración del servidor FastAPI."""

    host: str = Field(default="127.0.0.1", description="Host del servidor")
    port: int = Field(default=8000, gt=0, le=65535, description="Puerto del servidor")
    reload: bool = Field(default=True, description="Auto-reload en desarrollo")
    debug: bool = Field(default=True, description="Modo debug")

    # CORS
    cors_origins: List[str] = Field(
        default=["*"], description="Orígenes permitidos para CORS"
    )

    cors_allow_credentials: bool = Field(
        default=True, description="Permitir credenciales en CORS"
    )
    cors_allow_methods: List[str] = Field(
        default=["*"], description="Métodos HTTP permitidos"
    )
    cors_allow_headers: List[str] = Field(
        default=["*"], description="Headers permitidos"
    )

    # Static files
    static_directory: str = Field(
        default="static", description="Directorio de archivos estáticos"
    )


class RAGSettings(BaseSettings):
    """Configuración del sistema RAG (Retrieval-Augmented Generation)."""

    # Configuración de la base de datos vectorial
    vector_db_path: Path = Field(
        default="../data/rag/vector_db_faiss/",
        description="Ruta a la base de datos vectorial FAISS",
    )

    # Configuración del modelo de embeddings
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Modelo de embeddings para el RAG",
    )

    # Configuración de búsqueda
    top_k_results: int = Field(
        default=5,
        gt=0,
        le=20,
        description="Número de documentos relevantes a recuperar",
    )

    # Configuración de fragmentación para búsquedas
    max_chunk_size: int = Field(
        default=1000, gt=0, description="Tamaño máximo de los fragmentos de texto"
    )

    chunk_overlap: int = Field(
        default=200, ge=0, description="Superposición entre fragmentos de texto"
    )

    # Configuración de habilitación
    enable_rag: bool = Field(default=True, description="Habilitar el sistema RAG")

    # Configuración de relevancia
    similarity_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Umbral mínimo de similitud para considerar un documento relevante",
    )

    @validator("vector_db_path")
    def validate_vector_db_path(cls, v):
        """Valida que la ruta de la base de datos vectorial exista."""
        if not Path(v).exists():
            print(f"⚠️ Advertencia: Base de datos vectorial no encontrada en {v}")
            print("💡 Ejecuta data/rag/rag_estractor.py para crear la base de datos")
        return v


class LoggingSettings(BaseSettings):
    """Configuración de logging."""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Nivel de logging"
    )

    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Formato de logs",
    )

    log_to_file: bool = Field(default=False, description="Guardar logs en archivo")
    log_file_path: Optional[Path] = Field(
        default=None, description="Ruta del archivo de logs"
    )


class AppSettings(BaseSettings):
    """Configuración principal de la aplicación."""

    # Metadatos de la aplicación
    app_name: str = Field(
        default="Analista AI - Inseguridad Alimentaria Colombia",
        description="Nombre de la aplicación",
    )

    app_version: str = Field(default="2.0.0", description="Versión de la aplicación")

    app_description: str = Field(
        default="Sistema de análisis inteligente de datos de inseguridad alimentaria en Colombia usando SmolAgents.",
        description="Descripción de la aplicación",
    )

    # Configuraciones de sub-módulos
    database: DatabaseSettings = DatabaseSettings()
    database_context: DatabaseContextSettings = DatabaseContextSettings()
    api: APISettings = APISettings()
    agent: SmolAgentSettings = SmolAgentSettings()
    rag: RAGSettings = RAGSettings()
    server: ServerSettings = ServerSettings()
    logging: LoggingSettings = LoggingSettings()

    # Entorno
    environment: Literal["development", "testing", "production"] = Field(
        default="development", description="Entorno de ejecución"
    )

    class Config:
        extra = "allow"


# Instancia global de configuración
settings = AppSettings()


def get_settings() -> AppSettings:
    """
    Obtiene la instancia de configuración.

    Returns:
        Configuración de la aplicación
    """
    return settings


def reload_settings() -> AppSettings:
    """
    Recarga la configuración desde las fuentes.

    Returns:
        Nueva instancia de configuración
    """
    global settings
    settings = AppSettings()
    return settings


def print_settings_summary():
    """Imprime un resumen de la configuración actual."""
    print("🔧 CONFIGURACIÓN DE LA APLICACIÓN")
    print("=" * 50)
    print(f"📱 Aplicación: {settings.app_name} v{settings.app_version}")
    print(f"🌍 Entorno: {settings.environment}")
    print(f"🖥️  Servidor: {settings.server.host}:{settings.server.port}")
    print(f"📊 Base de datos: {settings.database.db_path}")
    print(
        f"📋 Contexto BD: {'✅ Habilitado' if settings.database_context.include_context_in_prompt else '❌ Deshabilitado'}"
    )
    print(
        f"🤖 SmolAgent: {settings.agent.max_steps} pasos máx, verbosidad {settings.agent.verbosity_level}"
    )
    print(
        f"🔑 API Gemini: {'✅ Configurada' if settings.api.gemini_api_key and settings.api.gemini_api_key != 'TU_API_KEY_DE_GEMINI_AQUI' else '❌ No configurada'}"
    )
    print(f"📝 Logging: {settings.logging.log_level}")
    print("-" * 50)


if __name__ == "__main__":
    # Prueba de configuración
    print_settings_summary()
