# Backend core modules para SmolAgents
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
    quick_summary
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
    'quick_summary'
] 