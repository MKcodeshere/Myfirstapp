"""
Demo Script for Text-to-SQL Self-Healing System

Demonstrates the system's ability to:
1. Generate SQL from natural language
2. Detect errors automatically
3. Repair errors using hybrid approach
4. Execute corrected queries
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src import Text2SQLSelfHeal, DatabaseSchema


def main():
    """Run demo examples"""

    print("=" * 80)
    print("Text-to-SQL Self-Healing System - Demo")
    print("=" * 80)
    print()

    # Check for API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it before running the demo:")
        print("  export ANTHROPIC_API_KEY='your_api_key_here'")
        return

    # Paths
    base_dir = Path(__file__).parent.parent
    schema_path = base_dir / 'data' / 'schema.json'
    db_path = base_dir / 'data' / 'example.db'

    # Load schema
    print("Loading schema...")
    schema = DatabaseSchema.load_from_file(str(schema_path))
    print(f"Schema loaded: {len(schema.tables)} tables")
    print()

    # Initialize self-healing system
    print("Initializing self-healing system...")
    system = Text2SQLSelfHeal(
        schema=schema,
        database_path=str(db_path),
        api_key=api_key
    )
    print("System ready!")
    print()

    # Demo queries (some will have errors that need repair)
    demo_queries = [
        {
            'name': 'Query 1: Simple aggregation',
            'query': 'Show me the total contract value for each lead status in USA'
        },
        {
            'name': 'Query 2: Multiple joins',
            'query': 'List all leads from USA with their total contract values'
        },
        {
            'name': 'Query 3: Filtered aggregation',
            'query': 'What is the average contract value for qualified leads?'
        },
        {
            'name': 'Query 4: Count query',
            'query': 'How many leads do we have in each country?'
        },
        {
            'name': 'Query 5: Complex query',
            'query': 'Show me the top 3 countries by total contract value'
        }
    ]

    # Run each demo query
    for i, demo in enumerate(demo_queries, 1):
        print("=" * 80)
        print(f"{demo['name']}")
        print("=" * 80)
        print(f"Natural Language: {demo['query']}")
        print()

        # Execute query with self-healing
        result = system.query(demo['query'], verbose=True)

        # Show results
        print()
        print("-" * 80)
        if result['success']:
            print("✓ Query SUCCESSFUL")
            print()
            print("Results:")
            if result['result']:
                for row in result['result']:
                    print(f"  {row}")
            else:
                print("  (No rows returned)")
        else:
            print("✗ Query FAILED")
            print(f"Error: {result.get('error_message', 'Unknown error')}")

        print()
        print("Metadata:")
        metadata = result['metadata']
        print(f"  Path taken: {metadata.get('path_taken', 'N/A')}")
        print(f"  Total latency: {metadata.get('total_latency', 0):.2f}s")
        print(f"  Generation time: {metadata.get('generation_time', 0):.2f}s")
        print(f"  Detection time: {metadata.get('detection_time', 0):.2f}s")
        if metadata.get('repair_time'):
            print(f"  Repair time: {metadata.get('repair_time', 0):.2f}s")
        print(f"  Errors found: {len(metadata.get('errors_found', []))}")
        print(f"  Repair method: {metadata.get('repair_method', 'N/A')}")

        print()
        print(f"Final SQL:\n  {result['sql']}")
        print()

        if i < len(demo_queries):
            print()

    print()
    print("=" * 80)
    print("Demo complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
