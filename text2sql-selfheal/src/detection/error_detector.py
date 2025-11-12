"""
Error Detection Module (Phase 2)

Fast error detection using deterministic algorithms:
- SQL parsing to AST
- Schema validation
- Pattern matching
- Join validation
- Aggregation validation

Latency: 50-100ms (no LLM calls)
"""

from typing import List, Dict, Optional, Any
import sqlglot
from sqlglot import exp, parse_one
from sqlglot.errors import ParseError

from ..utils.schema import DatabaseSchema
from ..utils.fuzzy_match import fuzzy_match_table, fuzzy_match_column


class ErrorDetector:
    """
    Fast error detector for SQL queries

    Uses AST parsing and schema validation to detect errors
    without requiring LLM calls.
    """

    def __init__(self, schema: DatabaseSchema):
        """
        Initialize error detector

        Args:
            schema: Database schema for validation
        """
        self.schema = schema

    def detect_errors(self, sql: str) -> List[Dict[str, Any]]:
        """
        Detect all errors in SQL query

        Args:
            sql: SQL query string

        Returns:
            List of error dictionaries with structure:
            {
                'category': str,
                'type': str,
                'message': str,
                'token': Optional[str],
                'suggestion': Optional[str],
                'confidence': str,
                'location': Optional[Any]
            }
        """
        errors = []

        # Step 1: Parse SQL to AST
        try:
            ast = parse_one(sql, dialect='sqlite')
        except ParseError as e:
            errors.append({
                'category': 'SYNTAX',
                'type': 'S1',
                'message': f'Invalid SQL syntax: {str(e)}',
                'token': None,
                'suggestion': None,
                'confidence': 'high',
                'location': None
            })
            return errors  # Cannot proceed without valid AST

        # Step 2: Schema Validation
        errors.extend(self._detect_schema_errors(ast))

        # Step 3: Join Validation
        errors.extend(self._detect_join_errors(ast))

        # Step 4: Aggregation Validation
        errors.extend(self._detect_aggregation_errors(ast))

        # Step 5: Filter Validation
        errors.extend(self._detect_filter_errors(ast))

        # Step 6: Structural Validation
        errors.extend(self._detect_structural_errors(ast))

        return errors

    def _detect_schema_errors(self, ast: exp.Expression) -> List[Dict[str, Any]]:
        """
        Detect table/column name errors using fuzzy matching

        Checks:
        - SC1: Non-existent tables
        - SC2: Non-existent columns
        - SC4: Ambiguous column references

        Latency: 20-40ms
        """
        errors = []

        # Extract all table references
        for table_node in ast.find_all(exp.Table):
            table_name = table_node.name

            # Check if table exists in schema
            if not self.schema.has_table(table_name):
                # Find closest match using fuzzy matching
                suggestion = fuzzy_match_table(table_name, self.schema, max_distance=2)

                errors.append({
                    'category': 'SCHEMA',
                    'type': 'SC1',
                    'message': f"Table '{table_name}' does not exist",
                    'token': table_name,
                    'suggestion': suggestion,
                    'confidence': 'high' if suggestion else 'low',
                    'location': table_node
                })

        # Extract all column references
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
                # Find closest match
                suggestion = fuzzy_match_column(
                    col_name,
                    self.schema,
                    table_context=table_name,
                    max_distance=2
                )

                errors.append({
                    'category': 'SCHEMA',
                    'type': 'SC2',
                    'message': f"Column '{col_name}' does not exist",
                    'token': col_name,
                    'suggestion': suggestion,
                    'confidence': 'high' if suggestion else 'low',
                    'location': column_node
                })

            # Check for ambiguous columns (column exists in multiple tables)
            elif not table_name:
                matching_tables = self.schema.find_all_tables_for_column(col_name)
                if len(matching_tables) > 1:
                    errors.append({
                        'category': 'SCHEMA',
                        'type': 'SC4',
                        'message': f"Column '{col_name}' is ambiguous (exists in {len(matching_tables)} tables)",
                        'token': col_name,
                        'suggestion': f"Qualify with table name: {matching_tables[0]}.{col_name}",
                        'confidence': 'high',
                        'location': column_node
                    })

        return errors

    def _detect_aggregation_errors(self, ast: exp.Expression) -> List[Dict[str, Any]]:
        """
        Detect missing GROUP BY or incorrect aggregation

        Checks:
        - A1: Missing GROUP BY with aggregate functions
        - A3: HAVING clause without aggregates (should be WHERE)

        Latency: 10-20ms
        """
        errors = []

        # Check if query uses aggregate functions
        has_aggregate = any([
            list(ast.find_all(exp.Sum)),
            list(ast.find_all(exp.Count)),
            list(ast.find_all(exp.Avg)),
            list(ast.find_all(exp.Min)),
            list(ast.find_all(exp.Max))
        ])

        # Check if query has GROUP BY
        has_group_by = ast.find(exp.Group) is not None

        if has_aggregate and not has_group_by:
            # Get SELECT clause
            select = ast.find(exp.Select)
            if select:
                # Find non-aggregated columns in SELECT
                non_agg_columns = []

                for expr in select.expressions:
                    if isinstance(expr, exp.Column):
                        # Check if this column is not inside an aggregate
                        if not self._is_inside_aggregate(expr):
                            non_agg_columns.append(expr.name)

                # If there are non-aggregated columns, GROUP BY is needed
                if non_agg_columns:
                    errors.append({
                        'category': 'AGGREGATION',
                        'type': 'A1',
                        'message': 'Missing GROUP BY with aggregate function',
                        'token': None,
                        'suggestion': f"GROUP BY {', '.join(non_agg_columns)}",
                        'confidence': 'high',
                        'location': None
                    })

        # Check HAVING without aggregate in condition
        having = ast.find(exp.Having)
        if having and not self._contains_aggregate(having):
            errors.append({
                'category': 'AGGREGATION',
                'type': 'A3',
                'message': 'HAVING clause should be WHERE (no aggregates in condition)',
                'token': None,
                'suggestion': 'Move condition to WHERE clause',
                'confidence': 'high',
                'location': having
            })

        return errors

    def _detect_join_errors(self, ast: exp.Expression) -> List[Dict[str, Any]]:
        """
        Detect JOIN-related errors

        Checks:
        - J1: Multiple tables without JOIN
        - J3: JOIN without ON clause
        - J4: JOIN with invalid FK relationship

        Latency: 20-30ms
        """
        errors = []

        # Get all tables and joins
        tables = list(ast.find_all(exp.Table))
        joins = list(ast.find_all(exp.Join))

        # Check: Multiple tables without JOIN (Cartesian product)
        if len(tables) > 1 and len(joins) == 0:
            table_names = [t.name for t in tables]
            join_suggestions = self.schema.generate_join_path(table_names)

            errors.append({
                'category': 'JOIN',
                'type': 'J1',
                'message': f'Multiple tables ({len(tables)}) used without JOIN',
                'token': None,
                'suggestion': '\n'.join(join_suggestions) if join_suggestions else None,
                'confidence': 'high',
                'location': None
            })

        # Check each JOIN
        for join_node in joins:
            # Check: JOIN without ON clause
            if not join_node.on:
                # Get the joined table name
                joined_table = None
                if hasattr(join_node, 'this') and isinstance(join_node.this, exp.Table):
                    joined_table = join_node.this.name

                errors.append({
                    'category': 'JOIN',
                    'type': 'J3',
                    'message': f'JOIN missing ON clause',
                    'token': joined_table,
                    'suggestion': self._suggest_join_condition(joined_table, tables),
                    'confidence': 'high',
                    'location': join_node
                })

            # Check: JOIN with invalid FK relationship
            elif join_node.on:
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
                            errors.append({
                                'category': 'JOIN',
                                'type': 'J4',
                                'message': 'JOIN uses columns without FK relationship',
                                'token': f"{left_col} = {right_col}",
                                'suggestion': None,  # Schema-based suggestion would go here
                                'confidence': 'medium',
                                'location': join_node
                            })

        return errors

    def _detect_filter_errors(self, ast: exp.Expression) -> List[Dict[str, Any]]:
        """
        Detect WHERE clause errors

        Checks:
        - F2: Type mismatch in conditions

        Latency: 10-20ms
        """
        errors = []

        # Get WHERE clause
        where = ast.find(exp.Where)
        if not where:
            return errors

        # Check for type mismatches
        for eq_node in where.find_all(exp.EQ):
            left = eq_node.left
            right = eq_node.right

            # Check if comparing column to literal with type mismatch
            if isinstance(left, exp.Column) and isinstance(right, exp.Literal):
                column_name = left.name
                table_name = left.table if hasattr(left, 'table') else None

                # Get column type from schema
                if table_name:
                    table = self.schema.get_table(table_name)
                    if table:
                        column = table.get_column(column_name)
                        if column:
                            # Simple type check
                            if self._has_type_mismatch(column.data_type, right.this):
                                errors.append({
                                    'category': 'FILTER',
                                    'type': 'F2',
                                    'message': f"Type mismatch: column '{column_name}' ({column.data_type}) compared to '{right.this}'",
                                    'token': column_name,
                                    'suggestion': None,
                                    'confidence': 'medium',
                                    'location': eq_node
                                })

        return errors

    def _detect_structural_errors(self, ast: exp.Expression) -> List[Dict[str, Any]]:
        """
        Detect structural issues (placeholders for future enhancement)

        Checks:
        - T3: Subquery issues (placeholder)

        Latency: 5-10ms
        """
        errors = []

        # Placeholder for subquery validation
        # Can be extended based on specific requirements

        return errors

    # Helper methods

    def _is_inside_aggregate(self, node: exp.Expression) -> bool:
        """Check if a node is inside an aggregate function"""
        parent = node.parent
        while parent:
            if isinstance(parent, (exp.Sum, exp.Count, exp.Avg, exp.Min, exp.Max)):
                return True
            parent = parent.parent
        return False

    def _contains_aggregate(self, node: exp.Expression) -> bool:
        """Check if a node contains any aggregate functions"""
        return any([
            node.find(exp.Sum),
            node.find(exp.Count),
            node.find(exp.Avg),
            node.find(exp.Min),
            node.find(exp.Max)
        ])

    def _suggest_join_condition(self, joined_table: Optional[str], all_tables: List[exp.Table]) -> Optional[str]:
        """Suggest JOIN ON condition based on schema FK relationships"""
        if not joined_table or len(all_tables) == 0:
            return None

        # Try to find FK relationship with any other table
        for table_node in all_tables:
            table_name = table_node.name
            if table_name != joined_table:
                suggestion = self.schema.suggest_join_condition(table_name, joined_table)
                if suggestion:
                    return suggestion

        return None

    def _has_type_mismatch(self, column_type: str, literal_value: Any) -> bool:
        """Simple type mismatch detection"""
        column_type_lower = column_type.lower()

        # Check for obvious mismatches
        if 'int' in column_type_lower or 'number' in column_type_lower:
            # Expecting numeric value
            try:
                float(str(literal_value))
                return False
            except ValueError:
                return True

        return False
