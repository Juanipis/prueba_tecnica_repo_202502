"""
Herramientas SmolAgents para el análisis de datos de inseguridad alimentaria.

Este módulo contiene las herramientas esenciales que el agente puede usar para:
- Consultar la base de datos SQLite con SQL flexible
- Explorar el esquema de la base de datos
- Realizar análisis estadísticos con pandas
- Crear visualizaciones con matplotlib (token-eficiente)
- Formatear tablas y citas de fuentes web correctamente
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any
from smolagents import tool
import base64
from io import BytesIO
import uuid

# Ruta a la base de datos - se importará dinámicamente
from .settings import get_settings

# Import del session manager para manejo de imágenes por sesión
from .session_manager import session_manager

# Contexto global para el session_id actual (thread-safe)
import threading
_session_context = threading.local()

def set_current_session_id(session_id: str):
    """Establece el session_id actual para las herramientas."""
    _session_context.current_session_id = session_id

def get_current_session_id() -> str:
    """Obtiene el session_id actual, por defecto "default"."""
    return getattr(_session_context, 'current_session_id', 'default')

def get_db_path() -> str:
    """Obtiene la ruta de la base de datos desde la configuración."""
    return str(get_settings().database.db_path)

def _store_image(session_id: str, image_base64: str, title: str, chart_type: str) -> str:
    """
    Almacena una imagen base64 en la sesión específica y retorna un ID.
    
    Args:
        session_id: ID de la sesión
        image_base64: String base64 de la imagen
        title: Título de la gráfica
        chart_type: Tipo de gráfica
        
    Returns:
        ID único para referenciar la imagen
    """
    return session_manager.store_image(session_id, image_base64, title, chart_type)

def get_stored_images(session_id: str) -> Dict[str, Dict[str, str]]:
    """Obtiene todas las imágenes almacenadas en una sesión específica."""
    return session_manager.get_session_images(session_id)

def clear_stored_images(session_id: str):
    """Limpia el almacenamiento temporal de imágenes de una sesión específica."""
    session_manager.clear_session_images(session_id)


@tool
def sql_query(query: str) -> str:
    """
    Ejecuta una consulta SQL en la base de datos.
    
    Esta es la herramienta principal para acceder a los datos. El agente puede crear
    cualquier consulta SQL necesaria para obtener la información requerida.
    
    Args:
        query: Consulta SQL a ejecutar. Debe ser SQL válido.
        
    Returns:
        Resultados de la consulta como string formatado, o mensaje de error.
        
    Ejemplo de uso:
        sql_query("SELECT * FROM geografia WHERE nivel = 'Departamental' LIMIT 5")
        sql_query("SELECT g.nombre, AVG(dm.valor) as promedio FROM datos_medicion dm JOIN geografia g ON dm.id_geografia = g.id_geografia WHERE dm.año = 2022 GROUP BY g.nombre ORDER BY promedio DESC LIMIT 10")
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
    
    Esta herramienta es esencial para que el agente comprenda la estructura
    de datos disponible y pueda crear consultas SQL apropiadas.
    
    COMPLETAMENTE DINÁMICO: No asume nada sobre la estructura de la base de datos.
    
    Returns:
        Descripción completa de las tablas, columnas, tipos de datos, relaciones y contenido de muestra.
    """
    try:
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            schema_info = "ESQUEMA COMPLETO DE LA BASE DE DATOS\n"
            schema_info += "=" * 45 + "\n\n"
            
            # Obtener lista de tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if not tables:
                return "⚠️ No se encontraron tablas en la base de datos."
            
            schema_info += f"🗃️ TOTAL DE TABLAS: {len(tables)}\n\n"
            
            # Información detallada de cada tabla
            for table_name in tables:
                table_name = table_name[0]
                schema_info += f"📊 TABLA: {table_name}\n"
                schema_info += "-" * 40 + "\n"
                
                # Obtener información de columnas
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                schema_info += "COLUMNAS:\n"
                primary_keys = []
                for col in columns:
                    col_id, name, data_type, not_null, default, is_pk = col
                    if is_pk:
                        primary_keys.append(name)
                    
                    pk_marker = " (CLAVE PRIMARIA)" if is_pk else ""
                    null_marker = " NOT NULL" if not_null else ""
                    default_marker = f" DEFAULT {default}" if default else ""
                    
                    schema_info += f"  • {name}: {data_type}{pk_marker}{null_marker}{default_marker}\n"
                
                # Obtener información de claves foráneas
                cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                foreign_keys = cursor.fetchall()
                
                if foreign_keys:
                    schema_info += "\nCLAVES FORÁNEAS:\n"
                    for fk in foreign_keys:
                        id_fk, seq, table_ref, from_col, to_col, on_update, on_delete, match = fk
                        schema_info += f"  • {from_col} → {table_ref}.{to_col}\n"
                
                # Obtener conteo de registros
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                schema_info += f"\nTOTAL REGISTROS: {count:,}\n"
                
                # Mostrar muestra de datos (primeras 3 filas)
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_data = cursor.fetchall()
                    
                    if sample_data:
                        schema_info += "\nMUESTRA DE DATOS (primeras 3 filas):\n"
                        col_names = [description[0] for description in cursor.description]
                        for i, row in enumerate(sample_data, 1):
                            schema_info += f"  Fila {i}:\n"
                            for col_name, value in zip(col_names, row):
                                # Truncar valores muy largos para legibilidad
                                display_value = str(value)
                                if len(display_value) > 50:
                                    display_value = display_value[:47] + "..."
                                schema_info += f"    {col_name}: {display_value}\n"
                else:
                    schema_info += "\n⚠️ Tabla vacía (sin registros)\n"
                
                schema_info += "\n" + "="*40 + "\n\n"
            
            # Detectar automáticamente patrones comunes de datos
            schema_info += "🔍 ANÁLISIS AUTOMÁTICO DE PATRONES:\n"
            schema_info += "-" * 35 + "\n"
            
            # Detectar columnas que podrían ser fechas/años
            date_patterns = []
            for table_name in [t[0] for t in tables]:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                for col in columns:
                    col_name = col[1].lower()
                    if any(keyword in col_name for keyword in ['año', 'year', 'fecha', 'date', 'time']):
                        try:
                            cursor.execute(f"SELECT DISTINCT {col[1]} FROM {table_name} ORDER BY {col[1]} LIMIT 10")
                            values = cursor.fetchall()
                            if values:
                                date_patterns.append(f"  • {table_name}.{col[1]}: {[v[0] for v in values[:5]]}...")
                        except:
                            pass
            
            if date_patterns:
                schema_info += "📅 COLUMNAS TEMPORALES DETECTADAS:\n"
                schema_info += "\n".join(date_patterns) + "\n\n"
            
            # Detectar columnas que podrían ser categóricas importantes
            categorical_patterns = []
            for table_name in [t[0] for t in tables]:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_records = cursor.fetchone()[0]
                
                if total_records > 0:
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    for col in columns:
                        if col[2].upper() in ['TEXT', 'VARCHAR']:  # Solo columnas de texto
                            try:
                                cursor.execute(f"SELECT COUNT(DISTINCT {col[1]}) as unique_count FROM {table_name}")
                                unique_count = cursor.fetchone()[0]
                                # Si hay pocas categorías distintas comparado con el total, es probablemente categórica
                                if unique_count <= min(20, total_records * 0.5):
                                    cursor.execute(f"SELECT DISTINCT {col[1]} FROM {table_name} LIMIT 5")
                                    sample_values = [v[0] for v in cursor.fetchall()]
                                    categorical_patterns.append(f"  • {table_name}.{col[1]} ({unique_count} valores): {sample_values}...")
                            except:
                                pass
            
            if categorical_patterns:
                schema_info += "🏷️ COLUMNAS CATEGÓRICAS DETECTADAS:\n"
                schema_info += "\n".join(categorical_patterns[:10]) + "\n\n"  # Limitar a 10 para no saturar
            
            # Detectar columnas numéricas importantes
            numeric_patterns = []
            for table_name in [t[0] for t in tables]:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                for col in columns:
                    if col[2].upper() in ['INTEGER', 'REAL', 'NUMERIC', 'DECIMAL', 'FLOAT']:
                        try:
                            cursor.execute(f"SELECT MIN({col[1]}), MAX({col[1]}), COUNT(*) FROM {table_name} WHERE {col[1]} IS NOT NULL")
                            min_val, max_val, count = cursor.fetchone()
                            if count > 0:
                                numeric_patterns.append(f"  • {table_name}.{col[1]}: rango [{min_val}, {max_val}] ({count} valores)")
                        except:
                            pass
            
            if numeric_patterns:
                schema_info += "📊 COLUMNAS NUMÉRICAS DETECTADAS:\n"
                schema_info += "\n".join(numeric_patterns[:10]) + "\n\n"
            
            # Resumen final con sugerencias genéricas
            schema_info += "💡 SUGERENCIAS GENERALES PARA CONSULTAS:\n"
            schema_info += "-" * 40 + "\n"
            schema_info += "• Explora los datos: SELECT * FROM [nombre_tabla] LIMIT 10\n"
            schema_info += "• Cuenta registros: SELECT COUNT(*) FROM [nombre_tabla]\n"
            schema_info += "• Valores únicos: SELECT DISTINCT [columna] FROM [nombre_tabla]\n"
            schema_info += "• Agrupaciones: SELECT [columna], COUNT(*) FROM [nombre_tabla] GROUP BY [columna]\n"
            schema_info += "• Unir tablas: usa las claves foráneas detectadas arriba para JOIN\n"
            schema_info += "• Estadísticas: SELECT AVG([columna_numerica]), MIN([columna_numerica]), MAX([columna_numerica]) FROM [nombre_tabla]\n\n"
            
            schema_info += "🎯 ESTRATEGIA RECOMENDADA:\n"
            schema_info += "1. Empieza explorando tablas individuales\n"
            schema_info += "2. Identifica las relaciones entre tablas usando las claves foráneas\n"
            schema_info += "3. Construye consultas JOIN según necesites\n"
            schema_info += "4. Usa columnas temporales y categóricas para filtros específicos\n"
            
            return schema_info
            
    except Exception as e:
        return f"Error obteniendo esquema: {str(e)}"


@tool
def analyze_data_pandas(query: str) -> str:
    """
    Ejecuta una consulta SQL y retorna análisis estadístico usando pandas.
    
    Esta herramienta permite al agente realizar análisis estadísticos detallados
    sobre cualquier conjunto de datos obtenido mediante SQL.
    
    Args:
        query: Consulta SQL que retornará datos para analizar
        
    Returns:
        Análisis estadístico completo incluyendo estadísticas descriptivas,
        información sobre valores faltantes, distribuciones, etc.
    """
    try:
        # Ejecutar consulta y cargar en DataFrame
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return "No se encontraron datos para analizar."
        
        analysis = f"📊 ANÁLISIS ESTADÍSTICO COMPLETO\n"
        analysis += f"Consulta: {query[:100]}{'...' if len(query) > 100 else ''}\n"
        analysis += "=" * 60 + "\n\n"
        
        # Información básica del DataFrame
        analysis += f"📋 INFORMACIÓN GENERAL:\n"
        analysis += f"  • Forma de los datos: {df.shape[0]:,} filas × {df.shape[1]} columnas\n"
        analysis += f"  • Columnas: {list(df.columns)}\n"
        analysis += f"  • Memoria utilizada: {df.memory_usage(deep=True).sum():,} bytes\n\n"
        
        # Tipos de datos
        analysis += f"🏷️ TIPOS DE DATOS:\n"
        for col, dtype in df.dtypes.items():
            analysis += f"  • {col}: {dtype}\n"
        analysis += "\n"
        
        # Estadísticas descriptivas para columnas numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            analysis += "📈 ESTADÍSTICAS DESCRIPTIVAS (columnas numéricas):\n"
            analysis += "-" * 50 + "\n"
            desc_stats = df[numeric_cols].describe()
            analysis += desc_stats.to_string() + "\n\n"
            
            # Información adicional sobre distribuciones
            analysis += "📊 ANÁLISIS DE DISTRIBUCIÓN:\n"
            for col in numeric_cols:
                skewness = df[col].skew()
                kurtosis = df[col].kurtosis()
                analysis += f"  • {col}:\n"
                analysis += f"    - Asimetría (skewness): {skewness:.3f}\n"
                analysis += f"    - Curtosis (kurtosis): {kurtosis:.3f}\n"
        
        # Información sobre columnas categóricas
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            analysis += "\n🏷️ ANÁLISIS CATEGÓRICO:\n"
            analysis += "-" * 25 + "\n"
            for col in categorical_cols:
                unique_count = df[col].nunique()
                analysis += f"  • {col}: {unique_count:,} valores únicos\n"
                
                # Mostrar frecuencias si son pocos valores únicos
                if unique_count <= 20:
                    value_counts = df[col].value_counts()
                    analysis += f"    Distribución:\n"
                    for value, count in value_counts.head(10).items():
                        percentage = (count / len(df)) * 100
                        analysis += f"      - {value}: {count:,} ({percentage:.1f}%)\n"
                    if len(value_counts) > 10:
                        analysis += f"      - ... y {len(value_counts) - 10} valores más\n"
            analysis += "\n"
        
        # Valores faltantes
        missing = df.isnull().sum()
        if missing.any():
            analysis += "❌ VALORES FALTANTES:\n"
            analysis += "-" * 20 + "\n"
            for col, count in missing.items():
                if count > 0:
                    percentage = (count / len(df)) * 100
                    analysis += f"  • {col}: {count:,} valores faltantes ({percentage:.1f}%)\n"
            analysis += "\n"
        else:
            analysis += "✅ No hay valores faltantes en los datos.\n\n"
        
        # Correlaciones si hay múltiples columnas numéricas
        if len(numeric_cols) > 1:
            analysis += "🔗 MATRIZ DE CORRELACIÓN:\n"
            analysis += "-" * 25 + "\n"
            corr_matrix = df[numeric_cols].corr()
            analysis += corr_matrix.to_string() + "\n\n"
        
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


@tool
def create_chart_visualization(query: str, chart_type: str = "bar", title: str = "", 
                              x_column: str = "", y_column: str = "", 
                              figsize_width: int = 10, figsize_height: int = 6) -> str:
    """
    Crea una visualización usando matplotlib a partir de una consulta SQL.
    
    IMPORTANTE: Esta función es token-eficiente. No retorna la imagen base64 directamente
    para evitar consumir tokens innecesariamente. La imagen se almacena en la sesión actual.
    
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
        
        # CLAVE: Almacenar imagen en la sesión actual, NO retornarla al agente
        current_session_id = get_current_session_id()
        image_id = _store_image(current_session_id, f"data:image/png;base64,{img_base64}", title or f"Gráfica {chart_type}", chart_type)
        
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
    
    IMPORTANTE: Token-eficiente - almacena imágenes en la sesión actual.
    
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
            
            # Extraer componentes disponibles
            title = parts[0] if len(parts) > 0 and parts[0] else "Título no disponible"
            author = parts[1] if len(parts) > 1 and parts[1] else "Autor no disponible"
            date = parts[2] if len(parts) > 2 and parts[2] else "s.f."
            url = parts[3] if len(parts) > 3 and parts[3] else ""
            
            # Si no hay comas, asumir que es solo una fuente simple
            if len(parts) == 1:
                # Solo un elemento, tratarlo como título/fuente
                if 'http' in source_info:
                    # Si contiene URL
                    url_parts = source_info.split('http', 1)
                    title = url_parts[0].strip()
                    url = 'http' + url_parts[1].strip()
                    author = "Fuente web"
                else:
                    # Solo título/autor
                    title = source_info
                    author = "Fuente no especificada"
            
            # Si el "autor" parece ser un año, intercambiar
            elif len(parts) == 2:
                if parts[1].strip().isdigit() and len(parts[1].strip()) == 4:
                    # El segundo elemento es un año
                    author = parts[0]
                    date = parts[1]
                    title = "Información no especificada"
                else:
                    # Orden normal: título, autor
                    title = parts[0]
                    author = parts[1]
            
            # Formatear fecha
            if date.isdigit() and len(date) == 4:
                date = f"({date})"
            elif date == "s.f.":
                date = "(s.f.)"
            else:
                date = f"({date})"
            
            # Formatear cita APA con lo que tengamos
            citation = f"{author}. {date}. *{title}*."
            if url:
                citation += f" {url}"
            
            return citation
        
        elif citation_style.lower() == "simple":
            # Formato simple: solo fuente y URL
            parts = source_info.split(',')
            if len(parts) >= 2:
                source_name = parts[0].strip()
                url = parts[-1].strip() if 'http' in parts[-1] else ""
                return f"Fuente: {source_name}. {url}" if url else f"Fuente: {source_name}"
            else:
                # Solo un elemento
                if 'http' in source_info:
                    url_parts = source_info.split('http', 1)
                    source_name = url_parts[0].strip() or "Fuente web"
                    url = 'http' + url_parts[1].strip()
                    return f"Fuente: {source_name}. {url}"
                else:
                    return f"Fuente: {source_info}"
        
        else:
            return f"Estilo de citación '{citation_style}' no soportado. Use 'apa' o 'simple'."
            
    except Exception as e:
        return f"Fuente: {source_info}"


@tool
def create_sources_section(sources_list: str, include_title: bool = True) -> str:
    """
    Crea una sección de fuentes consultadas bien formateada.
    
    Args:
        sources_list: Lista de fuentes separadas por punto y coma (;)
                     Formato: "fuente1_info; fuente2_info; ..."
        include_title: Si incluir el título "Fuentes Consultadas" o solo la lista
        
    Returns:
        Sección de fuentes formateada en Markdown
        
    Example:
        create_sources_section("Políticas alimentarias, MinSalud, 2024, url1; Estadísticas FAO, FAO Colombia, 2023, url2")
    """
    try:
        sources = [source.strip() for source in sources_list.split(';') if source.strip()]
        
        if not sources:
            return ""
        
        formatted_section = ""
        
        if include_title:
            formatted_section = "\n## 📚 Fuentes Consultadas\n\n"
        
        for i, source in enumerate(sources, 1):
            formatted_citation = format_web_citation(source, "apa")
            formatted_section += f"{i}. {formatted_citation}\n"
        
        if include_title:
            formatted_section += "\n---\n*Fuentes consultadas para complementar el análisis de datos locales*\n"
        
        return formatted_section
        
    except Exception as e:
        return ""
