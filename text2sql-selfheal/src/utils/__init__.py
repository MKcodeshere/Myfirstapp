"""
Utilities package for Text-to-SQL Self-Healing System
"""

from .error_taxonomy import (
    ERROR_TAXONOMY,
    ErrorCategory,
    get_error_category,
    is_simple_error,
    get_repair_method,
    format_compact_taxonomy,
    sort_errors_by_priority
)

from .schema import (
    Column,
    Table,
    DatabaseSchema
)

from .fuzzy_match import (
    levenshtein_distance,
    fuzzy_match,
    fuzzy_match_with_score,
    fuzzy_match_column,
    fuzzy_match_table,
    calculate_similarity_score,
    get_best_matches
)

__all__ = [
    # Error taxonomy
    'ERROR_TAXONOMY',
    'ErrorCategory',
    'get_error_category',
    'is_simple_error',
    'get_repair_method',
    'format_compact_taxonomy',
    'sort_errors_by_priority',

    # Schema
    'Column',
    'Table',
    'DatabaseSchema',

    # Fuzzy matching
    'levenshtein_distance',
    'fuzzy_match',
    'fuzzy_match_with_score',
    'fuzzy_match_column',
    'fuzzy_match_table',
    'calculate_similarity_score',
    'get_best_matches',
]
