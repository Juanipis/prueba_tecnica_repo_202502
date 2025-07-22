#!/usr/bin/env python3
"""
Ejemplos de consultas para la base de datos normalizada de inseguridad alimentaria.

Este módulo contiene consultas SQL de ejemplo que demuestran cómo
usar la base de datos normalizada para obtener insights.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional


def connect_to_database(db_path: str = "sqlite_databases/inseguridad_alimentaria_latest.db") -> sqlite3.Connection:
    """
    Conecta a la base de datos SQLite.
    
    Args:
        db_path: Ruta a la base de datos
        
    Returns:
        Conexión a la base de datos
        
    Raises:
        FileNotFoundError: Si la base de datos no existe
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
    
    return sqlite3.connect(db_path)


def query_nacional_por_año(db_path: str = "sqlite_databases/inseguridad_alimentaria_latest.db") -> pd.DataFrame:
    """
    Consulta datos nacionales por año e indicador.
    """
    query = """
    SELECT 
        i.nombre_indicador,
        dm.año,
        dm.valor,
        i.tipo_dato,
        i.tipo_de_medida
    FROM datos_medicion dm
    JOIN geografia g ON dm.id_geografia = g.id_geografia
    JOIN indicadores i ON dm.id_indicador = i.id_indicador
    WHERE g.nivel = 'Nacional'
    ORDER BY i.nombre_indicador, dm.año
    """
    
    conn = connect_to_database(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df


def query_departamentos_por_indicador(indicador: str, 
                                    año: Optional[int] = None,
                                    db_path: str = "sqlite_databases/inseguridad_alimentaria_latest.db") -> pd.DataFrame:
    """
    Consulta datos departamentales para un indicador específico.
    
    Args:
        indicador: Nombre del indicador a consultar
        año: Año específico (opcional)
        db_path: Ruta a la base de datos
    """
    where_clause = "WHERE g.nivel = 'Departamental' AND i.nombre_indicador = ?"
    params = [indicador]
    
    if año:
        where_clause += " AND dm.año = ?"
        params.append(año)
    
    query = f"""
    SELECT 
        g.nombre as departamento,
        dm.año,
        dm.valor,
        i.tipo_dato
    FROM datos_medicion dm
    JOIN geografia g ON dm.id_geografia = g.id_geografia
    JOIN indicadores i ON dm.id_indicador = i.id_indicador
    {where_clause}
    ORDER BY dm.año DESC, dm.valor DESC
    """
    
    conn = connect_to_database(db_path)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df


def query_municipios_top_por_departamento(departamento: str,
                                        indicador: str,
                                        año: int,
                                        limit: int = 10,
                                        db_path: str = "sqlite_databases/inseguridad_alimentaria_latest.db") -> pd.DataFrame:
    """
    Consulta los municipios con mayor valor para un indicador en un departamento específico.
    
    Args:
        departamento: Nombre del departamento
        indicador: Nombre del indicador
        año: Año específico
        limit: Número máximo de resultados
        db_path: Ruta a la base de datos
    """
    query = """
    SELECT 
        gm.nombre as municipio,
        gd.nombre as departamento,
        dm.valor,
        i.tipo_dato
    FROM datos_medicion dm
    JOIN geografia gm ON dm.id_geografia = gm.id_geografia
    JOIN geografia gd ON gm.id_padre = gd.id_geografia
    JOIN indicadores i ON dm.id_indicador = i.id_indicador
    WHERE gm.nivel = 'Municipal'
        AND gd.nombre = ?
        AND i.nombre_indicador = ?
        AND dm.año = ?
    ORDER BY dm.valor DESC
    LIMIT ?
    """
    
    conn = connect_to_database(db_path)
    df = pd.read_sql_query(query, conn, params=[departamento, indicador, año, limit])
    conn.close()
    
    return df


def query_comparacion_regional(indicador: str,
                             año: int,
                             db_path: str = "sqlite_databases/inseguridad_alimentaria_latest.db") -> pd.DataFrame:
    """
    Compara valores regionales para un indicador en un año específico.
    
    Args:
        indicador: Nombre del indicador
        año: Año específico
        db_path: Ruta a la base de datos
    """
    query = """
    SELECT 
        g.nombre as region,
        dm.valor,
        i.tipo_dato,
        -- Comparar con promedio nacional
        (SELECT dm_nacional.valor 
         FROM datos_medicion dm_nacional
         JOIN geografia g_nacional ON dm_nacional.id_geografia = g_nacional.id_geografia
         WHERE g_nacional.nivel = 'Nacional' 
           AND dm_nacional.id_indicador = dm.id_indicador
           AND dm_nacional.año = dm.año) as valor_nacional
    FROM datos_medicion dm
    JOIN geografia g ON dm.id_geografia = g.id_geografia
    JOIN indicadores i ON dm.id_indicador = i.id_indicador
    WHERE g.nivel = 'Regional'
        AND i.nombre_indicador = ?
        AND dm.año = ?
    ORDER BY dm.valor DESC
    """
    
    conn = connect_to_database(db_path)
    df = pd.read_sql_query(query, conn, params=[indicador, año])
    conn.close()
    
    # Calcular diferencia con nacional
    if not df.empty:
        df['diferencia_con_nacional'] = df['valor'] - df['valor_nacional']
    
    return df


def query_evolucion_temporal(entidad_geografica: str,
                           indicador: str,
                           db_path: str = "sqlite_databases/inseguridad_alimentaria_latest.db") -> pd.DataFrame:
    """
    Consulta la evolución temporal de un indicador para una entidad geográfica.
    
    Args:
        entidad_geografica: Nombre de la entidad (país, región, departamento, municipio)
        indicador: Nombre del indicador
        db_path: Ruta a la base de datos
    """
    query = """
    SELECT 
        g.nombre as entidad,
        g.nivel,
        dm.año,
        dm.valor,
        i.tipo_dato
    FROM datos_medicion dm
    JOIN geografia g ON dm.id_geografia = g.id_geografia
    JOIN indicadores i ON dm.id_indicador = i.id_indicador
    WHERE g.nombre = ?
        AND i.nombre_indicador = ?
    ORDER BY dm.año
    """
    
    conn = connect_to_database(db_path)
    df = pd.read_sql_query(query, conn, params=[entidad_geografica, indicador])
    conn.close()
    
    return df


def query_resumen_estadistico(db_path: str = "sqlite_databases/inseguridad_alimentaria_latest.db") -> pd.DataFrame:
    """
    Genera un resumen estadístico de la base de datos.
    """
    query = """
    SELECT 
        'Total entidades geográficas' as metrica,
        COUNT(*) as valor
    FROM geografia
    
    UNION ALL
    
    SELECT 
        'Entidades por nivel: ' || nivel as metrica,
        COUNT(*) as valor
    FROM geografia
    GROUP BY nivel
    
    UNION ALL
    
    SELECT 
        'Total indicadores' as metrica,
        COUNT(*) as valor
    FROM indicadores
    
    UNION ALL
    
    SELECT 
        'Total mediciones' as metrica,
        COUNT(*) as valor
    FROM datos_medicion
    
    UNION ALL
    
    SELECT 
        'Años disponibles' as metrica,
        COUNT(DISTINCT año) as valor
    FROM datos_medicion
    
    UNION ALL
    
    SELECT 
        'Rango años: ' || MIN(año) || ' - ' || MAX(año) as metrica,
        NULL as valor
    FROM datos_medicion
    """
    
    conn = connect_to_database(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df


def run_example_queries(db_path: str = "sqlite_databases/inseguridad_alimentaria_latest.db"):
    """
    Ejecuta todas las consultas de ejemplo y muestra los resultados.
    
    Args:
        db_path: Ruta a la base de datos
    """
    print("EJECUTANDO CONSULTAS DE EJEMPLO")
    print("=" * 60)
    
    try:
        # 1. Resumen estadístico
        print("\n1. RESUMEN ESTADISTICO DE LA BASE DE DATOS")
        print("-" * 50)
        df_resumen = query_resumen_estadistico(db_path)
        for _, row in df_resumen.iterrows():
            if pd.isna(row['valor']):
                print(f"  {row['metrica']}")
            else:
                print(f"  {row['metrica']}: {row['valor']}")
        
        # 2. Datos nacionales
        print("\n2. DATOS NACIONALES POR AÑO")
        print("-" * 50)
        df_nacional = query_nacional_por_año(db_path)
        if not df_nacional.empty:
            for _, row in df_nacional.iterrows():
                print(f"  {row['año']} | {row['nombre_indicador']}: {row['valor']:.4f} {row['tipo_dato']}")
        
        # 3. Departamentos con mayor inseguridad alimentaria grave (2022)
        print("\n3. DEPARTAMENTOS - INSEGURIDAD ALIMENTARIA GRAVE (2022)")
        print("-" * 50)
        df_depts = query_departamentos_por_indicador("Inseguridad Alimentaria Grave", 2022, db_path)
        if not df_depts.empty:
            for i, row in df_depts.head(5).iterrows():
                print(f"  {i+1}. {row['departamento']}: {row['valor']:.4f} {row['tipo_dato']}")
        
        # 4. Comparación regional
        print("\n4. COMPARACION REGIONAL - PREVALENCIA HOGARES (2015)")
        print("-" * 50)
        df_regional = query_comparacion_regional("Prevalencia de hogares en inseguridad alimentaria", 2015, db_path)
        if not df_regional.empty:
            for _, row in df_regional.iterrows():
                diferencia = row['diferencia_con_nacional']
                signo = "+" if diferencia > 0 else ""
                print(f"  {row['region']}: {row['valor']:.3f} ({signo}{diferencia:.3f} vs nacional)")
        
        # 5. Top municipios en Antioquia
        print("\n5. TOP MUNICIPIOS EN ANTIOQUIA - INSEGURIDAD MODERADO O GRAVE (2022)")
        print("-" * 50)
        df_municipios = query_municipios_top_por_departamento(
            "Antioquia", "Inseguridad Alimentaria Moderado o Grave", 2022, 5, db_path
        )
        if not df_municipios.empty:
            for i, row in df_municipios.iterrows():
                print(f"  {i+1}. {row['municipio']}: {row['valor']:.4f} {row['tipo_dato']}")
        
        # 6. Evolución temporal Colombia
        print("\n6. EVOLUCION TEMPORAL - COLOMBIA")
        print("-" * 50)
        df_evolucion = query_evolucion_temporal("Colombia", "Inseguridad Alimentaria Grave", db_path)
        if not df_evolucion.empty:
            for _, row in df_evolucion.iterrows():
                print(f"  {row['año']}: {row['valor']:.4f} {row['tipo_dato']}")
        
        print("\n+ Consultas de ejemplo completadas exitosamente")
        
    except Exception as e:
        print(f"X Error ejecutando consultas: {e}")


def main():
    """Función principal para ejecutar las consultas de ejemplo."""
    print("CONSULTAS DE EJEMPLO - BASE DE DATOS INSEGURIDAD ALIMENTARIA")
    
    db_path = "sqlite_databases/inseguridad_alimentaria_latest.db"
    
    if not Path(db_path).exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        print("🔧 Ejecute primero el proceso ETL:")
        print("   poetry run python -m etl_inseguridad.main")
        return
    
    run_example_queries(db_path)


if __name__ == "__main__":
    main() 