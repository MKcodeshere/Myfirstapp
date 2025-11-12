"""
Setup Example Database

Creates the Leads & Contracts database example from the technical specification.

Schema:
- leads: lead_id (PK), name, email, status, country, created_date
- contracts: contract_id (PK), lead_id (FK), contract_value, signed_date
"""

import sqlite3
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.schema import DatabaseSchema, Table, Column


def create_database(db_path: str):
    """Create and populate example database"""

    # Connect to database (creates if doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop tables if exist
    cursor.execute('DROP TABLE IF EXISTS contracts')
    cursor.execute('DROP TABLE IF EXISTS leads')

    # Create leads table
    cursor.execute('''
        CREATE TABLE leads (
            lead_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            status TEXT NOT NULL,
            country TEXT NOT NULL,
            created_date TEXT NOT NULL
        )
    ''')

    # Create contracts table
    cursor.execute('''
        CREATE TABLE contracts (
            contract_id INTEGER PRIMARY KEY,
            lead_id INTEGER NOT NULL,
            contract_value REAL NOT NULL,
            signed_date TEXT NOT NULL,
            FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
        )
    ''')

    # Insert sample data - Leads
    leads_data = [
        (1, 'John Smith', 'john@example.com', 'qualified', 'USA', '2024-01-15'),
        (2, 'Maria Garcia', 'maria@example.com', 'new', 'USA', '2024-02-20'),
        (3, 'Li Wang', 'li@example.com', 'qualified', 'China', '2024-01-10'),
        (4, 'Emma Brown', 'emma@example.com', 'negotiation', 'USA', '2024-03-05'),
        (5, 'Ahmed Hassan', 'ahmed@example.com', 'qualified', 'UAE', '2024-02-28'),
        (6, 'Sophie Martin', 'sophie@example.com', 'closed-won', 'USA', '2024-01-20'),
        (7, 'Carlos Silva', 'carlos@example.com', 'new', 'Brazil', '2024-03-10'),
        (8, 'Anna Müller', 'anna@example.com', 'qualified', 'Germany', '2024-02-15'),
        (9, 'Raj Patel', 'raj@example.com', 'closed-won', 'USA', '2024-01-25'),
        (10, 'Yuki Tanaka', 'yuki@example.com', 'negotiation', 'Japan', '2024-03-01'),
    ]

    cursor.executemany('INSERT INTO leads VALUES (?, ?, ?, ?, ?, ?)', leads_data)

    # Insert sample data - Contracts
    contracts_data = [
        (1, 1, 50000.00, '2024-02-01'),
        (2, 1, 25000.00, '2024-03-15'),
        (3, 3, 75000.00, '2024-02-20'),
        (4, 4, 30000.00, '2024-03-25'),
        (5, 6, 100000.00, '2024-02-10'),
        (6, 6, 45000.00, '2024-03-05'),
        (7, 9, 80000.00, '2024-02-15'),
    ]

    cursor.executemany('INSERT INTO contracts VALUES (?, ?, ?, ?)', contracts_data)

    # Commit and close
    conn.commit()
    conn.close()

    print(f"Database created successfully: {db_path}")
    print(f"  - 10 leads inserted")
    print(f"  - 7 contracts inserted")


def create_schema_file(schema_path: str):
    """Create schema metadata file"""

    # Build schema object
    schema = DatabaseSchema()
    schema.database_name = 'leads_contracts'

    # Leads table
    leads_table = Table(name='leads')
    leads_table.add_column(Column(
        name='lead_id',
        data_type='INTEGER',
        nullable=False,
        primary_key=True
    ))
    leads_table.add_column(Column(
        name='name',
        data_type='TEXT',
        nullable=False
    ))
    leads_table.add_column(Column(
        name='email',
        data_type='TEXT',
        nullable=False
    ))
    leads_table.add_column(Column(
        name='status',
        data_type='TEXT',
        nullable=False
    ))
    leads_table.add_column(Column(
        name='country',
        data_type='TEXT',
        nullable=False
    ))
    leads_table.add_column(Column(
        name='created_date',
        data_type='TEXT',
        nullable=False
    ))
    schema.add_table(leads_table)

    # Contracts table
    contracts_table = Table(name='contracts')
    contracts_table.add_column(Column(
        name='contract_id',
        data_type='INTEGER',
        nullable=False,
        primary_key=True
    ))
    contracts_table.add_column(Column(
        name='lead_id',
        data_type='INTEGER',
        nullable=False,
        foreign_key=('leads', 'lead_id')
    ))
    contracts_table.add_column(Column(
        name='contract_value',
        data_type='REAL',
        nullable=False
    ))
    contracts_table.add_column(Column(
        name='signed_date',
        data_type='TEXT',
        nullable=False
    ))
    schema.add_table(contracts_table)

    # Save to file
    schema.save_to_file(schema_path)

    print(f"Schema file created successfully: {schema_path}")
    print("\nSchema:")
    print(schema.format_schema_compact())


if __name__ == '__main__':
    # Create data directory if doesn't exist
    data_dir = Path(__file__).parent
    data_dir.mkdir(exist_ok=True)

    # Paths
    db_path = data_dir / 'example.db'
    schema_path = data_dir / 'schema.json'

    print("Setting up example database and schema...")
    print("=" * 60)

    # Create database
    create_database(str(db_path))
    print()

    # Create schema file
    create_schema_file(str(schema_path))
    print()

    print("=" * 60)
    print("Setup complete!")
