"""
Database Schema Management Module

Handles schema metadata, foreign key relationships,
and schema-based suggestions for SQL generation and repair.
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
import json


@dataclass
class Column:
    """Represents a database column"""
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[Tuple[str, str]] = None  # (table, column)


@dataclass
class Table:
    """Represents a database table"""
    name: str
    columns: Dict[str, Column] = field(default_factory=dict)

    def add_column(self, column: Column):
        """Add a column to the table"""
        self.columns[column.name] = column

    def has_column(self, column_name: str) -> bool:
        """Check if table has a column"""
        return column_name.lower() in {col.lower() for col in self.columns.keys()}

    def get_column(self, column_name: str) -> Optional[Column]:
        """Get a column by name (case-insensitive)"""
        for col_name, col in self.columns.items():
            if col_name.lower() == column_name.lower():
                return col
        return None

    def get_primary_keys(self) -> List[str]:
        """Get list of primary key column names"""
        return [col.name for col in self.columns.values() if col.primary_key]

    def get_foreign_keys(self) -> Dict[str, Tuple[str, str]]:
        """Get dictionary of foreign keys {column: (ref_table, ref_column)}"""
        return {
            col.name: col.foreign_key
            for col in self.columns.values()
            if col.foreign_key
        }


class DatabaseSchema:
    """
    Database schema manager

    Provides:
    - Schema metadata storage
    - Column/table validation
    - Foreign key relationship queries
    - Schema-based suggestions for JOIN generation
    """

    def __init__(self):
        self.tables: Dict[str, Table] = {}
        self.database_name: str = ""

    def add_table(self, table: Table):
        """Add a table to the schema"""
        self.tables[table.name] = table

    def has_table(self, table_name: str) -> bool:
        """Check if table exists (case-insensitive)"""
        return table_name.lower() in {tbl.lower() for tbl in self.tables.keys()}

    def get_table(self, table_name: str) -> Optional[Table]:
        """Get a table by name (case-insensitive)"""
        for tbl_name, tbl in self.tables.items():
            if tbl_name.lower() == table_name.lower():
                return tbl
        return None

    def has_column(self, column_name: str, table_name: Optional[str] = None) -> bool:
        """
        Check if column exists in schema

        Args:
            column_name: Column name to check
            table_name: Optional table name to narrow search

        Returns:
            True if column exists
        """
        if table_name:
            table = self.get_table(table_name)
            return table.has_column(column_name) if table else False

        # Check all tables
        for table in self.tables.values():
            if table.has_column(column_name):
                return True
        return False

    def find_table_for_column(self, column_name: str) -> Optional[str]:
        """
        Find which table contains a column

        Args:
            column_name: Column name to search for

        Returns:
            Table name or None if not found or ambiguous
        """
        matching_tables = []

        for table_name, table in self.tables.items():
            if table.has_column(column_name):
                matching_tables.append(table_name)

        # Return only if unambiguous
        if len(matching_tables) == 1:
            return matching_tables[0]

        return None

    def find_all_tables_for_column(self, column_name: str) -> List[str]:
        """
        Find all tables that contain a column

        Args:
            column_name: Column name to search for

        Returns:
            List of table names
        """
        matching_tables = []

        for table_name, table in self.tables.items():
            if table.has_column(column_name):
                matching_tables.append(table_name)

        return matching_tables

    def is_valid_foreign_key(self, left_col: str, right_col: str) -> bool:
        """
        Check if two columns form a valid foreign key relationship

        Args:
            left_col: Left column in format "table.column"
            right_col: Right column in format "table.column"

        Returns:
            True if valid FK relationship exists
        """
        # Parse column references
        left_parts = left_col.split('.')
        right_parts = right_col.split('.')

        if len(left_parts) != 2 or len(right_parts) != 2:
            return False

        left_table, left_column = left_parts
        right_table, right_column = right_parts

        # Get tables
        left_tbl = self.get_table(left_table)
        right_tbl = self.get_table(right_table)

        if not left_tbl or not right_tbl:
            return False

        # Check if either side has FK to the other
        left_fks = left_tbl.get_foreign_keys()
        right_fks = right_tbl.get_foreign_keys()

        # Check left -> right FK
        if left_column in left_fks:
            ref_table, ref_column = left_fks[left_column]
            if ref_table.lower() == right_table.lower() and ref_column.lower() == right_column.lower():
                return True

        # Check right -> left FK
        if right_column in right_fks:
            ref_table, ref_column = right_fks[right_column]
            if ref_table.lower() == left_table.lower() and ref_column.lower() == left_column.lower():
                return True

        return False

    def get_foreign_key_between_tables(self, table1: str, table2: str) -> Optional[Tuple[str, str]]:
        """
        Get the foreign key relationship between two tables

        Args:
            table1: First table name
            table2: Second table name

        Returns:
            Tuple of (column1, column2) or None
        """
        tbl1 = self.get_table(table1)
        tbl2 = self.get_table(table2)

        if not tbl1 or not tbl2:
            return None

        # Check if table1 has FK to table2
        for col_name, (ref_table, ref_col) in tbl1.get_foreign_keys().items():
            if ref_table.lower() == table2.lower():
                return (f"{table1}.{col_name}", f"{table2}.{ref_col}")

        # Check if table2 has FK to table1
        for col_name, (ref_table, ref_col) in tbl2.get_foreign_keys().items():
            if ref_table.lower() == table1.lower():
                return (f"{table2}.{col_name}", f"{table1}.{ref_col}")

        return None

    def suggest_join_condition(self, table1: str, table2: str) -> Optional[str]:
        """
        Suggest JOIN ON condition for two tables

        Args:
            table1: First table name
            table2: Second table name

        Returns:
            JOIN ON condition string or None
        """
        fk = self.get_foreign_key_between_tables(table1, table2)
        if fk:
            return f"{fk[0]} = {fk[1]}"
        return None

    def generate_join_path(self, tables: List[str]) -> List[str]:
        """
        Generate JOIN clauses to connect multiple tables

        Uses breadth-first search to find shortest path through FK relationships

        Args:
            tables: List of table names to join

        Returns:
            List of JOIN clause strings
        """
        if len(tables) <= 1:
            return []

        joins = []
        connected = {tables[0]}
        remaining = set(tables[1:])

        while remaining:
            found = False

            for connected_table in list(connected):
                for remaining_table in list(remaining):
                    join_condition = self.suggest_join_condition(connected_table, remaining_table)

                    if join_condition:
                        joins.append(f"JOIN {remaining_table} ON {join_condition}")
                        connected.add(remaining_table)
                        remaining.remove(remaining_table)
                        found = True
                        break

                if found:
                    break

            if not found:
                # No direct FK path found, break to avoid infinite loop
                break

        return joins

    def format_schema_compact(self) -> str:
        """
        Format schema for LLM context (compact representation)

        Returns:
            Formatted schema string
        """
        lines = []

        for table_name, table in self.tables.items():
            cols = []
            for col_name, col in table.columns.items():
                col_str = f"{col_name} ({col.data_type})"
                if col.primary_key:
                    col_str += " PK"
                if col.foreign_key:
                    ref_table, ref_col = col.foreign_key
                    col_str += f" FK->{ref_table}.{ref_col}"
                cols.append(col_str)

            lines.append(f"{table_name}: {', '.join(cols)}")

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Convert schema to dictionary for serialization"""
        return {
            'database_name': self.database_name,
            'tables': {
                table_name: {
                    'columns': {
                        col_name: {
                            'name': col.name,
                            'data_type': col.data_type,
                            'nullable': col.nullable,
                            'primary_key': col.primary_key,
                            'foreign_key': col.foreign_key
                        }
                        for col_name, col in table.columns.items()
                    }
                }
                for table_name, table in self.tables.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'DatabaseSchema':
        """Create schema from dictionary"""
        schema = cls()
        schema.database_name = data.get('database_name', '')

        for table_name, table_data in data.get('tables', {}).items():
            table = Table(name=table_name)

            for col_name, col_data in table_data.get('columns', {}).items():
                column = Column(
                    name=col_data['name'],
                    data_type=col_data['data_type'],
                    nullable=col_data.get('nullable', True),
                    primary_key=col_data.get('primary_key', False),
                    foreign_key=tuple(col_data['foreign_key']) if col_data.get('foreign_key') else None
                )
                table.add_column(column)

            schema.add_table(table)

        return schema

    def save_to_file(self, filepath: str):
        """Save schema to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'DatabaseSchema':
        """Load schema from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
