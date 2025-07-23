#!/usr/bin/env python3
"""
Script de prueba para verificar las mejoras de tablas Markdown y palabras clave.

Este script prueba:
1. El formato correcto de tablas Markdown
2. La extracción de palabras clave
3. La integración con el agente
4. El renderizado en el frontend
"""

import sys
import os

# Agregar el directorio actual al path para importar módulos locales
sys.path.insert(0, os.path.dirname(__file__))

def test_markdown_table_formatting():
    """Prueba la herramienta de formato de tablas Markdown."""
    try:
        from core.sql_tools import create_formatted_markdown_table
        
        print("📊 Probando formato de tablas Markdown...")
        
        # Consulta de prueba
        test_query = """
        SELECT 
            g.nombre as "Departamento",
            i.nombre_indicador as "Indicador",
            dm.año as "Año",
            ROUND(dm.valor * 100, 1) as "Porcentaje"
        FROM datos_medicion dm
        JOIN geografia g ON dm.id_geografia = g.id_geografia
        JOIN indicadores i ON dm.id_indicador = i.id_indicador
        WHERE g.nivel = 'Departamental' 
            AND dm.año = 2022
            AND i.nombre_indicador LIKE '%Grave%'
        ORDER BY dm.valor DESC
        LIMIT 5
        """
        
        result = create_formatted_markdown_table(test_query, "Top 5 Departamentos - Inseguridad Grave 2022")
        
        print("Tabla generada:")
        print(result)
        print("✅ Formato de tablas Markdown: OK")
        return True
        
    except Exception as e:
        print(f"❌ Error en formato de tablas: {e}")
        return False

def test_keyword_extraction():
    """Prueba la herramienta de extracción de palabras clave."""
    try:
        from core.sql_tools import extract_analysis_keywords
        
        print("\n🔍 Probando extracción de palabras clave...")
        
        # Texto de análisis de prueba
        sample_analysis = """
        # Análisis de Inseguridad Alimentaria en Colombia 2022

        ## Datos Generales
        El análisis de los datos de inseguridad alimentaria en Colombia para el año 2022 
        muestra que Chocó presenta la mayor prevalencia de inseguridad alimentaria grave 
        con un 28.5%, seguido por La Guajira con 24.2% y Nariño con 22.8%.

        ## Estadísticas Descriptivas
        La media nacional de inseguridad alimentaria moderada es de 15.4%, con una 
        desviación estándar de 8.3%. Los departamentos de Antioquia y Cundinamarca 
        muestran valores por debajo del promedio nacional.

        ## Comparación Regional
        Las regiones del Pacífico y Caribe presentan los mayores índices, mientras que 
        la región Andina mantiene niveles más bajos. Se observa una correlación negativa 
        entre desarrollo económico e inseguridad alimentaria.

        ## Gráficas Generadas
        Se han creado visualizaciones que muestran la distribución por departamentos 
        y la evolución temporal desde 2015 hasta 2022.
        """
        
        keywords = extract_analysis_keywords(sample_analysis, 12)
        
        print(f"Palabras clave extraídas: {keywords}")
        print("✅ Extracción de palabras clave: OK")
        return True
        
    except Exception as e:
        print(f"❌ Error en extracción de palabras clave: {e}")
        return False

def test_agent_integration():
    """Prueba la integración de las nuevas herramientas con el agente."""
    try:
        from core.smolagent import food_security_agent
        
        if not food_security_agent:
            print("❌ Agente no inicializado")
            return False
        
        print("\n🤖 Probando integración con el agente...")
        
        # Verificar que las herramientas están disponibles
        tools_names = [tool.name for tool in food_security_agent.agent.tools if hasattr(tool, 'name')]
        
        required_tools = ['create_formatted_markdown_table', 'extract_analysis_keywords']
        available_tools = [tool for tool in required_tools if tool in tools_names]
        
        print(f"Herramientas nuevas disponibles: {available_tools}")
        
        if len(available_tools) == len(required_tools):
            print("✅ Todas las herramientas nuevas están integradas")
            return True
        else:
            missing = set(required_tools) - set(available_tools)
            print(f"❌ Herramientas faltantes: {missing}")
            return False
            
    except Exception as e:
        print(f"❌ Error en integración del agente: {e}")
        return False

def test_context_instructions():
    """Verifica que las nuevas instrucciones estén en el contexto del agente."""
    try:
        from core.smolagent import food_security_agent
        
        if not food_security_agent:
            print("❌ Agente no inicializado")
            return False
        
        print("\n📋 Verificando instrucciones de tablas y palabras clave...")
        
        # Crear una pregunta de prueba para ver el contexto
        test_question = "pregunta de prueba"
        context = food_security_agent._enhance_question_with_context(test_question)
        
        # Verificar que el contexto incluya las nuevas instrucciones
        required_instructions = [
            "INSTRUCCIONES PARA TABLAS MARKDOWN",
            "create_formatted_markdown_table",
            "INSTRUCCIONES PARA PALABRAS CLAVE",
            "extract_analysis_keywords"
        ]
        
        found_instructions = []
        for instruction in required_instructions:
            if instruction in context:
                found_instructions.append(instruction)
        
        print(f"Instrucciones encontradas: {len(found_instructions)}/{len(required_instructions)}")
        for instruction in found_instructions:
            print(f"  ✅ {instruction}")
        
        missing_instructions = set(required_instructions) - set(found_instructions)
        for instruction in missing_instructions:
            print(f"  ❌ {instruction}")
        
        if len(found_instructions) == len(required_instructions):
            print("✅ Todas las instrucciones están presentes")
            return True
        else:
            print("⚠️ Algunas instrucciones pueden estar faltando")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando instrucciones: {e}")
        return False

def test_markdown_table_regex():
    """Prueba que el regex de tablas Markdown en el frontend funcione."""
    print("\n🔧 Probando regex de tablas Markdown para el frontend...")
    
    # Ejemplo de tabla Markdown bien formateada
    sample_table = """
### Top 5 Departamentos - Inseguridad Grave 2022

| Departamento | Indicador | Año | Porcentaje |
|--------------|-----------|-----|------------|
| Chocó | Inseguridad Alimentaria Grave | 2022 | 28.5% |
| La Guajira | Inseguridad Alimentaria Grave | 2022 | 24.2% |
| Nariño | Inseguridad Alimentaria Grave | 2022 | 22.8% |
| Córdoba | Inseguridad Alimentaria Grave | 2022 | 20.1% |
| Cauca | Inseguridad Alimentaria Grave | 2022 | 19.7% |
"""
    
    # Simular el regex del frontend
    import re
    
    table_pattern = r'(\|[^|\n]*\|[\s\S]*?\n(?:\|[^|\n]*\|.*\n?)*)'
    matches = re.findall(table_pattern, sample_table)
    
    if matches:
        print(f"✅ Regex detectó {len(matches)} tabla(s)")
        print("Primera tabla detectada:")
        print(matches[0][:200] + "..." if len(matches[0]) > 200 else matches[0])
        return True
    else:
        print("❌ Regex no detectó tablas")
        return False

def main():
    """Función principal de pruebas."""
    print("🧪 PRUEBAS DE TABLAS MARKDOWN Y PALABRAS CLAVE")
    print("=" * 60)
    
    # Test 1: Formato de tablas Markdown
    test1_ok = test_markdown_table_formatting()
    
    # Test 2: Extracción de palabras clave
    test2_ok = test_keyword_extraction()
    
    # Test 3: Integración con agente
    test3_ok = test_agent_integration()
    
    # Test 4: Verificación de instrucciones
    test4_ok = test_context_instructions()
    
    # Test 5: Regex de frontend
    test5_ok = test_markdown_table_regex()
    
    # Resumen
    print("\n📊 RESUMEN DE PRUEBAS")
    print("-" * 35)
    print(f"Formato de tablas Markdown: {'✅' if test1_ok else '❌'}")
    print(f"Extracción de palabras clave: {'✅' if test2_ok else '❌'}")
    print(f"Integración con agente: {'✅' if test3_ok else '❌'}")
    print(f"Instrucciones de contexto: {'✅' if test4_ok else '❌'}")
    print(f"Regex de frontend: {'✅' if test5_ok else '❌'}")
    
    all_passed = test1_ok and test2_ok and test3_ok and test4_ok and test5_ok
    
    if all_passed:
        print("\n🎉 ¡Todas las pruebas pasaron! Sistema de tablas y palabras clave listo.")
        print("\n💡 Ejemplos de preguntas que generarán tablas y palabras clave:")
        print('   "¿Cuáles son las estadísticas de inseguridad alimentaria por departamento')
        print('    en 2022? Muestra los resultados en una tabla formateada"')
        print('   "Analiza la distribución por regiones e incluye palabras clave del análisis"')
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisa la configuración.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 