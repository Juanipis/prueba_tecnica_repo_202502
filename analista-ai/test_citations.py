#!/usr/bin/env python3
"""
Script de prueba para verificar las herramientas de citación web del SmolAgent.

Este script prueba:
1. El formateo de citas individuales
2. La creación de secciones de fuentes
3. La integración con el agente
"""

import sys
import os

# Agregar el directorio actual al path para importar módulos locales
sys.path.insert(0, os.path.dirname(__file__))

def test_format_web_citation():
    """Prueba la herramienta de formateo de citas individuales."""
    try:
        from core.sql_tools import format_web_citation
        
        print("📚 Probando formateo de citas individuales...")
        
        # Casos de prueba
        test_cases = [
            "Política Nacional de Seguridad Alimentaria, Ministerio de Salud Colombia, 2024, https://minsalud.gov.co/politicas",
            "Estadísticas de inseguridad alimentaria, FAO Colombia, 2023, https://fao.org/colombia/estadisticas",
            "Programas contra la pobreza, Gobierno de Colombia, s.f., https://gobierno.gov.co/programas"
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Caso de prueba {i} ---")
            print(f"Entrada: {test_case}")
            
            result = format_web_citation(test_case, "apa")
            print(f"Cita APA: {result}")
            
            result_simple = format_web_citation(test_case, "simple")
            print(f"Cita simple: {result_simple}")
        
        print("✅ Formateo de citas: OK")
        return True
        
    except Exception as e:
        print(f"❌ Error en formateo de citas: {e}")
        return False

def test_create_sources_section():
    """Prueba la herramienta de creación de secciones de fuentes."""
    try:
        from core.sql_tools import create_sources_section
        
        print("\n📖 Probando creación de secciones de fuentes...")
        
        # Lista de fuentes de prueba
        sources_test = """Política Nacional de Seguridad Alimentaria, Ministerio de Salud Colombia, 2024, https://minsalud.gov.co/politicas;
        Estadísticas de inseguridad alimentaria, FAO Colombia, 2023, https://fao.org/colombia/estadisticas;
        Programas contra la pobreza, Gobierno de Colombia, 2024, https://gobierno.gov.co/programas"""
        
        print("Fuentes de entrada:")
        for line in sources_test.split(';'):
            print(f"  - {line.strip()}")
        
        result = create_sources_section(sources_test)
        print("\nSección generada:")
        print(result)
        
        print("✅ Creación de secciones: OK")
        return True
        
    except Exception as e:
        print(f"❌ Error en creación de secciones: {e}")
        return False

def test_agent_integration():
    """Prueba la integración de las herramientas de citación con el agente."""
    try:
        from core.smolagent import food_security_agent
        
        if not food_security_agent:
            print("❌ Agente no inicializado")
            return False
        
        print("\n🤖 Probando integración con el agente...")
        
        # Verificar que las herramientas están disponibles en el agente
        tools_names = [tool.name for tool in food_security_agent.agent.tools if hasattr(tool, 'name')]
        
        citation_tools = ['format_web_citation', 'create_sources_section']
        available_citation_tools = [tool for tool in citation_tools if tool in tools_names]
        
        print(f"Herramientas de citación disponibles: {available_citation_tools}")
        
        if len(available_citation_tools) == len(citation_tools):
            print("✅ Todas las herramientas de citación están integradas")
            return True
        else:
            missing = set(citation_tools) - set(available_citation_tools)
            print(f"❌ Herramientas faltantes: {missing}")
            return False
            
    except Exception as e:
        print(f"❌ Error en integración del agente: {e}")
        return False

def test_citation_instructions():
    """Verifica que las instrucciones de citación estén en el contexto del agente."""
    try:
        from core.smolagent import food_security_agent
        
        if not food_security_agent:
            print("❌ Agente no inicializado")
            return False
        
        print("\n📋 Verificando instrucciones de citación...")
        
        # Crear una pregunta de prueba para ver el contexto
        test_question = "pregunta de prueba"
        context = food_security_agent._enhance_question_with_context(test_question)
        
        # Verificar que el contexto incluya instrucciones de citación
        citation_keywords = [
            "INSTRUCCIONES OBLIGATORIAS PARA CITAR FUENTES WEB",
            "📚 Fuentes Consultadas",
            "format_web_citation",
            "create_sources_section"
        ]
        
        found_keywords = []
        for keyword in citation_keywords:
            if keyword in context:
                found_keywords.append(keyword)
        
        print(f"Instrucciones de citación encontradas: {len(found_keywords)}/{len(citation_keywords)}")
        for keyword in found_keywords:
            print(f"  ✅ {keyword}")
        
        missing_keywords = set(citation_keywords) - set(found_keywords)
        for keyword in missing_keywords:
            print(f"  ❌ {keyword}")
        
        if len(found_keywords) == len(citation_keywords):
            print("✅ Todas las instrucciones de citación están presentes")
            return True
        else:
            print("⚠️ Algunas instrucciones de citación pueden estar faltando")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando instrucciones: {e}")
        return False

def main():
    """Función principal de pruebas."""
    print("🧪 PRUEBAS DE SISTEMA DE CITACIÓN WEB")
    print("=" * 50)
    
    # Test 1: Formateo de citas individuales
    test1_ok = test_format_web_citation()
    
    # Test 2: Creación de secciones de fuentes
    test2_ok = test_create_sources_section()
    
    # Test 3: Integración con agente
    test3_ok = test_agent_integration()
    
    # Test 4: Verificación de instrucciones
    test4_ok = test_citation_instructions()
    
    # Resumen
    print("\n📊 RESUMEN DE PRUEBAS")
    print("-" * 25)
    print(f"Formateo de citas: {'✅' if test1_ok else '❌'}")
    print(f"Secciones de fuentes: {'✅' if test2_ok else '❌'}")
    print(f"Integración con agente: {'✅' if test3_ok else '❌'}")
    print(f"Instrucciones de citación: {'✅' if test4_ok else '❌'}")
    
    all_passed = test1_ok and test2_ok and test3_ok and test4_ok
    
    if all_passed:
        print("\n🎉 ¡Todas las pruebas pasaron! Sistema de citación listo para usar.")
        print("\n💡 Ejemplo de pregunta que generará citas:")
        print('   "¿Cuáles son las políticas de seguridad alimentaria de Colombia')
        print('    según fuentes oficiales y cómo se comparan con nuestros datos?"')
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisa la configuración.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 