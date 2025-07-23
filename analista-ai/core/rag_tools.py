"""
Herramientas RAG (Retrieval-Augmented Generation) para SmolAgents.

Este módulo proporciona herramientas para realizar búsquedas semánticas
en la base de datos vectorial de documentos sobre seguridad alimentaria.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from smolagents import tool
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from .settings import get_settings


class RAGSourceTracker:
    """Clase para rastrear las fuentes RAG utilizadas en una sesión."""

    def __init__(self):
        self._sources_used = {}  # session_id -> List[Dict]

    def add_source(self, session_id: str, query: str, documents: List[Dict[str, Any]]):
        """
        Registra las fuentes utilizadas en una búsqueda RAG.

        Args:
            session_id: ID de la sesión actual
            query: Consulta realizada
            documents: Lista de documentos encontrados con metadata
        """
        if session_id not in self._sources_used:
            self._sources_used[session_id] = []

        for doc in documents:
            source_info = {
                "query": query,
                "content_preview": doc.get("content", "")[:200] + "..."
                if len(doc.get("content", "")) > 200
                else doc.get("content", ""),
                "metadata": doc.get("metadata", {}),
                "source_file": doc.get("metadata", {}).get(
                    "source", "Documento especializado"
                ),
                "page": doc.get("metadata", {}).get("page", None),
            }
            self._sources_used[session_id].append(source_info)

    def get_sources(self, session_id: str) -> List[Dict[str, Any]]:
        """Obtiene las fuentes utilizadas en una sesión."""
        return self._sources_used.get(session_id, [])

    def clear_sources(self, session_id: str):
        """Limpia las fuentes de una sesión."""
        if session_id in self._sources_used:
            del self._sources_used[session_id]

    def format_rag_sources(self, session_id: str) -> str:
        """
        Formatea las fuentes RAG para mostrar al usuario.

        Returns:
            Sección formateada de referencias RAG en Markdown
        """
        sources = self.get_sources(session_id)
        if not sources:
            return ""

        # Eliminar duplicados basándose en source_file y página
        unique_sources = {}
        for source in sources:
            key = f"{source['source_file']}_{source.get('page', 'N/A')}"
            if key not in unique_sources:
                unique_sources[key] = source

        formatted = "\n## 📚 Referencias RAG - Documentos Especializados\n\n"

        for i, source in enumerate(unique_sources.values(), 1):
            source_file = source["source_file"]
            page = source.get("page")
            content_preview = source["content_preview"]

            # Formatear la referencia
            if page:
                reference = f"{i}. **{source_file}** (Página {page})"
            else:
                reference = f"{i}. **{source_file}**"

            formatted += f"{reference}\n"
            formatted += f'   *Extracto:* "{content_preview}"\n\n'

        formatted += "---\n*Referencias extraídas de la base de conocimientos especializada sobre seguridad alimentaria*\n"

        return formatted


# Instancia global del rastreador de fuentes
_rag_source_tracker = RAGSourceTracker()


class RAGRetriever:
    """Clase para manejar la carga y búsqueda en la base de datos vectorial."""

    def __init__(self):
        self.settings = get_settings()
        self.vector_store = None
        self.embeddings = None
        self._initialize_rag()

    def _initialize_rag(self):
        """Inicializa el sistema RAG cargando la base de datos vectorial."""
        try:
            if not self.settings.rag.enable_rag:
                print("🔄 RAG deshabilitado en configuración")
                return

            vector_db_path = Path(self.settings.rag.vector_db_path)

            if not vector_db_path.exists():
                print(f"⚠️ Base de datos vectorial no encontrada en: {vector_db_path}")
                print(
                    "💡 Ejecuta 'python data/rag/rag_estractor.py' para crear la base de datos"
                )
                return

            print(f"🔍 Cargando base de datos vectorial desde: {vector_db_path}")

            # Inicializar embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.settings.rag.embedding_model
            )

            # Cargar la base de datos vectorial usando los parámetros correctos
            # folder_path: ruta a la carpeta que contiene index.faiss e index.pkl
            # embeddings: modelo de embeddings utilizado al crear el índice
            # index_name: nombre del archivo de índice (por defecto "index")
            # allow_dangerous_deserialization: permite cargar objetos pickle (necesario para FAISS)
            self.vector_store = FAISS.load_local(
                folder_path=str(vector_db_path),
                embeddings=self.embeddings,
                index_name="index",
                allow_dangerous_deserialization=True,
            )

            print("✅ Base de datos vectorial RAG cargada exitosamente")

        except Exception as e:
            print(f"❌ Error inicializando RAG: {e}")
            self.vector_store = None
            self.embeddings = None

    def search(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Realiza una búsqueda semántica en la base de datos vectorial.

        Args:
            query: Consulta de búsqueda
            k: Número de resultados a retornar (por defecto usa configuración)

        Returns:
            Lista de diccionarios con información de documentos relevantes
        """
        if not self.vector_store:
            return [
                {
                    "error": "❌ Sistema RAG no disponible. Base de datos vectorial no cargada."
                }
            ]

        try:
            k = k or self.settings.rag.top_k_results

            # Realizar búsqueda por similitud
            docs = self.vector_store.similarity_search(query, k=k)

            if not docs:
                return [
                    {
                        "error": "🔍 No se encontraron documentos relevantes para la consulta."
                    }
                ]

            # Formatear resultados como diccionarios para mejor manejo
            results = []
            for i, doc in enumerate(docs, 1):
                content = doc.page_content.strip()
                metadata = doc.metadata

                result_dict = {
                    "content": content,
                    "metadata": metadata,
                    "document_number": i,
                }
                results.append(result_dict)

            return results

        except Exception as e:
            return [{"error": f"❌ Error en búsqueda RAG: {e}"}]


# Instancia global del retriever
_rag_retriever = RAGRetriever()


@tool
def search_food_security_documents(query: str, max_results: int = 5) -> str:
    """
    Busca información relevante en documentos sobre seguridad alimentaria usando RAG.

    Esta herramienta permite al agente acceder a información especializada sobre
    seguridad alimentaria, nutrición y políticas alimentarias desde documentos
    técnicos y oficiales cargados en la base de datos vectorial.

    Args:
        query: Consulta de búsqueda. Debe ser descriptiva y específica sobre el tema de interés.
               Ejemplos: "políticas de seguridad alimentaria", "malnutrición infantil",
                        "programas alimentarios", "indicadores nutricionales"
        max_results: Número máximo de documentos relevantes a retornar (1-10)

    Returns:
        Documentos relevantes encontrados en la base de conocimientos, o mensaje de error.

    Ejemplo de uso:
        search_food_security_documents("programas de alimentación escolar en Colombia")
        search_food_security_documents("causas de la inseguridad alimentaria")
    """
    try:
        # Validar parámetros
        if not query or not query.strip():
            return "❌ Error: La consulta no puede estar vacía"

        max_results = max(1, min(max_results, 10))  # Limitar entre 1 y 10

        # Realizar búsqueda
        results = _rag_retriever.search(query.strip(), k=max_results)

        if not results:
            return "🔍 No se encontraron documentos relevantes para la consulta."

        # Verificar si hay errores
        if len(results) == 1 and "error" in results[0]:
            return results[0]["error"]

        # Obtener session_id actual
        from .sql_tools import get_current_session_id

        session_id = get_current_session_id()

        # Registrar las fuentes utilizadas si hay session_id
        if session_id:
            _rag_source_tracker.add_source(session_id, query, results)

        # Formatear respuesta
        response = f"🔍 **Búsqueda RAG:** {query}\n"
        response += f"📚 **Documentos encontrados:** {len(results)}\n\n"

        for result in results:
            doc_num = result.get("document_number", "?")
            content = result.get("content", "")
            metadata = result.get("metadata", {})

            response += f"\n=== Documento {doc_num} ===\n"
            response += f"**Contenido:** {content}\n"

            if metadata:
                response += f"**Metadatos:** {metadata}\n"

        # Agregar nota sobre el uso de la información
        response += "\n💡 **Nota:** Esta información proviene de documentos especializados sobre seguridad alimentaria. "
        response += (
            "Úsala para complementar el análisis de los datos de la base de datos."
        )

        if session_id:
            response += "\n🔖 **Las fuentes utilizadas se han registrado automáticamente para incluir en las referencias.**"

        return response

    except Exception as e:
        return f"❌ Error en búsqueda de documentos: {e}"


@tool
def create_rag_sources_section() -> str:
    """
    Crea una sección de referencias RAG con todos los documentos especializados utilizados.

    Esta herramienta debe usarse AL FINAL del análisis para incluir automáticamente
    todas las fuentes RAG que se consultaron durante la sesión.

    Returns:
        Sección formateada de referencias RAG en Markdown, o cadena vacía si no hay fuentes.

    Ejemplo de uso:
        # Usar al final del análisis después de search_food_security_documents
        create_rag_sources_section()
    """
    try:
        # Obtener session_id actual
        from .sql_tools import get_current_session_id

        session_id = get_current_session_id()

        if not session_id:
            return ""

        # Obtener las fuentes RAG formateadas
        rag_sources = _rag_source_tracker.format_rag_sources(session_id)

        return rag_sources

    except Exception as e:
        return f"❌ Error creando sección de referencias RAG: {e}"


@tool
def clear_rag_sources() -> str:
    """
    Limpia las fuentes RAG registradas para la sesión actual.

    Útil para reiniciar el rastreo de fuentes en una nueva consulta.

    Returns:
        Mensaje de confirmación.
    """
    try:
        # Obtener session_id actual
        from .sql_tools import get_current_session_id

        session_id = get_current_session_id()

        if session_id:
            _rag_source_tracker.clear_sources(session_id)
            return "✅ Fuentes RAG limpiadas para la sesión actual"
        else:
            return "⚠️ No hay sesión activa para limpiar"

    except Exception as e:
        return f"❌ Error limpiando fuentes RAG: {e}"


@tool
def get_rag_system_status() -> str:
    """
    Obtiene el estado actual del sistema RAG.

    Returns:
        Información sobre el estado del sistema RAG, configuración y estadísticas.
    """
    try:
        settings = get_settings()
        status = "📊 **Estado del Sistema RAG**\n\n"

        # Estado general
        if settings.rag.enable_rag:
            status += "✅ **Estado:** Habilitado\n"
        else:
            status += "❌ **Estado:** Deshabilitado\n"

        # Configuración
        status += "🔧 **Configuración:**\n"
        status += f"- Modelo de embeddings: {settings.rag.embedding_model}\n"
        status += f"- Resultados por búsqueda: {settings.rag.top_k_results}\n"
        status += f"- Umbral de similitud: {settings.rag.similarity_threshold}\n"
        status += f"- Ruta base de datos: {settings.rag.vector_db_path}\n\n"

        # Estado de la base de datos
        if _rag_retriever.vector_store:
            status += "✅ **Base de datos vectorial:** Cargada correctamente\n"
            # Intentar obtener estadísticas si están disponibles
            try:
                # FAISS no expone directamente el número de vectores, pero podemos intentar una búsqueda
                _rag_retriever.vector_store.similarity_search("test", k=1)
                status += "🔍 **Capacidad de búsqueda:** Operativa\n"
            except Exception:
                status += "⚠️ **Capacidad de búsqueda:** Limitada\n"
        else:
            status += "❌ **Base de datos vectorial:** No disponible\n"
            status += "💡 **Solución:** Ejecuta 'python data/rag/rag_estractor.py' para crear la base de datos\n"

        return status

    except Exception as e:
        return f"❌ Error obteniendo estado RAG: {e}"
