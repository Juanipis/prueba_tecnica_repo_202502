# Backend core modules para SmolAgents con búsqueda web
from .smolagent import food_security_agent, InseguridadAlimentariaAgent
from .sql_tools import (
    sql_query,
    get_database_schema,
    analyze_data_pandas,
    get_top_entities,
    compare_years,
    calculate_statistics,
    create_formatted_table,
    get_available_years,
    get_available_indicators,
    get_entities_by_level,
    quick_summary,
    create_chart_visualization,
    create_multiple_charts,
    analyze_and_visualize,
    format_web_citation,
    create_sources_section,
    extract_analysis_keywords,
    create_formatted_markdown_table,
    get_stored_images,
    clear_stored_images
)

__all__ = [
    'food_security_agent',
    'InseguridadAlimentariaAgent',
    'sql_query',
    'get_database_schema',
    'analyze_data_pandas',
    'get_top_entities',
    'compare_years',
    'calculate_statistics',
    'create_formatted_table',
    'get_available_years',
    'get_available_indicators',
    'get_entities_by_level',
    'quick_summary',
    'create_chart_visualization',
    'create_multiple_charts',
    'analyze_and_visualize',
    'format_web_citation',
    'create_sources_section',
    'extract_analysis_keywords',
    'create_formatted_markdown_table',
    'get_stored_images',
    'clear_stored_images'
] 