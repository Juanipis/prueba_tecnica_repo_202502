#!/usr/bin/env python3
"""
Módulo de extracción para el proceso ETL de inseguridad alimentaria.

Este módulo se encarga de leer los archivos Excel originales y 
retornar DataFrames de pandas para su posterior procesamiento.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Tuple


def extract_excel_files(data_path: str = "raw") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Extrae datos de los archivos Excel de inseguridad alimentaria.
    
    Args:
        data_path: Ruta a la carpeta que contiene los archivos Excel
        
    Returns:
        Tupla con DataFrames (regional, departamental, municipal)
        
    Raises:
        FileNotFoundError: Si algún archivo Excel no existe
        Exception: Si hay error leyendo los archivos
    """
    data_dir = Path(data_path)
    
    excel_files = {
        'regional': data_dir / "Regional.xlsx",
        'departamental': data_dir / "Departamental.xlsx", 
        'municipal': data_dir / "Municipal.xlsx"
    }
    
    # Verificar que todos los archivos existen
    for level, file_path in excel_files.items():
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo {level} no encontrado: {file_path}")
    
    try:
        # Leer archivos Excel
        print("Extrayendo datos de archivos Excel...")
        
        df_regional = pd.read_excel(excel_files['regional'])
        print(f"  + Regional: {df_regional.shape[0]} registros")
        
        df_departamental = pd.read_excel(excel_files['departamental'])
        print(f"  + Departamental: {df_departamental.shape[0]} registros")
        
        df_municipal = pd.read_excel(excel_files['municipal'])
        print(f"  + Municipal: {df_municipal.shape[0]} registros")
        
        return df_regional, df_departamental, df_municipal
        
    except Exception as e:
        raise Exception(f"Error extrayendo datos: {e}")


def validate_dataframes(df_regional: pd.DataFrame, 
                       df_departamental: pd.DataFrame, 
                       df_municipal: pd.DataFrame) -> bool:
    """
    Valida que los DataFrames tengan la estructura esperada.
    
    Args:
        df_regional: DataFrame regional
        df_departamental: DataFrame departamental  
        df_municipal: DataFrame municipal
        
    Returns:
        True si la validación es exitosa
        
    Raises:
        ValueError: Si alguna validación falla
    """
    # Validar columnas esperadas
    expected_cols = {
        'regional': ['region', 'dato_region', 'dato_nacional', 'tipo_dato', 'año', 'indicador'],
        'departamental': ['departamento', 'año', 'indicador', 'dato_departamento', 'dato_nacional', 'tipo_dato', 'tipo_de_medida'],
        'municipal': ['municipio', 'departamento', 'año', 'indicador', 'dato_municipio', 'dato_departamento', 'dato_nacional', 'tipo_dato', 'tipo_de_medida']
    }
    
    dataframes = {
        'regional': df_regional,
        'departamental': df_departamental,
        'municipal': df_municipal
    }
    
    for level, df in dataframes.items():
        expected = expected_cols[level]
        actual = list(df.columns)
        
        if actual != expected:
            raise ValueError(f"Columnas incorrectas en {level}. Esperadas: {expected}, Actual: {actual}")
    
    # Validar que no hay DataFrames vacíos
    for level, df in dataframes.items():
        if df.empty:
            raise ValueError(f"DataFrame {level} está vacío")
    
    print("Validacion de estructura completada exitosamente")
    return True


def main():
    """Función principal para el módulo de extracción."""
    try:
        # Extraer datos
        df_regional, df_departamental, df_municipal = extract_excel_files()
        
        # Validar estructura
        validate_dataframes(df_regional, df_departamental, df_municipal)
        
        print("\n=== Resumen de Extracción ===")
        print(f"Total de registros extraídos: {df_regional.shape[0] + df_departamental.shape[0] + df_municipal.shape[0]}")
        print("Extraccion completada exitosamente")
        
    except Exception as e:
        print(f"Error en extracción: {e}")
        return False
    
    return True


if __name__ == "__main__":
    main() 