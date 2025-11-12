"""
Fuzzy Matching Utilities

Implements Levenshtein distance algorithm for typo detection
and correction suggestions in SQL table/column names.
"""

from typing import List, Optional, Tuple, Dict
from cachetools import LRUCache

# Cache for fuzzy match results (avoid repeated distance calculations)
_fuzzy_match_cache: LRUCache = LRUCache(maxsize=1000)


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein (edit) distance between two strings

    Measures minimum number of single-character edits (insertions,
    deletions, substitutions) to transform s1 into s2.

    Algorithm: Dynamic programming
    Time complexity: O(m * n) where m, n are string lengths
    Space complexity: O(n)

    Args:
        s1: First string
        s2: Second string

    Returns:
        Edit distance (integer >= 0)

    Examples:
        >>> levenshtein_distance("kitten", "sitting")
        3
        >>> levenshtein_distance("lead_status", "status")
        5
    """
    # Ensure s1 is the longer string for optimization
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    # Empty string case
    if len(s2) == 0:
        return len(s1)

    # Initialize previous row of distances
    previous_row = list(range(len(s2) + 1))

    # Calculate distances row by row
    for i, c1 in enumerate(s1):
        current_row = [i + 1]

        for j, c2 in enumerate(s2):
            # Cost of operations
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (0 if c1 == c2 else 1)

            current_row.append(min(insertions, deletions, substitutions))

        previous_row = current_row

    return previous_row[-1]


def fuzzy_match(
    typo: str,
    valid_options: List[str],
    max_distance: int = 2,
    case_sensitive: bool = False
) -> Optional[str]:
    """
    Find closest match using Levenshtein distance

    Args:
        typo: Incorrect string to correct
        valid_options: List of valid strings to match against
        max_distance: Maximum edit distance to consider (default: 2)
        case_sensitive: Whether to do case-sensitive matching (default: False)

    Returns:
        Closest matching string or None if no match within max_distance

    Examples:
        >>> fuzzy_match("lead_status", ["status", "name", "country"])
        None  # distance too large
        >>> fuzzy_match("statuss", ["status", "name", "country"])
        'status'  # distance = 1
        >>> fuzzy_match("leads.id", ["leads.lead_id", "leads.name"])
        'leads.lead_id'  # distance = 7 but partial match
    """
    # Create cache key
    cache_key = (
        typo if case_sensitive else typo.lower(),
        tuple(sorted(opt if case_sensitive else opt.lower() for opt in valid_options)),
        max_distance,
        case_sensitive
    )

    # Check cache
    if cache_key in _fuzzy_match_cache:
        return _fuzzy_match_cache[cache_key]

    # Prepare strings for matching
    search_string = typo if case_sensitive else typo.lower()
    matches: List[Tuple[str, int]] = []

    for option in valid_options:
        compare_string = option if case_sensitive else option.lower()

        # Calculate edit distance
        distance = levenshtein_distance(search_string, compare_string)

        if distance <= max_distance:
            matches.append((option, distance))

    # No matches found
    if not matches:
        result = None
    else:
        # Return closest match (minimum distance)
        result = min(matches, key=lambda x: x[1])[0]

    # Cache result
    _fuzzy_match_cache[cache_key] = result

    return result


def fuzzy_match_with_score(
    typo: str,
    valid_options: List[str],
    max_distance: int = 2,
    case_sensitive: bool = False
) -> List[Tuple[str, int]]:
    """
    Find all matches within distance threshold with scores

    Args:
        typo: Incorrect string to correct
        valid_options: List of valid strings to match against
        max_distance: Maximum edit distance to consider
        case_sensitive: Whether to do case-sensitive matching

    Returns:
        List of (match, distance) tuples, sorted by distance

    Examples:
        >>> fuzzy_match_with_score("stat", ["status", "state", "stat", "name"])
        [('stat', 0), ('state', 1), ('status', 2)]
    """
    search_string = typo if case_sensitive else typo.lower()
    matches: List[Tuple[str, int]] = []

    for option in valid_options:
        compare_string = option if case_sensitive else option.lower()
        distance = levenshtein_distance(search_string, compare_string)

        if distance <= max_distance:
            matches.append((option, distance))

    # Sort by distance (closest first)
    return sorted(matches, key=lambda x: x[1])


def fuzzy_match_column(
    typo: str,
    schema,  # DatabaseSchema object
    table_context: Optional[str] = None,
    max_distance: int = 2
) -> Optional[str]:
    """
    Find closest column name match using schema context

    If table_context is provided, searches only that table.
    Otherwise searches all tables.

    Args:
        typo: Incorrect column name
        schema: DatabaseSchema object
        table_context: Optional table name to narrow search
        max_distance: Maximum edit distance

    Returns:
        Closest matching column name or None
    """
    if table_context:
        # Search specific table
        table = schema.get_table(table_context)
        if table:
            valid_columns = list(table.columns.keys())
            return fuzzy_match(typo, valid_columns, max_distance)
        return None
    else:
        # Search all tables
        all_columns = []
        for table in schema.tables.values():
            all_columns.extend(table.columns.keys())

        # Remove duplicates while preserving order
        seen = set()
        unique_columns = []
        for col in all_columns:
            col_lower = col.lower()
            if col_lower not in seen:
                seen.add(col_lower)
                unique_columns.append(col)

        return fuzzy_match(typo, unique_columns, max_distance)


def fuzzy_match_table(
    typo: str,
    schema,  # DatabaseSchema object
    max_distance: int = 2
) -> Optional[str]:
    """
    Find closest table name match using schema

    Args:
        typo: Incorrect table name
        schema: DatabaseSchema object
        max_distance: Maximum edit distance

    Returns:
        Closest matching table name or None
    """
    valid_tables = list(schema.tables.keys())
    return fuzzy_match(typo, valid_tables, max_distance)


def calculate_similarity_score(s1: str, s2: str) -> float:
    """
    Calculate similarity score between two strings (0.0 to 1.0)

    Uses normalized Levenshtein distance.
    Score of 1.0 = identical, 0.0 = completely different

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not s1 or not s2:
        return 0.0

    max_len = max(len(s1), len(s2))
    distance = levenshtein_distance(s1.lower(), s2.lower())

    return 1.0 - (distance / max_len)


def get_best_matches(
    query: str,
    candidates: List[str],
    top_k: int = 3,
    min_similarity: float = 0.5
) -> List[Tuple[str, float]]:
    """
    Get top-k best matches with similarity scores

    Args:
        query: Query string
        candidates: List of candidate strings
        top_k: Number of top matches to return
        min_similarity: Minimum similarity threshold (0.0 to 1.0)

    Returns:
        List of (candidate, similarity_score) tuples
    """
    scored_candidates = []

    for candidate in candidates:
        score = calculate_similarity_score(query, candidate)
        if score >= min_similarity:
            scored_candidates.append((candidate, score))

    # Sort by score descending
    scored_candidates.sort(key=lambda x: x[1], reverse=True)

    return scored_candidates[:top_k]


def clear_cache():
    """Clear the fuzzy match cache"""
    global _fuzzy_match_cache
    _fuzzy_match_cache.clear()
