"""
Herramientas SmolAgents para el análisis de datos de inseguridad alimentaria.

Este módulo contiene las herramientas que el agente puede usar para:
- Consultar la base de datos SQLite
- Realizar análisis estadísticos
- Generar insights sobre los datos
- Crear visualizaciones con matplotlib (token-eficiente)
- Formatear citas de fuentes web correctamente
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from smolagents import tool
import base64
from io import BytesIO
import uuid
import re
from datetime import datetime

# Ruta a la base de datos - se importará dinámicamente
from .settings import get_settings

# Storage temporal para imágenes (token-eficiente)
_image_storage = {}

def get_db_path() -> str:
    """Obtiene la ruta de la base de datos desde la configuración."""
    return str(get_settings().database.db_path)

def _store_image(image_base64: str, title: str, chart_type: str) -> str:
    """
    Almacena una imagen base64 temporalmente y retorna un ID.
    
    Args:
        image_base64: String base64 de la imagen
        title: Título de la gráfica
        chart_type: Tipo de gráfica
        
    Returns:
        ID único para referenciar la imagen
    """
    image_id = str(uuid.uuid4())[:8]
    _image_storage[image_id] = {
        'data': image_base64,
        'title': title,
        'type': chart_type
    }
    return image_id

def get_stored_images() -> Dict[str, Dict[str, str]]:
    """Obtiene todas las imágenes almacenadas temporalmente."""
    return _image_storage.copy()

def clear_stored_images():
    """Limpia el almacenamiento temporal de imágenes."""
    global _image_storage
    _image_storage.clear()


@tool
def format_web_citation(source_info: str, citation_style: str = "apa") -> str:
    """
    Ayuda a formatear citas de fuentes web de manera consistente y profesional.
    
    Args:
        source_info: Información de la fuente en formato libre (ej: "título, autor, fecha, URL")
        citation_style: Estilo de citación ("apa", "simple")
        
    Returns:
        Cita formateada según el estilo especificado
        
    Examples:
        format_web_citation("Políticas de seguridad alimentaria, MinSalud Colombia, 2024, https://minsalud.gov.co/politicas")
        -> "MinSalud Colombia. (2024). *Políticas de seguridad alimentaria*. https://minsalud.gov.co/politicas"
    """
    try:
        if citation_style.lower() == "apa":
            # Intentar extraer componentes de la información
            parts = [part.strip() for part in source_info.split(',')]
            
            # Plantilla básica para APA
            if len(parts) >= 3:
                title = parts[0] if parts[0] else "Título no disponible"
                author = parts[1] if len(parts) > 1 and parts[1] else "Autor no disponible"
                date = parts[2] if len(parts) > 2 and parts[2] else "s.f."
                url = parts[3] if len(parts) > 3 and parts[3] else ""
                
                # Formatear fecha si es un año
                if date.isdigit() and len(date) == 4:
                    date = f"({date})"
                elif date == "s.f.":
                    date = "(s.f.)"
                else:
                    date = f"({date})"
                
                # Formatear cita APA
                citation = f"{author}. {date}. *{title}*."
                if url:
                    citation += f" {url}"
                
                return citation
            else:
                return f"Información insuficiente para formatear cita APA: {source_info}"
        
        elif citation_style.lower() == "simple":
            # Formato simple: solo fuente y URL
            parts = source_info.split(',')
            if len(parts) >= 2:
                source_name = parts[0].strip()
                url = parts[-1].strip() if 'http' in parts[-1] else ""
                return f"Fuente: {source_name}. {url}" if url else f"Fuente: {source_name}"
            else:
                return f"Fuente: {source_info}"
        
        else:
            return f"Estilo de citación '{citation_style}' no soportado. Use 'apa' o 'simple'."
            
    except Exception as e:
        return f"Error formateando cita: {str(e)}. Información original: {source_info}"


@tool
def create_sources_section(sources_list: str) -> str:
    """
    Crea una sección de fuentes consultadas bien formateada.
    
    Args:
        sources_list: Lista de fuentes separadas por punto y coma (;)
                     Formato: "fuente1_info; fuente2_info; ..."
        
    Returns:
        Sección de fuentes formateada en Markdown
        
    Example:
        create_sources_section("Políticas alimentarias, MinSalud, 2024, url1; Estadísticas FAO, FAO Colombia, 2023, url2")
    """
    try:
        sources = [source.strip() for source in sources_list.split(';') if source.strip()]
        
        if not sources:
            return "No se proporcionaron fuentes para formatear."
        
        formatted_section = "\n## 📚 Fuentes Consultadas\n\n"
        
        for i, source in enumerate(sources, 1):
            formatted_citation = format_web_citation(source, "apa")
            formatted_section += f"{i}. {formatted_citation}\n"
        
        formatted_section += "\n---\n*Fuentes consultadas para complementar el análisis de datos locales*\n"
        
        return formatted_section
        
    except Exception as e:
        return f"Error creando sección de fuentes: {str(e)}"


@tool
def sql_query(query: str) -> str:
    """
    Ejecuta una consulta SQL en la base de datos de inseguridad alimentaria de Colombia.
    
    La base de datos contiene tres tablas principales:
    
    Tabla 'geografia':
    - id_geografia: INTEGER (clave primaria)
    - nivel: TEXT (Nacional, Regional, Departamental, Municipal)
    - nombre: TEXT (nombre de la entidad geográfica)
    - id_padre: INTEGER (referencia jerárquica, puede ser NULL)
    - codigo_dane: TEXT (código DANE, puede ser NULL)
    
    Tabla 'indicadores':
    - id_indicador: INTEGER (clave primaria)
    - nombre_indicador: TEXT (nombre del indicador)
    - tipo_dato: TEXT (tipo de dato, ej: "Porcentaje")
    - tipo_de_medida: TEXT (metodología, ej: "Prevalencia")
    
    Tabla 'datos_medicion':
    - id_medicion: INTEGER (clave primaria)
    - id_geografia: INTEGER (referencia a geografia)
    - id_indicador: INTEGER (referencia a indicadores)
    - año: INTEGER (año de la medición)
    - valor: REAL (valor numérico del indicador)
    
    Relaciones:
    - datos_medicion.id_geografia → geografia.id_geografia
    - datos_medicion.id_indicador → indicadores.id_indicador
    - geografia.id_padre → geografia.id_geografia (jerarquía)
    
    Args:
        query: Consulta SQL a ejecutar. Debe ser SQL válido.
        
    Returns:
        Resultados de la consulta como string formatado, o mensaje de error.
    """
    try:
        # Obtener ruta de la base de datos desde configuración
        db_path = get_db_path()
        
        # Verificar que el archivo de base de datos existe
        db_file = Path(db_path)
        if not db_file.exists():
            return f"Error: Base de datos no encontrada en {db_path}"
        
        # Conectar y ejecutar consulta
        with sqlite3.connect(db_path) as conn:
            # Habilitar nombres de columnas en los resultados
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Ejecutar consulta
            cursor.execute(query)
            results = cursor.fetchall()
            
            if not results:
                return "No se encontraron resultados para la consulta."
            
            # Formatear resultados
            if len(results) == 1:
                row = results[0]
                formatted = "Resultado:\n"
                for key in row.keys():
                    formatted += f"  {key}: {row[key]}\n"
                return formatted
            else:
                # Múltiples resultados
                formatted = f"Encontrados {len(results)} resultados:\n\n"
                for i, row in enumerate(results):
                    formatted += f"Resultado {i+1}:\n"
                    for key in row.keys():
                        formatted += f"  {key}: {row[key]}\n"
                    formatted += "\n"
                return formatted
                
    except sqlite3.Error as e:
        return f"Error de SQL: {str(e)}"
    except Exception as e:
        return f"Error general: {str(e)}"


@tool
def get_database_schema() -> str:
    """
    Obtiene información detallada sobre el esquema de la base de datos.
    
    Returns:
        Descripción completa de las tablas, columnas y relaciones.
    """
    try:
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            schema_info = "ESQUEMA DE BASE DE DATOS - INSEGURIDAD ALIMENTARIA COLOMBIA\n"
            schema_info += "=" * 65 + "\n\n"
            
            # Obtener lista de tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table_name in tables:
                table_name = table_name[0]
                schema_info += f"TABLA: {table_name}\n"
                schema_info += "-" * 30 + "\n"
                
                # Obtener información de columnas
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                for col in columns:
                    col_id, name, data_type, not_null, default, is_pk = col
                    pk_marker = " (PK)" if is_pk else ""
                    null_marker = " NOT NULL" if not_null else ""
                    default_marker = f" DEFAULT {default}" if default else ""
                    
                    schema_info += f"  {name}: {data_type}{pk_marker}{null_marker}{default_marker}\n"
                
                # Obtener conteo de registros
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                schema_info += f"  Total registros: {count}\n\n"
            
            # Información adicional sobre indicadores
            cursor.execute("SELECT nombre_indicador FROM indicadores")
            indicadores = cursor.fetchall()
            schema_info += "INDICADORES DISPONIBLES:\n"
            schema_info += "-" * 25 + "\n"
            for ind in indicadores:
                schema_info += f"  - {ind[0]}\n"
            
            return schema_info
            
    except Exception as e:
        return f"Error obteniendo esquema: {str(e)}"


@tool
def analyze_data_pandas(query: str) -> str:
    """
    Ejecuta una consulta SQL y retorna los datos como DataFrame de pandas para análisis.
    
    Esta herramienta permite realizar análisis estadísticos más complejos
    usando pandas y numpy sobre los resultados de consultas SQL.
    
    Args:
        query: Consulta SQL que retornará datos para analizar
        
    Returns:
        Información estadística y descriptiva de los datos obtenidos.
    """
    try:
        # Ejecutar consulta y cargar en DataFrame
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return "No se encontraron datos para analizar."
        
        analysis = f"ANÁLISIS DE DATOS - {len(df)} registros encontrados\n"
        analysis += "=" * 50 + "\n\n"
        
        # Información básica del DataFrame
        analysis += f"Forma de los datos: {df.shape[0]} filas, {df.shape[1]} columnas\n"
        analysis += f"Columnas: {list(df.columns)}\n\n"
        
        # Estadísticas descriptivas para columnas numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            analysis += "ESTADÍSTICAS DESCRIPTIVAS (columnas numéricas):\n"
            analysis += "-" * 45 + "\n"
            desc_stats = df[numeric_cols].describe()
            analysis += desc_stats.to_string() + "\n\n"
        
        # Información sobre columnas categóricas
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            analysis += "INFORMACIÓN CATEGÓRICA:\n"
            analysis += "-" * 25 + "\n"
            for col in categorical_cols:
                unique_count = df[col].nunique()
                analysis += f"{col}: {unique_count} valores únicos\n"
                if unique_count <= 10:  # Mostrar valores si son pocos
                    values = df[col].unique()
                    analysis += f"  Valores: {list(values)}\n"
            analysis += "\n"
        
        # Valores faltantes
        missing = df.isnull().sum()
        if missing.any():
            analysis += "VALORES FALTANTES:\n"
            analysis += "-" * 20 + "\n"
            for col, count in missing.items():
                if count > 0:
                    analysis += f"{col}: {count} ({count/len(df)*100:.1f}%)\n"
            analysis += "\n"
        
        return analysis
        
    except Exception as e:
        return f"Error en análisis pandas: {str(e)}"


@tool
def create_formatted_table(query: str, format_type: str = "markdown") -> str:
    """
    Ejecuta una consulta SQL y retorna los resultados formateados como tabla.
    
    Args:
        query: Consulta SQL a ejecutar
        format_type: Tipo de formato ("markdown", "html", "csv")
        
    Returns:
        Tabla formateada según el tipo especificado
    """
    try:
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return "No se encontraron resultados para la consulta."
        
        if format_type.lower() == "markdown":
            try:
                return df.to_markdown(index=False, tablefmt="grid")
            except ImportError:
                # Fallback si tabulate no está disponible
                return df.to_string(index=False)
        elif format_type.lower() == "html":
            return df.to_html(index=False, classes="table table-striped")
        elif format_type.lower() == "csv":
            return df.to_csv(index=False)
        else:
            return df.to_string(index=False)
            
    except Exception as e:
        return f"Error creando tabla formateada: {str(e)}"


@tool
def get_available_years() -> str:
    """
    Obtiene los años disponibles en la base de datos.
    
    Returns:
        Lista de años con datos disponibles
    """
    query = """
    SELECT DISTINCT año 
    FROM datos_medicion 
    ORDER BY año ASC
    """
    
    try:
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            years = [row[0] for row in cursor.fetchall()]
            
        if years:
            return f"Años disponibles: {', '.join(map(str, years))}\nTotal: {len(years)} años de datos"
        else:
            return "No se encontraron años con datos disponibles."
            
    except Exception as e:
        return f"Error obteniendo años disponibles: {str(e)}"


@tool
def get_available_indicators() -> str:
    """
    Obtiene la lista completa de indicadores disponibles.
    
    Returns:
        Lista detallada de indicadores con sus tipos
    """
    query = """
    SELECT 
        nombre_indicador,
        tipo_dato,
        tipo_de_medida,
        COUNT(DISTINCT dm.año) as años_disponibles
    FROM indicadores i
    LEFT JOIN datos_medicion dm ON i.id_indicador = dm.id_indicador
    GROUP BY i.id_indicador, nombre_indicador, tipo_dato, tipo_de_medida
    ORDER BY nombre_indicador
    """
    
    try:
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            
        if results:
            formatted = "INDICADORES DISPONIBLES:\n"
            formatted += "=" * 50 + "\n\n"
            
            for nombre, tipo_dato, tipo_medida, años in results:
                formatted += f"📊 {nombre}\n"
                formatted += f"   Tipo: {tipo_dato}\n"
                formatted += f"   Medida: {tipo_medida}\n"
                formatted += f"   Años con datos: {años}\n\n"
                
            return formatted
        else:
            return "No se encontraron indicadores disponibles."
            
    except Exception as e:
        return f"Error obteniendo indicadores: {str(e)}"


@tool
def get_entities_by_level(nivel: str = "Departamental") -> str:
    """
    Obtiene las entidades disponibles para un nivel geográfico específico.
    
    Args:
        nivel: Nivel geográfico (Nacional, Regional, Departamental, Municipal)
        
    Returns:
        Lista de entidades para el nivel especificado
    """
    query = f"""
    SELECT 
        nombre,
        codigo_dane,
        COUNT(DISTINCT dm.año) as años_con_datos
    FROM geografia g
    LEFT JOIN datos_medicion dm ON g.id_geografia = dm.id_geografia
    WHERE g.nivel = '{nivel}'
    GROUP BY g.id_geografia, nombre, codigo_dane
    ORDER BY nombre
    """
    
    try:
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            
        if results:
            formatted = f"ENTIDADES - NIVEL {nivel.upper()}:\n"
            formatted += "=" * 40 + "\n\n"
            
            for nombre, codigo, años in results:
                codigo_text = f" (DANE: {codigo})" if codigo else ""
                años_text = f" - {años} años con datos" if años > 0 else " - Sin datos"
                formatted += f"📍 {nombre}{codigo_text}{años_text}\n"
                
            formatted += f"\nTotal entidades: {len(results)}"
            return formatted
        else:
            return f"No se encontraron entidades para el nivel {nivel}."
            
    except Exception as e:
        return f"Error obteniendo entidades: {str(e)}"


@tool
def quick_summary(año: int = 2022) -> str:
    """
    Genera un resumen rápido de todos los indicadores para un año específico.
    
    Args:
        año: Año para el resumen (por defecto 2022)
        
    Returns:
        Resumen estadístico de todos los indicadores
    """
    try:
        query = f"""
        SELECT 
            i.nombre_indicador,
            g.nivel,
            COUNT(*) as num_entidades,
            ROUND(AVG(dm.valor) * 100, 2) as promedio_porcentaje,
            ROUND(MIN(dm.valor) * 100, 2) as minimo_porcentaje,
            ROUND(MAX(dm.valor) * 100, 2) as maximo_porcentaje
        FROM datos_medicion dm
        JOIN geografia g ON dm.id_geografia = g.id_geografia
        JOIN indicadores i ON dm.id_indicador = i.id_indicador
        WHERE dm.año = {año}
        GROUP BY i.nombre_indicador, g.nivel
        ORDER BY i.nombre_indicador, g.nivel
        """
        
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return f"No se encontraron datos para el año {año}."
        
        summary = f"RESUMEN RÁPIDO - AÑO {año}\n"
        summary += "=" * 40 + "\n\n"
        
        for indicador in df['nombre_indicador'].unique():
            summary += f"📊 {indicador}\n"
            indicador_data = df[df['nombre_indicador'] == indicador]
            
            for _, row in indicador_data.iterrows():
                summary += f"   {row['nivel']}: {row['num_entidades']} entidades, "
                summary += f"promedio {row['promedio_porcentaje']}%, "
                summary += f"rango {row['minimo_porcentaje']}-{row['maximo_porcentaje']}%\n"
            summary += "\n"
        
        return summary
        
    except Exception as e:
        return f"Error generando resumen: {str(e)}"


@tool
def get_top_entities(indicador: str, año: int, nivel: str = "Departamental", limit: int = 10) -> str:
    """
    Obtiene las entidades con mayor valor para un indicador específico.
    
    Args:
        indicador: Nombre del indicador (ej: "Inseguridad Alimentaria Grave")
        año: Año de consulta
        nivel: Nivel geográfico (Nacional, Regional, Departamental, Municipal)
        limit: Número máximo de resultados a retornar
        
    Returns:
        Lista ordenada de entidades con los valores más altos.
    """
    query = f"""
    SELECT 
        g.nombre as entidad,
        g.nivel,
        i.nombre_indicador,
        dm.año,
        dm.valor,
        ROUND(dm.valor * 100, 2) as porcentaje
    FROM datos_medicion dm
    JOIN geografia g ON dm.id_geografia = g.id_geografia
    JOIN indicadores i ON dm.id_indicador = i.id_indicador
    WHERE i.nombre_indicador LIKE '%{indicador}%'
        AND dm.año = {año}
        AND g.nivel = '{nivel}'
    ORDER BY dm.valor DESC
    LIMIT {limit}
    """
    
    return sql_query(query)


@tool
def compare_years(indicador: str, entidad: str = "Colombia") -> str:
    """
    Compara la evolución de un indicador a lo largo de los años para una entidad.
    
    Args:
        indicador: Nombre del indicador a analizar
        entidad: Nombre de la entidad geográfica (por defecto "Colombia")
        
    Returns:
        Evolución temporal del indicador para la entidad especificada.
    """
    query = f"""
    SELECT 
        g.nombre as entidad,
        i.nombre_indicador,
        dm.año,
        dm.valor,
        ROUND(dm.valor * 100, 2) as porcentaje
    FROM datos_medicion dm
    JOIN geografia g ON dm.id_geografia = g.id_geografia
    JOIN indicadores i ON dm.id_indicador = i.id_indicador
    WHERE i.nombre_indicador LIKE '%{indicador}%'
        AND g.nombre LIKE '%{entidad}%'
    ORDER BY dm.año ASC
    """
    
    return sql_query(query)


@tool
def calculate_statistics(indicador: str, año: int, nivel: str = "Departamental") -> str:
    """
    Calcula estadísticas descriptivas para un indicador específico.
    
    Args:
        indicador: Nombre del indicador
        año: Año de análisis
        nivel: Nivel geográfico
        
    Returns:
        Estadísticas descriptivas (media, mediana, desviación estándar, etc.)
    """
    query = f"""
    SELECT dm.valor
    FROM datos_medicion dm
    JOIN geografia g ON dm.id_geografia = g.id_geografia
    JOIN indicadores i ON dm.id_indicador = i.id_indicador
    WHERE i.nombre_indicador LIKE '%{indicador}%'
        AND dm.año = {año}
        AND g.nivel = '{nivel}'
    """
    
    try:
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return "No se encontraron datos para el análisis estadístico."
        
        values = df['valor']
        
        stats = f"ESTADÍSTICAS DESCRIPTIVAS\n"
        stats += f"Indicador: {indicador}\n"
        stats += f"Año: {año}, Nivel: {nivel}\n"
        stats += "=" * 40 + "\n"
        stats += f"Número de observaciones: {len(values)}\n"
        stats += f"Media: {values.mean():.6f} ({values.mean()*100:.2f}%)\n"
        stats += f"Mediana: {values.median():.6f} ({values.median()*100:.2f}%)\n"
        stats += f"Desviación estándar: {values.std():.6f}\n"
        stats += f"Mínimo: {values.min():.6f} ({values.min()*100:.2f}%)\n"
        stats += f"Máximo: {values.max():.6f} ({values.max()*100:.2f}%)\n"
        stats += f"Percentil 25: {values.quantile(0.25):.6f}\n"
        stats += f"Percentil 75: {values.quantile(0.75):.6f}\n"
        
        return stats
        
    except Exception as e:
        return f"Error calculando estadísticas: {str(e)}" 


@tool
def create_chart_visualization(query: str, chart_type: str = "bar", title: str = "", 
                              x_column: str = "", y_column: str = "", 
                              figsize_width: int = 10, figsize_height: int = 6) -> str:
    """
    Crea una visualización usando matplotlib a partir de una consulta SQL.
    
    IMPORTANTE: Esta función es token-eficiente. No retorna la imagen base64 directamente
    para evitar consumir tokens innecesariamente. La imagen se almacena temporalmente.
    
    Args:
        query: Consulta SQL que retornará los datos para visualizar
        chart_type: Tipo de gráfica ("bar", "line", "pie", "scatter", "histogram")
        title: Título de la gráfica
        x_column: Nombre de la columna para el eje X (si aplica)
        y_column: Nombre de la columna para el eje Y (si aplica) 
        figsize_width: Ancho de la figura en pulgadas
        figsize_height: Alto de la figura en pulgadas
        
    Returns:
        Mensaje corto confirmando la creación (NO la imagen base64)
    """
    try:
        # Importar matplotlib sin pyplot para evitar memory leaks
        from matplotlib.figure import Figure
        import matplotlib.pyplot as plt
        plt.style.use('default')  # Estilo limpio
        
        # Ejecutar consulta y cargar datos
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return "Error: No se encontraron datos para visualizar."
            
        # Crear figura usando Figure() directamente (recomendado para web)
        fig = Figure(figsize=(figsize_width, figsize_height))
        ax = fig.subplots()
        
        # Detectar columnas automáticamente si no se especifican
        if not x_column and len(df.columns) >= 1:
            x_column = df.columns[0]
        if not y_column and len(df.columns) >= 2:
            y_column = df.columns[1]
        elif not y_column and len(df.columns) == 1:
            y_column = df.columns[0]
            
        # Crear diferentes tipos de gráficas
        if chart_type.lower() == "bar":
            if x_column and y_column and x_column in df.columns and y_column in df.columns:
                ax.bar(df[x_column], df[y_column])
                ax.set_xlabel(x_column)
                ax.set_ylabel(y_column)
            else:
                return f"Error: Columnas {x_column} o {y_column} no encontradas en los datos."
                
        elif chart_type.lower() == "line":
            if x_column and y_column and x_column in df.columns and y_column in df.columns:
                ax.plot(df[x_column], df[y_column], marker='o')
                ax.set_xlabel(x_column)
                ax.set_ylabel(y_column)
            else:
                return f"Error: Columnas {x_column} o {y_column} no encontradas en los datos."
                
        elif chart_type.lower() == "pie":
            if y_column and y_column in df.columns:
                # Para pie chart, usar la primera columna como labels si existe
                labels = df[x_column] if x_column and x_column in df.columns else df.index
                ax.pie(df[y_column], labels=labels, autopct='%1.1f%%')
            else:
                return f"Error: Columna {y_column} no encontrada en los datos."
                
        elif chart_type.lower() == "scatter":
            if x_column and y_column and x_column in df.columns and y_column in df.columns:
                ax.scatter(df[x_column], df[y_column])
                ax.set_xlabel(x_column)
                ax.set_ylabel(y_column)
            else:
                return f"Error: Columnas {x_column} o {y_column} no encontradas en los datos."
                
        elif chart_type.lower() == "histogram":
            if y_column and y_column in df.columns:
                ax.hist(df[y_column], bins=20, edgecolor='black', alpha=0.7)
                ax.set_xlabel(y_column)
                ax.set_ylabel('Frecuencia')
            else:
                return f"Error: Columna {y_column} no encontrada en los datos."
        else:
            return f"Error: Tipo de gráfica '{chart_type}' no soportado. Use: bar, line, pie, scatter, histogram"
        
        # Configurar título y layout
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Rotar labels del eje X si son muchos o muy largos
        if chart_type.lower() in ["bar", "line"] and x_column in df.columns:
            if len(df[x_column]) > 10 or any(len(str(x)) > 8 for x in df[x_column]):
                ax.tick_params(axis='x', rotation=45)
        
        # Mejorar el layout
        fig.tight_layout()
        
        # Guardar en buffer de memoria como PNG
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        
        # Convertir a base64
        img_base64 = base64.b64encode(buf.getvalue()).decode('ascii')
        buf.close()
        
        # Limpiar memoria
        fig.clear()
        
        # CLAVE: Almacenar imagen temporalmente, NO retornarla al agente
        image_id = _store_image(f"data:image/png;base64,{img_base64}", title or f"Gráfica {chart_type}", chart_type)
        
        # Retornar solo mensaje corto (token-eficiente)
        return f"✅ Gráfica {chart_type} creada exitosamente: '{title}' (ID: {image_id})"
        
    except ImportError as e:
        return f"Error: matplotlib no disponible: {str(e)}"
    except Exception as e:
        return f"Error creando visualización: {str(e)}"


@tool
def create_multiple_charts(query: str, chart_configs: str) -> str:
    """
    Crea múltiples visualizaciones a partir de una consulta SQL.
    
    IMPORTANTE: Token-eficiente - no retorna imágenes base64 directamente.
    
    Args:
        query: Consulta SQL que retornará los datos
        chart_configs: String JSON con configuraciones de múltiples gráficas
                      Ejemplo: '[{"type":"bar","title":"Gráfica 1","x":"col1","y":"col2"},{"type":"pie","title":"Gráfica 2","y":"col3"}]'
        
    Returns:
        Resumen de gráficas creadas (NO las imágenes base64)
    """
    try:
        import json
        
        # Parsear configuraciones
        configs = json.loads(chart_configs)
        
        # Ejecutar consulta una sola vez
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return "Error: No se encontraron datos para visualizar."
        
        results = []
        
        for i, config in enumerate(configs):
            chart_type = config.get('type', 'bar')
            title = config.get('title', f'Gráfica {i+1}')
            x_col = config.get('x', '')
            y_col = config.get('y', '')
            
            # Crear gráfica individual usando la query original
            result = create_chart_visualization(
                query=query,
                chart_type=chart_type,
                title=title,
                x_column=x_col,
                y_column=y_col
            )
            
            results.append(f"- {result}")
        
        return f"✅ {len(configs)} gráficas creadas:\n" + "\n".join(results)
        
    except json.JSONDecodeError:
        return "Error: chart_configs debe ser un JSON válido"
    except Exception as e:
        return f"Error creando múltiples visualizaciones: {str(e)}"


@tool
def analyze_and_visualize(query: str, analysis_type: str = "complete") -> str:
    """
    Realiza análisis completo con estadísticas y visualizaciones automáticas.
    
    IMPORTANTE: Token-eficiente - almacena imágenes temporalmente.
    
    Args:
        query: Consulta SQL para analizar
        analysis_type: Tipo de análisis ("complete", "basic", "charts_only")
        
    Returns:
        Análisis de texto + confirmación de gráficas creadas
    """
    try:
        # Ejecutar consulta
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return "No se encontraron datos para analizar."
        
        result = "# ANÁLISIS COMPLETO CON VISUALIZACIONES\n\n"
        
        if analysis_type in ["complete", "basic"]:
            # Análisis estadístico
            result += "## 📊 Estadísticas Descriptivas\n\n"
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                stats = df[numeric_cols].describe()
                result += "```\n" + stats.to_string() + "\n```\n\n"
            
            result += f"- **Total registros**: {len(df)}\n"
            result += f"- **Columnas**: {list(df.columns)}\n\n"
        
        if analysis_type in ["complete", "charts_only"]:
            # Generar visualizaciones automáticas
            result += "## 📈 Visualizaciones Generadas\n\n"
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            categorical_cols = df.select_dtypes(include=['object']).columns
            
            created_charts = []
            
            # Gráfica 1: Bar chart si hay categorías y números
            if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                chart_result = create_chart_visualization(
                    query=query,
                    chart_type="bar",
                    title=f"Distribución por {categorical_cols[0]}",
                    x_column=categorical_cols[0],
                    y_column=numeric_cols[0]
                )
                created_charts.append(f"- {chart_result}")
            
            # Gráfica 2: Histograma de la primera columna numérica
            if len(numeric_cols) > 0:
                chart_result = create_chart_visualization(
                    query=query,
                    chart_type="histogram",
                    title=f"Distribución de {numeric_cols[0]}",
                    y_column=numeric_cols[0]
                )
                created_charts.append(f"- {chart_result}")
            
            # Gráfica 3: Pie chart si hay pocas categorías
            if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                unique_categories = df[categorical_cols[0]].nunique()
                if unique_categories <= 10:  # Solo si no hay demasiadas categorías
                    chart_result = create_chart_visualization(
                        query=query,
                        chart_type="pie",
                        title=f"Proporción por {categorical_cols[0]}",
                        x_column=categorical_cols[0],
                        y_column=numeric_cols[0]
                    )
                    created_charts.append(f"- {chart_result}")
            
            if created_charts:
                result += "\n".join(created_charts) + "\n\n"
        
        result += "---\n*Análisis generado automáticamente por SmolAgent con matplotlib*"
        return result
        
    except Exception as e:
        return f"Error en análisis y visualización: {str(e)}" 


@tool
def extract_analysis_keywords(analysis_text: str, max_keywords: int = 10) -> str:
    """
    Extrae palabras clave relevantes del análisis realizado.
    
    Args:
        analysis_text: Texto del análisis realizado
        max_keywords: Número máximo de palabras clave a extraer
        
    Returns:
        Lista de palabras clave separadas por comas
    """
    try:
        import re
        from collections import Counter
        
        # Limpiar texto
        text = analysis_text.lower()
        
        # Palabras clave específicas del dominio
        domain_keywords = {
            'inseguridad alimentaria', 'seguridad alimentaria', 'prevalencia',
            'inseguridad grave', 'inseguridad moderada', 'hogares vulnerables',
            'departamentos', 'municipios', 'regiones', 'colombia',
            'antioquia', 'cundinamarca', 'atlántico', 'valle del cauca',
            'cauca', 'nariño', 'chocó', 'córdoba', 'bolívar', 'magdalena',
            'cesar', 'sucre', 'la guajira', 'santander', 'norte de santander',
            'boyacá', 'tolima', 'huila', 'meta', 'casanare', 'arauca',
            'vichada', 'guainía', 'vaupés', 'amazonas', 'guaviare',
            'putumayo', 'caquetá', 'bogotá', 'medellín', 'cali', 'barranquilla',
            'cartagena', 'bucaramanga', 'pereira', 'manizales', 'ibagué',
            'neiva', 'villavicencio', 'montería', 'valledupar', 'sincelejo',
            'riohacha', 'santa marta', 'quibdó', 'popayán', 'pasto',
            'florencia', 'yopal', 'arauca ciudad', 'puerto carreño',
            'inírida', 'mitú', 'leticia', 'san josé del guaviare', 'mocoa'
        }
        
        # Términos de análisis estadístico
        analysis_terms = {
            'estadísticas descriptivas', 'promedio', 'media', 'mediana',
            'máximo', 'mínimo', 'desviación estándar', 'percentil',
            'distribución', 'correlación', 'tendencia', 'evolución',
            'comparación', 'ranking', 'porcentaje', 'proporción',
            'variabilidad', 'outliers', 'patrones', 'datos históricos'
        }
        
        # Buscar palabras clave del dominio
        found_keywords = []
        for keyword in domain_keywords:
            if keyword in text:
                found_keywords.append(keyword.title())
        
        # Buscar términos de análisis
        for term in analysis_terms:
            if term in text:
                found_keywords.append(f"📊 {term.title()}")
        
        # Buscar años mencionados
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        for year in set(years):
            found_keywords.append(f"📅 Año {year}")
        
        # Buscar porcentajes para identificar datos cuantitativos
        percentages = re.findall(r'\b\d+\.?\d*\s*%', text)
        if percentages:
            found_keywords.append("📈 Datos Porcentuales")
        
        # Identificar si hay gráficas mencionadas
        if any(word in text for word in ['gráfica', 'gráfico', 'visualización', 'chart', 'plot']):
            found_keywords.append("📊 Visualizaciones")
        
        # Identificar si hay fuentes web
        if any(word in text for word in ['según', 'fuente', 'http', 'www', 'referencias']):
            found_keywords.append("🔗 Fuentes Externas")
        
        # Limitar cantidad y remover duplicados
        unique_keywords = list(dict.fromkeys(found_keywords))[:max_keywords]
        
        return ", ".join(unique_keywords) if unique_keywords else "Análisis, Inseguridad Alimentaria, Colombia"
        
    except Exception as e:
        return f"Error extrayendo palabras clave: {str(e)}"


@tool 
def create_formatted_markdown_table(data_query: str, table_title: str = "") -> str:
    """
    Crea una tabla Markdown correctamente formateada a partir de una consulta SQL.
    
    IMPORTANTE: Esta función genera tablas con el formato Markdown correcto para 
    que se rendericen apropiadamente en el frontend.
    
    Args:
        data_query: Consulta SQL que retornará los datos para la tabla
        table_title: Título opcional para la tabla
        
    Returns:
        Tabla en formato Markdown correctamente estructurada
        
    Formato correcto de tabla Markdown:
    | Columna 1 | Columna 2 | Columna 3 |
    |-----------|-----------|-----------|
    | Dato 1    | Dato 2    | Dato 3    |
    | Dato 4    | Dato 5    | Dato 6    |
    """
    try:
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(data_query, conn)
        
        if df.empty:
            return "No se encontraron datos para crear la tabla."
        
        # Crear encabezado de tabla
        table_md = ""
        if table_title:
            table_md += f"\n### {table_title}\n\n"
        
        # Crear encabezados
        headers = "| " + " | ".join(df.columns) + " |"
        table_md += headers + "\n"
        
        # Crear línea separadora
        separator = "|" + "|".join(["-" * (len(col) + 2) for col in df.columns]) + "|"
        table_md += separator + "\n"
        
        # Agregar filas de datos
        for _, row in df.iterrows():
            # Formatear valores (especialmente números)
            formatted_values = []
            for val in row:
                if pd.isna(val):
                    formatted_values.append("N/A")
                elif isinstance(val, float):
                    if val < 1.0:
                        formatted_values.append(f"{val*100:.1f}%")  # Convertir a porcentaje
                    else:
                        formatted_values.append(f"{val:.2f}")
                else:
                    formatted_values.append(str(val))
            
            row_md = "| " + " | ".join(formatted_values) + " |"
            table_md += row_md + "\n"
        
        table_md += "\n"
        return table_md
        
    except Exception as e:
        return f"Error creando tabla Markdown: {str(e)}" 