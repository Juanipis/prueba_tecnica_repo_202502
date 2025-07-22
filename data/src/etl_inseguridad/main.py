#!/usr/bin/env python3
"""
Script principal para el proceso ETL de inseguridad alimentaria.

Este módulo orquesta todo el proceso ETL: Extract, Transform, Load
para convertir datos de Excel a una base de datos SQLite normalizada.
"""

import sys
import time
from pathlib import Path
from typing import Optional
from .extract import extract_excel_files, validate_dataframes
from .transform import transform_data
from .load import load_data_to_database, run_data_quality_checks


def print_banner():
    """Imprime el banner del proceso ETL."""
    banner = """
================================================================
                    ETL INSEGURIDAD ALIMENTARIA               
                                                              
  Proceso de normalizacion de datos de inseguridad           
  alimentaria en Colombia - Excel a SQLite                   
================================================================
    """
    print(banner)


def print_step(step_number: int, step_name: str, description: str):
    """Imprime información de cada paso del proceso."""
    print(f"\n{'='*60}")
    print(f"PASO {step_number}: {step_name}")
    print(f"{'='*60}")
    print(f"{description}")
    print()


def run_full_etl(data_path: str = "raw", 
                skip_quality_checks: bool = False) -> bool:
    """
    Ejecuta el proceso ETL completo.
    
    Args:
        data_path: Ruta a los archivos Excel de entrada
        skip_quality_checks: Si True, omite las verificaciones de calidad
        
    Returns:
        True si el proceso fue exitoso
    """
    start_time = time.time()
    
    try:
        # PASO 1: EXTRACCIÓN
        print_step(1, "EXTRACCIÓN", "Leyendo archivos Excel y validando estructura")
        
        df_regional, df_departamental, df_municipal = extract_excel_files(data_path)
        validate_dataframes(df_regional, df_departamental, df_municipal)
        
        print("Extraccion completada exitosamente")
        
        # PASO 2: TRANSFORMACIÓN Y CURADO
        print_step(2, "TRANSFORMACIÓN", "Curando, normalizando y guardando datos en curated/ y processed/")
        
        df_geografia, df_indicadores, df_medicion, timestamp = transform_data(
            df_regional, df_departamental, df_municipal
        )
        
        print("Transformacion completada exitosamente")
        
        # PASO 3: CARGA
        print_step(3, "CARGA", f"Creando base de datos SQLite con timestamp {timestamp}")
        
        success, db_path = load_data_to_database(df_geografia, df_indicadores, df_medicion, timestamp)
        
        if not success:
            print("X Error en la carga de datos")
            return False
            
        print("Carga completada exitosamente")
        
        # PASO 4: VERIFICACIONES DE CALIDAD (opcional)
        if not skip_quality_checks:
            print_step(4, "VERIFICACIONES", "Ejecutando verificaciones de calidad de datos")
            
            quality_ok = run_data_quality_checks(db_path)
            
            if quality_ok:
                print("Verificaciones de calidad completadas exitosamente")
            else:
                print("! Algunas verificaciones de calidad fallaron")
        
        # RESUMEN FINAL
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n{'='*60}")
        print("PROCESO ETL COMPLETADO EXITOSAMENTE")
        print(f"{'='*60}")
        print(f"Tiempo total: {duration:.2f} segundos")
        print(f"Base de datos creada: {db_path}")
        print(f"Tablas creadas:")
        print(f"   • geografía: {len(df_geografia)} registros")
        print(f"   • indicadores: {len(df_indicadores)} registros")
        print(f"   • datos_medicion: {len(df_medicion)} registros")
        
        return True
        
    except Exception as e:
        print(f"\nX ERROR EN PROCESO ETL: {e}")
        return False


def validate_input_files(data_path: str = "raw") -> bool:
    """
    Valida que los archivos de entrada existan.
    
    Args:
        data_path: Ruta a los archivos Excel
        
    Returns:
        True si todos los archivos existen
    """
    data_dir = Path(data_path)
    required_files = ["Regional.xlsx", "Departamental.xlsx", "Municipal.xlsx"]
    
    print("Validando archivos de entrada...")
    
    missing_files = []
    for file_name in required_files:
        file_path = data_dir / file_name
        if file_path.exists():
            print(f"  + {file_name}")
        else:
            print(f"  X {file_name} (NO ENCONTRADO)")
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\nX Archivos faltantes: {', '.join(missing_files)}")
        print(f"Verifique que los archivos esten en: {data_dir.absolute()}")
        return False
    
    print("Todos los archivos de entrada estan disponibles")
    return True


def main():
    """Función principal del script."""
    print_banner()
    
    # Verificar argumentos de línea de comandos
    data_path = "raw"
    skip_quality_checks = False
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print("Uso: python -m etl_inseguridad.main [opciones]")
            print("\nOpciones:")
            print("  -h, --help           Muestra esta ayuda")
            print("  --skip-quality       Omite las verificaciones de calidad")
            print("  --data-path PATH     Ruta personalizada a archivos Excel (default: raw)")
            print("  NOTA: Base de datos se crea automáticamente con timestamp en sqlite_databases/")
            return
        
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == "--skip-quality":
                skip_quality_checks = True
            elif arg == "--data-path" and i + 1 < len(sys.argv):
                data_path = sys.argv[i + 1]
    
    # Validar archivos de entrada
    if not validate_input_files(data_path):
        sys.exit(1)
    
    # Ejecutar proceso ETL
    success = run_full_etl(data_path, skip_quality_checks)
    
    if success:
        print("\nProceso ETL finalizado con exito!")
        print("Puede explorar la base de datos con su herramienta SQLite preferida")
        sys.exit(0)
    else:
        print("\nEl proceso ETL fallo. Revise los errores anteriores.")
        sys.exit(1)


if __name__ == "__main__":
    main() 