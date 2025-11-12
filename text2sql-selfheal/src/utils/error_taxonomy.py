"""
Error Taxonomy for Text-to-SQL Self-Healing System

Defines 29 error types across 7 categories:
- Syntax (S): SQL syntax errors
- Schema (SC): Table/column mismatches
- Join (J): JOIN-related errors
- Filter (F): WHERE clause errors
- Aggregation (A): GROUP BY/aggregate errors
- Structural (T): Missing clauses
- Logical (L): Intent/scope errors
"""

from typing import Dict, List
from enum import Enum


class ErrorCategory(Enum):
    """Error categories"""
    SYNTAX = "SYNTAX"
    SCHEMA = "SCHEMA"
    JOIN = "JOIN"
    FILTER = "FILTER"
    AGGREGATION = "AGGREGATION"
    STRUCTURAL = "STRUCTURAL"
    LOGICAL = "LOGICAL"


# Complete Error Taxonomy: 29 types across 7 categories
ERROR_TAXONOMY = {
    "Syntax (S)": {
        "S1": "Invalid SQL syntax",
        "S2": "Unbalanced parentheses",
        "S3": "Invalid identifiers",
        "S4": "Missing keywords"
    },
    "Schema (SC)": {
        "SC1": "Non-existent table",
        "SC2": "Non-existent column",
        "SC3": "Wrong foreign key",
        "SC4": "Ambiguous column reference",
        "SC5": "Schema type mismatch"
    },
    "Join (J)": {
        "J1": "Missing JOIN clause",
        "J2": "Wrong JOIN type",
        "J3": "Missing ON clause",
        "J4": "Wrong JOIN columns",
        "J5": "Unnecessary table"
    },
    "Filter (F)": {
        "F1": "Wrong WHERE column",
        "F2": "Type mismatch in condition",
        "F3": "Missing condition",
        "F4": "Wrong logical operator",
        "F5": "Invalid comparison operator"
    },
    "Aggregation (A)": {
        "A1": "Missing GROUP BY",
        "A2": "Wrong GROUP BY columns",
        "A3": "HAVING vs WHERE confusion",
        "A4": "Wrong aggregate function"
    },
    "Structural (T)": {
        "T1": "Missing ORDER BY",
        "T2": "Missing LIMIT",
        "T3": "Subquery issue",
        "T4": "Wrong set operation",
        "T5": "Missing DISTINCT"
    },
    "Logical (L)": {
        "L1": "Wrong query scope (global vs grouped)",
        "L2": "Missing subquery correlation",
        "L3": "Intent mismatch"
    }
}


# Error frequency distribution (based on research)
ERROR_FREQUENCY = {
    "SC2": 22,  # Wrong column name
    "SC1": 13,  # Wrong table name
    "J1": 11,   # Missing JOIN
    "A1": 9,    # Missing GROUP BY
    "J4": 8,    # Wrong JOIN columns
    "SC4": 6,   # Ambiguous column
    "F2": 5,    # Type mismatch
    "L1": 5,    # Wrong query scope
    "J3": 4,    # Missing ON clause
    "A3": 3,    # HAVING vs WHERE
}


# Error repair methods
ERROR_REPAIR_METHOD = {
    # Syntax errors - Rule-based
    "S1": "rule_based",
    "S2": "rule_based",
    "S3": "rule_based",
    "S4": "rule_based",

    # Schema errors - Rule-based (fuzzy matching)
    "SC1": "rule_based",
    "SC2": "rule_based",
    "SC3": "rule_based",
    "SC4": "rule_based",
    "SC5": "rule_based",

    # Join errors - Hybrid
    "J1": "rule_based",
    "J2": "hybrid",
    "J3": "rule_based",
    "J4": "rule_based",
    "J5": "llm_guided",

    # Filter errors - Rule-based
    "F1": "rule_based",
    "F2": "rule_based",
    "F3": "rule_based",
    "F4": "rule_based",
    "F5": "rule_based",

    # Aggregation errors - Rule-based
    "A1": "rule_based",
    "A2": "rule_based",
    "A3": "rule_based",
    "A4": "hybrid",

    # Structural errors - Hybrid
    "T1": "hybrid",
    "T2": "hybrid",
    "T3": "llm_guided",
    "T4": "hybrid",
    "T5": "rule_based",

    # Logical errors - LLM-guided
    "L1": "llm_guided",
    "L2": "llm_guided",
    "L3": "llm_guided",
}


def get_error_category(error_code: str) -> ErrorCategory:
    """
    Get the category for an error code

    Args:
        error_code: Error code (e.g., 'SC2', 'J1')

    Returns:
        ErrorCategory enum value
    """
    # Check multi-character prefixes first
    if error_code.startswith('SC'):
        return ErrorCategory.SCHEMA

    # Then check single-character prefixes
    prefix = error_code[0] if len(error_code) > 0 else ""

    if prefix == 'S':
        return ErrorCategory.SYNTAX
    elif prefix == 'J':
        return ErrorCategory.JOIN
    elif prefix == 'F':
        return ErrorCategory.FILTER
    elif prefix == 'A':
        return ErrorCategory.AGGREGATION
    elif prefix == 'T':
        return ErrorCategory.STRUCTURAL
    elif prefix == 'L':
        return ErrorCategory.LOGICAL
    else:
        raise ValueError(f"Unknown error code: {error_code}")


def is_simple_error(error_codes: List[str]) -> bool:
    """
    Determine if errors can be handled by rule-based repair

    Simple errors are those in categories: SYNTAX, SCHEMA, AGGREGATION, FILTER
    Complex errors require LLM-guided correction

    Args:
        error_codes: List of error codes

    Returns:
        True if all errors are simple (rule-based), False otherwise
    """
    simple_categories = {
        ErrorCategory.SYNTAX,
        ErrorCategory.SCHEMA,
        ErrorCategory.AGGREGATION,
        ErrorCategory.FILTER
    }

    for code in error_codes:
        category = get_error_category(code)
        if category not in simple_categories:
            # Check if error can be handled by rules
            if ERROR_REPAIR_METHOD.get(code) == "llm_guided":
                return False

    return True


def get_repair_method(error_code: str) -> str:
    """
    Get the recommended repair method for an error code

    Args:
        error_code: Error code (e.g., 'SC2', 'J1')

    Returns:
        Repair method: 'rule_based', 'hybrid', or 'llm_guided'
    """
    return ERROR_REPAIR_METHOD.get(error_code, "llm_guided")


def format_compact_taxonomy() -> str:
    """
    Format error taxonomy for LLM context (compact representation)

    Returns:
        Formatted string of error taxonomy
    """
    lines = []
    for category, errors in ERROR_TAXONOMY.items():
        lines.append(f"\n{category}:")
        for code, description in errors.items():
            lines.append(f"  {code}: {description}")

    return "\n".join(lines)


def get_error_description(error_code: str) -> str:
    """
    Get human-readable description for an error code

    Args:
        error_code: Error code (e.g., 'SC2', 'J1')

    Returns:
        Error description
    """
    for category, errors in ERROR_TAXONOMY.items():
        if error_code in errors:
            return errors[error_code]

    return "Unknown error"


# Priority order for error repair (fix higher priority first)
ERROR_PRIORITY = {
    ErrorCategory.SYNTAX: 1,      # Fix syntax first
    ErrorCategory.SCHEMA: 2,      # Then schema issues
    ErrorCategory.JOIN: 3,        # Then joins
    ErrorCategory.AGGREGATION: 4, # Then aggregation
    ErrorCategory.FILTER: 5,      # Then filters
    ErrorCategory.STRUCTURAL: 6,  # Then structural
    ErrorCategory.LOGICAL: 7,     # Finally logical
}


def sort_errors_by_priority(errors: List[Dict]) -> List[Dict]:
    """
    Sort errors by priority (syntax > schema > join > aggregation > filter > structural > logical)

    Args:
        errors: List of error dictionaries with 'type' field

    Returns:
        Sorted list of errors
    """
    def get_priority(error):
        error_code = error.get('type', '')
        category = get_error_category(error_code)
        return ERROR_PRIORITY.get(category, 99)

    return sorted(errors, key=get_priority)
