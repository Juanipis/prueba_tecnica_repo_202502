"""
Herramientas SmolAgents para el análisis de datos de inseguridad alimentaria.

Este módulo contiene las herramientas que el agente puede usar para:
- Consultar la base de datos SQLite
- Realizar análisis estadísticos
- Generar insights sobre los datos
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from smolagents import tool


# Ruta a la base de datos - se importará dinámicamente
from .settings import get_settings

def get_db_path() -> str:
    """Obtiene la ruta de la base de datos desde la configuración."""
    return str(get_settings().database.db_path)


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