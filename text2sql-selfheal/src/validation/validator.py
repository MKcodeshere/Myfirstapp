"""
Validation Module (Phase 4)

Prevents mis-repairs (making queries worse):
- Syntax validation
- Schema validation
- Error comparison
- Confidence estimation

Conservative approach: Prefer no repair over bad repair
"""

from typing import Optional, Tuple
import re
import sqlglot
from sqlglot import parse_one
from sqlglot.errors import ParseError
from sqlglot import exp

from ..utils.schema import DatabaseSchema
from ..detection.error_detector import ErrorDetector


# Confidence threshold for accepting repairs
CONFIDENCE_THRESHOLD = 0.7


class RepairValidator:
    """
    Validator for repaired SQL queries

    Ensures that repairs improve the SQL without introducing new errors.
    """

    def __init__(self, schema: DatabaseSchema):
        """
        Initialize validator

        Args:
            schema: Database schema for validation
        """
        self.schema = schema
        self.error_detector = ErrorDetector(schema)

    def validate_repair(
        self,
        original_sql: str,
        repaired_sql: str
    ) -> Tuple[bool, str]:
        """
        Validate that repair improved the SQL

        Args:
            original_sql: SQL before repair
            repaired_sql: SQL after repair

        Returns:
            Tuple of (is_valid, reason)
            - is_valid: Boolean indicating if repair is acceptable
            - reason: Description of validation result
        """
        # Check 1: Is it syntactically valid?
        try:
            ast = parse_one(repaired_sql, dialect='sqlite')
        except ParseError as e:
            return False, f"Syntax error in repaired SQL: {str(e)}"

        # Check 2: Did we actually change something?
        if self._normalize_sql(original_sql) == self._normalize_sql(repaired_sql):
            return False, "No actual modification made"

        # Check 3: Are all schema elements valid?
        if not self._all_tables_exist(ast):
            return False, "Repaired SQL contains non-existent tables"

        if not self._all_columns_exist(ast):
            return False, "Repaired SQL contains non-existent columns"

        # Check 4: Compare error counts
        try:
            original_errors = self.error_detector.detect_errors(original_sql)
        except:
            original_errors = []

        try:
            new_errors = self.error_detector.detect_errors(repaired_sql)
        except:
            # If we can't detect errors in repaired SQL, it might be invalid
            return False, "Cannot validate repaired SQL"

        if len(new_errors) > len(original_errors):
            return False, f"Repair introduced more errors ({len(new_errors)} vs {len(original_errors)})"

        # Check 5: Confidence estimation
        confidence = self._estimate_confidence(repaired_sql, ast)

        if confidence < CONFIDENCE_THRESHOLD:
            return False, f"Low confidence in repair ({confidence:.2f} < {CONFIDENCE_THRESHOLD})"

        # All checks passed
        return True, f"Repair validated (confidence: {confidence:.2f}, errors reduced: {len(original_errors)} → {len(new_errors)})"

    def _normalize_sql(self, sql: str) -> str:
        """
        Normalize SQL for comparison

        Args:
            sql: SQL query string

        Returns:
            Normalized SQL (lowercase, no extra whitespace)
        """
        # Remove extra whitespace
        normalized = ' '.join(sql.split())

        # Convert to lowercase
        normalized = normalized.lower()

        # Remove semicolon at end
        normalized = normalized.rstrip(';')

        return normalized

    def _all_tables_exist(self, ast: exp.Expression) -> bool:
        """Check if all tables in AST exist in schema"""
        for table_node in ast.find_all(exp.Table):
            table_name = table_node.name
            if not self.schema.has_table(table_name):
                return False
        return True

    def _all_columns_exist(self, ast: exp.Expression) -> bool:
        """Check if all columns in AST exist in schema"""
        for column_node in ast.find_all(exp.Column):
            col_name = column_node.name

            # Skip wildcards
            if col_name == '*':
                continue

            # Get table context if available
            table_name = None
            if hasattr(column_node, 'table') and column_node.table:
                table_name = column_node.table

            # Check if column exists
            if not self.schema.has_column(col_name, table_name):
                return False

        return True

    def _estimate_confidence(self, sql: str, ast: exp.Expression) -> float:
        """
        Estimate confidence that repaired SQL is correct

        Factors:
        - Query complexity
        - Schema coverage
        - Structural soundness

        Args:
            sql: SQL query string
            ast: Parsed AST

        Returns:
            Confidence score 0.0-1.0
        """
        confidence = 1.0

        # Penalty for complexity
        complexity = self._calculate_complexity(ast)
        if complexity > 5:
            confidence *= 0.9

        # Penalty for subqueries
        num_subqueries = len(list(ast.find_all(exp.Subquery)))
        confidence *= (0.95 ** num_subqueries)

        # Penalty for multiple JOINs
        num_joins = len(list(ast.find_all(exp.Join)))
        if num_joins > 2:
            confidence *= 0.9

        # Bonus for schema alignment (all FK relationships valid)
        if self._all_foreign_keys_valid(ast):
            confidence *= 1.05

        return min(confidence, 1.0)

    def _calculate_complexity(self, ast: exp.Expression) -> int:
        """
        Calculate query complexity score

        Factors:
        - Number of tables
        - Number of joins
        - Number of subqueries
        - Number of aggregate functions
        - Number of conditions

        Returns:
            Complexity score (integer)
        """
        complexity = 0

        # Count tables
        complexity += len(list(ast.find_all(exp.Table)))

        # Count joins
        complexity += len(list(ast.find_all(exp.Join))) * 2

        # Count subqueries
        complexity += len(list(ast.find_all(exp.Subquery))) * 3

        # Count aggregates
        complexity += len(list(ast.find_all(exp.Sum)))
        complexity += len(list(ast.find_all(exp.Count)))
        complexity += len(list(ast.find_all(exp.Avg)))
        complexity += len(list(ast.find_all(exp.Min)))
        complexity += len(list(ast.find_all(exp.Max)))

        # Count conditions in WHERE
        where_clause = ast.find(exp.Where)
        if where_clause:
            complexity += len(list(where_clause.find_all(exp.EQ)))
            complexity += len(list(where_clause.find_all(exp.GT)))
            complexity += len(list(where_clause.find_all(exp.LT)))
            complexity += len(list(where_clause.find_all(exp.GTE)))
            complexity += len(list(where_clause.find_all(exp.LTE)))

        return complexity

    def _all_foreign_keys_valid(self, ast: exp.Expression) -> bool:
        """
        Check if all JOIN conditions use valid foreign keys

        Args:
            ast: Parsed AST

        Returns:
            True if all JOINs use valid FK relationships
        """
        for join_node in ast.find_all(exp.Join):
            if join_node.on:
                # Extract join columns from ON clause
                on_clause = join_node.on

                if isinstance(on_clause, exp.EQ):
                    left = on_clause.left
                    right = on_clause.right

                    if isinstance(left, exp.Column) and isinstance(right, exp.Column):
                        left_col = f"{left.table}.{left.name}" if left.table else left.name
                        right_col = f"{right.table}.{right.name}" if right.table else right.name

                        # Validate FK relationship
                        if not self.schema.is_valid_foreign_key(left_col, right_col):
                            return False

        return True
