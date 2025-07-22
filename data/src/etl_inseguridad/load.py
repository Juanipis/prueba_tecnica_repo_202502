#!/usr/bin/env python3
"""
Módulo de carga para el proceso ETL de inseguridad alimentaria.

Este módulo se encarga de crear la base de datos SQLite y cargar
los datos transformados en las tablas normalizadas.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Tuple
from datetime import datetime
from .transform import transform_data
from .extract import extract_excel_files, validate_dataframes


def create_database_schema(db_path: str) -> sqlite3.Connection:
    """
    Crea la base de datos SQLite y las tablas según el esquema propuesto.
    
    Args:
        db_path: Ruta donde crear la base de datos
        
    Returns:
        Conexión a la base de datos
    """
    # Crear directorio si no existe
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Conectar a la base de datos (se crea si no existe)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Creando base de datos: {db_path}")
    
    # Crear tabla geografia
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS geografia (
            id_geografia INTEGER PRIMARY KEY,
            nivel TEXT NOT NULL,
            nombre TEXT NOT NULL,
            id_padre INTEGER,
            codigo_dane TEXT,
            FOREIGN KEY (id_padre) REFERENCES geografia (id_geografia)
        )
    """)
    
    # Crear tabla indicadores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indicadores (
            id_indicador INTEGER PRIMARY KEY,
            nombre_indicador TEXT NOT NULL,
            tipo_dato TEXT NOT NULL,
            tipo_de_medida TEXT NOT NULL
        )
    """)
    
    # Crear tabla datos_medicion
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datos_medicion (
            id_medicion INTEGER PRIMARY KEY,
            id_geografia INTEGER NOT NULL,
            id_indicador INTEGER NOT NULL,
            año INTEGER NOT NULL,
            valor REAL NOT NULL,
            FOREIGN KEY (id_geografia) REFERENCES geografia (id_geografia),
            FOREIGN KEY (id_indicador) REFERENCES indicadores (id_indicador),
            UNIQUE(id_geografia, id_indicador, año)
        )
    """)
    
    # Crear índices para mejorar rendimiento
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_geografia_nivel ON geografia (nivel)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_geografia_nombre ON geografia (nombre)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_medicion_geografia ON datos_medicion (id_geografia)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_medicion_indicador ON datos_medicion (id_indicador)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_medicion_año ON datos_medicion (año)")
    
    conn.commit()
    print("+ Esquema de base de datos creado exitosamente")
    
    return conn


def create_latest_database_link(db_path: str) -> None:
    """
    Crea un enlace/copia a la base de datos más reciente como 'latest'.
    
    Args:
        db_path: Ruta de la base de datos con timestamp
    """
    db_file = Path(db_path)
    latest_path = db_file.parent / "inseguridad_alimentaria_latest.db"
    
    # En Windows usamos copia en lugar de symlink
    try:
        if latest_path.exists():
            latest_path.unlink()
        
        # Copiar archivo en lugar de symlink para compatibilidad Windows
        import shutil
        shutil.copy2(db_path, latest_path)
        print(f"+ Enlace a base de datos más reciente creado: {latest_path.name}")
    except Exception as e:
        print(f"! No se pudo crear enlace a versión más reciente: {e}")


def load_data_to_database(df_geografia: pd.DataFrame,
                         df_indicadores: pd.DataFrame,
                         df_medicion: pd.DataFrame,
                         timestamp: str) -> Tuple[bool, str]:
    """
    Carga los datos transformados en la base de datos SQLite.
    
    Args:
        df_geografia: DataFrame con datos de geografía
        df_indicadores: DataFrame con datos de indicadores
        df_medicion: DataFrame con datos de medición
        timestamp: Timestamp para el nombre de la base de datos
        
    Returns:
        Tupla (success, db_path) - True si la carga fue exitosa y ruta de la DB
    """
    try:
        # Generar ruta de base de datos con timestamp
        db_dir = Path("sqlite_databases")
        db_dir.mkdir(exist_ok=True)
        db_path = str(db_dir / f"inseguridad_alimentaria_{timestamp}.db")
        
        # Crear base de datos y esquema
        conn = create_database_schema(db_path)
        
        print("Cargando datos en la base de datos...")
        
        # Limpiar tablas existentes (en orden para respetar claves foráneas)
        conn.execute("DELETE FROM datos_medicion")
        conn.execute("DELETE FROM indicadores")
        conn.execute("DELETE FROM geografia")
        
        # Cargar datos en orden (padres antes que hijos por claves foráneas)
        print("  + Cargando tabla geografia...")
        df_geografia.to_sql('geografia', conn, if_exists='append', index=False)
        
        print("  + Cargando tabla indicadores...")
        df_indicadores.to_sql('indicadores', conn, if_exists='append', index=False)
        
        print("  + Cargando tabla datos_medicion...")
        df_medicion.to_sql('datos_medicion', conn, if_exists='append', index=False)
        
        # Confirmar transacción
        conn.commit()
        
        # Verificar carga
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM geografia")
        count_geografia = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM indicadores")
        count_indicadores = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM datos_medicion")
        count_medicion = cursor.fetchone()[0]
        
        print(f"\n=== Verificación de Carga ===")
        print(f"Geografía: {count_geografia} registros")
        print(f"Indicadores: {count_indicadores} registros")
        print(f"Datos medición: {count_medicion} registros")
        
        conn.close()
        print("+ Datos cargados exitosamente en la base de datos")
        
        # Crear enlace simbólico a la versión más reciente DESPUÉS de cargar datos
        create_latest_database_link(db_path)
        
        return True, db_path
        
    except Exception as e:
        print(f"Error cargando datos: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False, ""


def run_data_quality_checks(db_path: str) -> bool:
    """
    Ejecuta verificaciones de calidad de datos en la base de datos.
    
    Args:
        db_path: Ruta de la base de datos
        
    Returns:
        True si todas las verificaciones pasan
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n=== Verificaciones de Calidad de Datos ===")
        
        # Verificar integridad referencial
        cursor.execute("""
            SELECT COUNT(*) FROM datos_medicion dm
            LEFT JOIN geografia g ON dm.id_geografia = g.id_geografia
            WHERE g.id_geografia IS NULL
        """)
        orphan_geografia = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM datos_medicion dm
            LEFT JOIN indicadores i ON dm.id_indicador = i.id_indicador
            WHERE i.id_indicador IS NULL
        """)
        orphan_indicadores = cursor.fetchone()[0]
        
        if orphan_geografia > 0:
            print(f"  X {orphan_geografia} registros con geografia_id invalido")
            return False
        else:
            print("  + Integridad referencial geografia OK")
            
        if orphan_indicadores > 0:
            print(f"  X {orphan_indicadores} registros con indicador_id invalido")
            return False
        else:
            print("  + Integridad referencial indicadores OK")
        
        # Verificar valores nulos en campos críticos
        cursor.execute("SELECT COUNT(*) FROM datos_medicion WHERE valor IS NULL")
        null_values = cursor.fetchone()[0]
        
        if null_values > 0:
            print(f"  ! {null_values} registros con valores nulos")
        else:
            print("  + No hay valores nulos en mediciones")
        
        # Verificar duplicados
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT id_geografia, id_indicador, año, COUNT(*) as cnt
                FROM datos_medicion 
                GROUP BY id_geografia, id_indicador, año
                HAVING cnt > 1
            )
        """)
        duplicates = cursor.fetchone()[0]
        
        if duplicates > 0:
            print(f"  X {duplicates} registros duplicados encontrados")
            return False
        else:
            print("  + No hay registros duplicados")
        
        # Mostrar resumen por nivel geográfico
        cursor.execute("""
            SELECT g.nivel, COUNT(*) as registros
            FROM datos_medicion dm
            JOIN geografia g ON dm.id_geografia = g.id_geografia
            GROUP BY g.nivel
            ORDER BY registros DESC
        """)
        
        print("\n  Registros por nivel geografico:")
        for nivel, count in cursor.fetchall():
            print(f"    {nivel}: {count} registros")
        
        conn.close()
        print("+ Verificaciones de calidad completadas")
        
        return True
        
    except Exception as e:
        print(f"Error en verificaciones de calidad: {e}")
        return False


def main():
    """Función principal para el módulo de carga."""
    try:
        # Extraer datos
        df_regional, df_departamental, df_municipal = extract_excel_files()
        validate_dataframes(df_regional, df_departamental, df_municipal)
        
        # Transformar datos
        df_geografia, df_indicadores, df_medicion, timestamp = transform_data(
            df_regional, df_departamental, df_municipal
        )
        
        # Cargar datos
        success, db_path = load_data_to_database(df_geografia, df_indicadores, df_medicion, timestamp)
        
        if success:
            # Ejecutar verificaciones de calidad
            run_data_quality_checks(db_path)
            print("\n+ Proceso de carga completado exitosamente")
            print(f"+ Base de datos creada: {db_path}")
            return True
        else:
            print("X Error en el proceso de carga")
            return False
            
    except Exception as e:
        print(f"Error en carga: {e}")
        return False


if __name__ == "__main__":
    main() 