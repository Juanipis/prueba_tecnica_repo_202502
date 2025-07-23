"""
Herramientas RAG (Retrieval-Augmented Generation) para SmolAgents.

Este módulo proporciona herramientas para realizar búsquedas semánticas
en la base de datos vectorial de documentos sobre seguridad alimentaria.
"""

from pathlib import Path
from typing import Optional, List
from smolagents import tool
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from .settings import get_settings


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

    def search(self, query: str, k: Optional[int] = None) -> List[str]:
        """
        Realiza una búsqueda semántica en la base de datos vectorial.

        Args:
            query: Consulta de búsqueda
            k: Número de resultados a retornar (por defecto usa configuración)

        Returns:
            Lista de documentos relevantes
        """
        if not self.vector_store:
            return ["❌ Sistema RAG no disponible. Base de datos vectorial no cargada."]

        try:
            k = k or self.settings.rag.top_k_results

            # Realizar búsqueda por similitud
            docs = self.vector_store.similarity_search(query, k=k)

            if not docs:
                return ["🔍 No se encontraron documentos relevantes para la consulta."]

            # Formatear resultados
            results = []
            for i, doc in enumerate(docs, 1):
                content = doc.page_content.strip()
                metadata = doc.metadata

                result = f"\n=== Documento {i} ===\n"
                result += f"Contenido: {content}\n"

                if metadata:
                    result += f"Metadatos: {metadata}\n"

                results.append(result)

            return results

        except Exception as e:
            return [f"❌ Error en búsqueda RAG: {e}"]


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

        # Formatear respuesta
        response = f"🔍 **Búsqueda RAG:** {query}\n"
        response += f"📚 **Documentos encontrados:** {len(results)}\n\n"

        for result in results:
            response += result + "\n"

        # Agregar nota sobre el uso de la información
        response += "\n💡 **Nota:** Esta información proviene de documentos especializados sobre seguridad alimentaria. "
        response += (
            "Úsala para complementar el análisis de los datos de la base de datos."
        )

        return response

    except Exception as e:
        return f"❌ Error en búsqueda de documentos: {e}"


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
