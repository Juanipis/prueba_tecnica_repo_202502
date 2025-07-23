import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS  # O Chroma

# --- Configuración ---
PDF_INPUT_DIR = "./pdfs/"  # Carpeta donde están tus PDFs
VECTOR_DB_PERSIST_DIR = "./vector_db_faiss/"  # Carpeta donde se guardará la base de datos vectorial (para FAISS)
# Si usas ChromaDB, puedes usar: VECTOR_DB_PERSIST_DIR = "./vector_db_chroma/"

# --- Funciones ---


def create_and_persist_vector_db(pdf_input_dir: str, persist_dir: str):
    """
    Carga PDFs, los divide en fragmentos, crea embeddings y persiste la base de datos vectorial.
    """
    if not os.path.exists(pdf_input_dir):
        print(f"Error: La carpeta de entrada de PDFs '{pdf_input_dir}' no existe.")
        return

    print(f"Cargando documentos PDF desde: {pdf_input_dir}")
    loader = DirectoryLoader(pdf_input_dir, glob="**/*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()

    if not documents:
        print("No se encontraron documentos PDF en la carpeta especificada.")
        return

    print(f"Se cargaron {len(documents)} documentos.")

    print("Dividiendo documentos en fragmentos...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Se generaron {len(chunks)} fragmentos.")

    print("Creando embeddings y construyendo la base de datos vectorial (FAISS)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vector_store = FAISS.from_documents(chunks, embeddings)

    # Guardar la base de datos vectorial
    os.makedirs(persist_dir, exist_ok=True)
    vector_store.save_local(persist_dir)
    print(f"Base de datos vectorial guardada exitosamente en: {persist_dir}")


def load_vector_db(persist_dir: str):
    """
    Carga una base de datos vectorial persistida.
    """
    if not os.path.exists(persist_dir):
        print(
            f"Error: La carpeta de la base de datos vectorial '{persist_dir}' no existe."
        )
        return None

    print(f"Cargando base de datos vectorial desde: {persist_dir}")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vector_store = FAISS.load_local(
        persist_dir, embeddings, allow_dangerous_deserialization=True
    )
    print("Base de datos vectorial cargada exitosamente.")
    return vector_store


# --- Ejecución principal ---
if __name__ == "__main__":
    print("=== Creador de Base de Datos Vectorial para RAG ===")
    print("Iniciando proceso de creación de la base de datos vectorial...")

    # Crear la base de datos vectorial a partir de los PDFs
    create_and_persist_vector_db(PDF_INPUT_DIR, VECTOR_DB_PERSIST_DIR)

    print("\n=== Verificando la base de datos creada ===")
    # Cargar y verificar que la base de datos se creó correctamente
    vector_store = load_vector_db(VECTOR_DB_PERSIST_DIR)

    if vector_store:
        print("✅ Base de datos vectorial creada y verificada exitosamente.")
        print(f"📁 Ubicación: {VECTOR_DB_PERSIST_DIR}")
        print("🔍 La base de datos está lista para ser utilizada en consultas RAG.")
    else:
        print("❌ Error al crear o verificar la base de datos vectorial.")

    print("\nProceso completado.")
