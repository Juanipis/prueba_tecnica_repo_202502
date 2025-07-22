#!/usr/bin/env python3
"""
Módulo de transformación para el proceso ETL de inseguridad alimentaria.

Este módulo se encarga de transformar los datos extraídos de Excel
en un formato normalizado según el esquema de base de datos propuesto.
"""

import pandas as pd
from typing import Dict, Tuple, List
from pathlib import Path
from datetime import datetime
from .extract import extract_excel_files, validate_dataframes


def create_geografia_table(df_regional: pd.DataFrame, 
                          df_departamental: pd.DataFrame, 
                          df_municipal: pd.DataFrame) -> pd.DataFrame:
    """
    Crea la tabla geografía normalizada a partir de los datos.
    
    Args:
        df_regional: DataFrame regional
        df_departamental: DataFrame departamental
        df_municipal: DataFrame municipal
        
    Returns:
        DataFrame con la tabla geografía normalizada
    """
    geografia_records = []
    id_counter = 1
    
    # Nivel Nacional - Colombia (siempre ID = 1)
    geografia_records.append({
        'id_geografia': id_counter,
        'nivel': 'Nacional',
        'nombre': 'Colombia',
        'id_padre': None,
        'codigo_dane': None
    })
    id_counter += 1
    
    # Nivel Regional
    regiones = df_regional['region'].unique()
    region_ids = {}
    
    for region in sorted(regiones):
        geografia_records.append({
            'id_geografia': id_counter,
            'nivel': 'Regional', 
            'nombre': region,
            'id_padre': 1,  # Colombia es el padre
            'codigo_dane': None
        })
        region_ids[region] = id_counter
        id_counter += 1
    
    # Nivel Departamental
    departamentos = df_departamental['departamento'].unique()
    # También obtener departamentos del archivo municipal
    departamentos_municipal = df_municipal['departamento'].unique()
    departamentos = sorted(set(list(departamentos) + list(departamentos_municipal)))
    
    departamento_ids = {}
    
    for departamento in departamentos:
        geografia_records.append({
            'id_geografia': id_counter,
            'nivel': 'Departamental',
            'nombre': departamento,
            'id_padre': 1,  # Por ahora todos dependen de Colombia, idealmente mapear a regiones
            'codigo_dane': None
        })
        departamento_ids[departamento] = id_counter
        id_counter += 1
    
    # Nivel Municipal
    municipios_data = df_municipal[['municipio', 'departamento']].drop_duplicates()
    
    for _, row in municipios_data.iterrows():
        municipio = row['municipio']
        departamento = row['departamento']
        
        geografia_records.append({
            'id_geografia': id_counter,
            'nivel': 'Municipal',
            'nombre': municipio,
            'id_padre': departamento_ids[departamento],
            'codigo_dane': None
        })
        id_counter += 1
    
    df_geografia = pd.DataFrame(geografia_records)
    print(f"+ Tabla geografia creada: {len(df_geografia)} registros")
    
    return df_geografia


def create_indicadores_table(df_regional: pd.DataFrame, 
                           df_departamental: pd.DataFrame, 
                           df_municipal: pd.DataFrame) -> pd.DataFrame:
    """
    Crea la tabla indicadores normalizada.
    
    Args:
        df_regional: DataFrame regional
        df_departamental: DataFrame departamental
        df_municipal: DataFrame municipal
        
    Returns:
        DataFrame con la tabla indicadores normalizada
    """
    indicadores_records = []
    id_counter = 1
    
    # Recopilar todos los indicadores únicos
    indicadores_data = []
    
    # Regional
    for _, row in df_regional.drop_duplicates(['indicador', 'tipo_dato']).iterrows():
        indicadores_data.append({
            'nombre_indicador': row['indicador'],
            'tipo_dato': row['tipo_dato'],
            'tipo_de_medida': 'Prevalencia'  # Asumido para regional
        })
    
    # Departamental
    for _, row in df_departamental.drop_duplicates(['indicador', 'tipo_dato', 'tipo_de_medida']).iterrows():
        indicadores_data.append({
            'nombre_indicador': row['indicador'],
            'tipo_dato': row['tipo_dato'],
            'tipo_de_medida': row['tipo_de_medida']
        })
    
    # Municipal
    for _, row in df_municipal.drop_duplicates(['indicador', 'tipo_dato', 'tipo_de_medida']).iterrows():
        indicadores_data.append({
            'nombre_indicador': row['indicador'],
            'tipo_dato': row['tipo_dato'],
            'tipo_de_medida': row['tipo_de_medida']
        })
    
    # Eliminar duplicados
    indicadores_unicos = []
    for ind in indicadores_data:
        if ind not in indicadores_unicos:
            indicadores_unicos.append(ind)
    
    # Crear registros con IDs
    for indicador_data in indicadores_unicos:
        indicadores_records.append({
            'id_indicador': id_counter,
            'nombre_indicador': indicador_data['nombre_indicador'],
            'tipo_dato': indicador_data['tipo_dato'],
            'tipo_de_medida': indicador_data['tipo_de_medida']
        })
        id_counter += 1
    
    df_indicadores = pd.DataFrame(indicadores_records)
    print(f"+ Tabla indicadores creada: {len(df_indicadores)} registros")
    
    return df_indicadores


def create_datos_medicion_table(df_regional: pd.DataFrame, 
                               df_departamental: pd.DataFrame, 
                               df_municipal: pd.DataFrame,
                               df_geografia: pd.DataFrame,
                               df_indicadores: pd.DataFrame) -> pd.DataFrame:
    """
    Crea la tabla datos_medicion normalizada.
    
    Args:
        df_regional: DataFrame regional
        df_departamental: DataFrame departamental
        df_municipal: DataFrame municipal
        df_geografia: DataFrame geografía
        df_indicadores: DataFrame indicadores
        
    Returns:
        DataFrame con la tabla datos_medicion normalizada
    """
    medicion_records = []
    id_counter = 1
    
    # Crear mapas de lookup
    geografia_map = {}
    for _, row in df_geografia.iterrows():
        key = (row['nivel'], row['nombre'])
        geografia_map[key] = row['id_geografia']
    
    indicadores_map = {}
    for _, row in df_indicadores.iterrows():
        key = (row['nombre_indicador'], row['tipo_dato'], row['tipo_de_medida'])
        indicadores_map[key] = row['id_indicador']
    
    # Procesar datos regionales (filtrar valores NULL)
    df_regional_clean = df_regional.dropna(subset=['dato_region'])
    regional_filtered = len(df_regional) - len(df_regional_clean)
    if regional_filtered > 0:
        print(f"  ! Filtrados {regional_filtered} registros regionales con valores NULL")
    
    for _, row in df_regional_clean.iterrows():
        id_geografia = geografia_map[('Regional', row['region'])]
        id_indicador = indicadores_map[(row['indicador'], row['tipo_dato'], 'Prevalencia')]
        
        medicion_records.append({
            'id_medicion': id_counter,
            'id_geografia': id_geografia,
            'id_indicador': id_indicador,
            'año': row['año'],
            'valor': row['dato_region']
        })
        id_counter += 1
    
    # Procesar datos departamentales (filtrar valores NULL)
    df_departamental_clean = df_departamental.dropna(subset=['dato_departamento'])
    departamental_filtered = len(df_departamental) - len(df_departamental_clean)
    if departamental_filtered > 0:
        print(f"  ! Filtrados {departamental_filtered} registros departamentales con valores NULL")
    
    for _, row in df_departamental_clean.iterrows():
        id_geografia = geografia_map[('Departamental', row['departamento'])]
        id_indicador = indicadores_map[(row['indicador'], row['tipo_dato'], row['tipo_de_medida'])]
        
        medicion_records.append({
            'id_medicion': id_counter,
            'id_geografia': id_geografia,
            'id_indicador': id_indicador,
            'año': row['año'],
            'valor': row['dato_departamento']
        })
        id_counter += 1
    
    # Procesar datos municipales (filtrar valores NULL)
    df_municipal_clean = df_municipal.dropna(subset=['dato_municipio'])
    municipal_filtered = len(df_municipal) - len(df_municipal_clean)
    if municipal_filtered > 0:
        print(f"  ! Filtrados {municipal_filtered} registros municipales con valores NULL")
    
    for _, row in df_municipal_clean.iterrows():
        id_geografia = geografia_map[('Municipal', row['municipio'])]
        id_indicador = indicadores_map[(row['indicador'], row['tipo_dato'], row['tipo_de_medida'])]
        
        medicion_records.append({
            'id_medicion': id_counter,
            'id_geografia': id_geografia,
            'id_indicador': id_indicador,
            'año': row['año'],
            'valor': row['dato_municipio']
        })
        id_counter += 1
    
    # Agregar datos nacionales únicos (filtrar valores NULL)
    datos_nacionales = set()
    
    # De datos regionales (filtrar NULL)
    df_regional_nacional = df_regional.dropna(subset=['dato_nacional'])
    for _, row in df_regional_nacional.iterrows():
        datos_nacionales.add((row['indicador'], 'Prevalencia', row['tipo_dato'], row['año'], row['dato_nacional']))
    
    # De datos departamentales (filtrar NULL)
    df_departamental_nacional = df_departamental.dropna(subset=['dato_nacional'])
    for _, row in df_departamental_nacional.iterrows():
        datos_nacionales.add((row['indicador'], row['tipo_de_medida'], row['tipo_dato'], row['año'], row['dato_nacional']))
    
    # De datos municipales (filtrar NULL)
    df_municipal_nacional = df_municipal.dropna(subset=['dato_nacional'])
    for _, row in df_municipal_nacional.iterrows():
        datos_nacionales.add((row['indicador'], row['tipo_de_medida'], row['tipo_dato'], row['año'], row['dato_nacional']))
    
    # Insertar datos nacionales
    id_colombia = geografia_map[('Nacional', 'Colombia')]
    
    for indicador, tipo_medida, tipo_dato, año, valor_nacional in datos_nacionales:
        id_indicador = indicadores_map[(indicador, tipo_dato, tipo_medida)]
        
        medicion_records.append({
            'id_medicion': id_counter,
            'id_geografia': id_colombia,
            'id_indicador': id_indicador,
            'año': año,
            'valor': valor_nacional
        })
        id_counter += 1
    
    df_medicion = pd.DataFrame(medicion_records)
    
    # Eliminar duplicados basados en id_geografia, id_indicador, año
    initial_count = len(df_medicion)
    df_medicion = df_medicion.drop_duplicates(subset=['id_geografia', 'id_indicador', 'año'], keep='first')
    final_count = len(df_medicion)
    
    if initial_count != final_count:
        duplicates_removed = initial_count - final_count
        print(f"  ! Eliminados {duplicates_removed} registros duplicados")
    
    print(f"+ Tabla datos_medicion creada: {len(df_medicion)} registros")
    
    return df_medicion


def save_curated_data(df_regional: pd.DataFrame, 
                     df_departamental: pd.DataFrame, 
                     df_municipal: pd.DataFrame,
                     timestamp: str) -> None:
    """
    Guarda los datos curados (limpios) en la carpeta curated.
    
    Args:
        df_regional: DataFrame regional limpio
        df_departamental: DataFrame departamental limpio
        df_municipal: DataFrame municipal limpio
        timestamp: Timestamp para el nombre de archivo
    """
    curated_dir = Path("curated")
    curated_dir.mkdir(exist_ok=True)
    
    # Guardar datos curados con timestamp
    df_regional.to_csv(curated_dir / f"regional_curated_{timestamp}.csv", index=False)
    df_departamental.to_csv(curated_dir / f"departamental_curated_{timestamp}.csv", index=False)
    df_municipal.to_csv(curated_dir / f"municipal_curated_{timestamp}.csv", index=False)
    
    print(f"+ Datos curados guardados en curated/ con timestamp {timestamp}")


def save_processed_data(df_geografia: pd.DataFrame,
                       df_indicadores: pd.DataFrame,
                       df_medicion: pd.DataFrame,
                       timestamp: str) -> None:
    """
    Guarda los datos procesados (normalizados) en la carpeta processed.
    
    Args:
        df_geografia: DataFrame geografía normalizado
        df_indicadores: DataFrame indicadores normalizado
        df_medicion: DataFrame medición normalizado
        timestamp: Timestamp para el nombre de archivo
    """
    processed_dir = Path("processed")
    processed_dir.mkdir(exist_ok=True)
    
    # Guardar datos procesados con timestamp
    df_geografia.to_csv(processed_dir / f"geografia_processed_{timestamp}.csv", index=False)
    df_indicadores.to_csv(processed_dir / f"indicadores_processed_{timestamp}.csv", index=False)
    df_medicion.to_csv(processed_dir / f"datos_medicion_processed_{timestamp}.csv", index=False)
    
    print(f"+ Datos procesados guardados en processed/ con timestamp {timestamp}")


def transform_data(df_regional: pd.DataFrame, 
                  df_departamental: pd.DataFrame, 
                  df_municipal: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    """
    Transforma los datos extraídos en tablas normalizadas.
    
    Args:
        df_regional: DataFrame regional
        df_departamental: DataFrame departamental
        df_municipal: DataFrame municipal
        
    Returns:
        Tupla con DataFrames (geografía, indicadores, datos_medicion, timestamp)
    """
    print("Iniciando transformación de datos...")
    
    # Generar timestamp para esta ejecución
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"+ Timestamp de ejecución: {timestamp}")
    
    # PASO 1: CURADO - Limpiar datos y guardar en curated/
    print("Limpiando datos para curado...")
    df_regional_clean = df_regional.dropna(subset=['dato_region'])
    df_departamental_clean = df_departamental.dropna(subset=['dato_departamento'])
    df_municipal_clean = df_municipal.dropna(subset=['dato_municipio'])
    
    # Mostrar estadísticas de limpieza
    regional_filtered = len(df_regional) - len(df_regional_clean)
    departamental_filtered = len(df_departamental) - len(df_departamental_clean)
    municipal_filtered = len(df_municipal) - len(df_municipal_clean)
    
    if regional_filtered > 0:
        print(f"  ! Filtrados {regional_filtered} registros regionales con valores NULL")
    if departamental_filtered > 0:
        print(f"  ! Filtrados {departamental_filtered} registros departamentales con valores NULL")
    if municipal_filtered > 0:
        print(f"  ! Filtrados {municipal_filtered} registros municipales con valores NULL")
    
    # Guardar datos curados
    save_curated_data(df_regional_clean, df_departamental_clean, df_municipal_clean, timestamp)
    
    # PASO 2: PROCESADO - Normalizar y guardar en processed/
    print("Normalizando datos para procesado...")
    df_geografia = create_geografia_table(df_regional_clean, df_departamental_clean, df_municipal_clean)
    df_indicadores = create_indicadores_table(df_regional_clean, df_departamental_clean, df_municipal_clean)
    df_medicion = create_datos_medicion_table(df_regional_clean, df_departamental_clean, df_municipal_clean, 
                                            df_geografia, df_indicadores)
    
    # Guardar datos procesados
    save_processed_data(df_geografia, df_indicadores, df_medicion, timestamp)
    
    print("+ Transformacion completada exitosamente")
    
    return df_geografia, df_indicadores, df_medicion, timestamp


def main():
    """Función principal para el módulo de transformación."""
    try:
        # Extraer datos
        df_regional, df_departamental, df_municipal = extract_excel_files()
        validate_dataframes(df_regional, df_departamental, df_municipal)
        
        # Transformar datos
        df_geografia, df_indicadores, df_medicion, timestamp = transform_data(
            df_regional, df_departamental, df_municipal
        )
        
        print("\n=== Resumen de Transformación ===")
        print(f"Geografía: {len(df_geografia)} registros")
        print(f"Indicadores: {len(df_indicadores)} registros") 
        print(f"Datos medición: {len(df_medicion)} registros")
        print("Transformacion completada exitosamente")
        
        return df_geografia, df_indicadores, df_medicion, timestamp
        
    except Exception as e:
        print(f"Error en transformación: {e}")
        return None


if __name__ == "__main__":
    main() 