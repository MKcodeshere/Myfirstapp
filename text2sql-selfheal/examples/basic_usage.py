"""
Basic Usage Example

Simple example showing how to use the Text-to-SQL Self-Healing System
"""

import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src import Text2SQLSelfHeal, DatabaseSchema


# Paths
base_dir = Path(__file__).parent.parent
schema_path = base_dir / 'data' / 'schema.json'
db_path = base_dir / 'data' / 'example.db'

# Load schema
schema = DatabaseSchema.load_from_file(str(schema_path))

# Initialize system
system = Text2SQLSelfHeal(
    schema=schema,
    database_path=str(db_path),
    api_key=os.getenv('ANTHROPIC_API_KEY', 'your_api_key_here')
)

# Query the database in natural language
result = system.query(
    "Show me the total contract value for each lead status in USA",
    verbose=False  # Set to True for detailed output
)

# Check result
if result['success']:
    print("Query successful!")
    print(f"SQL: {result['sql']}")
    print(f"Results: {result['result']}")
    print(f"Latency: {result['metadata']['total_latency']:.2f}s")
else:
    print("Query failed")
    print(f"Error: {result.get('error_message')}")
