"""
SQL Generation Module (Phase 1)

Generates SQL from natural language using LLM.

Latency: 2-3 seconds (always required)
"""

from typing import Optional
import re
from anthropic import Anthropic

from ..utils.schema import DatabaseSchema


class SQLGenerator:
    """
    SQL generator using LLM

    Converts natural language queries to SQL using Claude.
    """

    def __init__(self, schema: DatabaseSchema, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize SQL generator

        Args:
            schema: Database schema
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.schema = schema
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate(self, user_query: str) -> str:
        """
        Generate SQL from natural language query

        Args:
            user_query: Natural language question

        Returns:
            Generated SQL query string

        Latency: 2-3 seconds (LLM call)
        """
        # Build prompt with schema context
        prompt = self._build_prompt(user_query)

        # Call LLM
        sql_query = self._call_llm(prompt)

        # Clean output (remove markdown, etc.)
        sql_query = self._clean_sql_output(sql_query)

        return sql_query

    def _build_prompt(self, user_query: str) -> str:
        """
        Build prompt for SQL generation

        Args:
            user_query: Natural language question

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a SQL expert. Generate a SQL query to answer the user's question.

DATABASE SCHEMA:
{self.schema.format_schema_compact()}

USER QUESTION:
{user_query}

INSTRUCTIONS:
1. Generate ONLY the SQL query (no explanations)
2. Use SQLite syntax
3. Use only tables and columns from the schema
4. Ensure the query is syntactically correct
5. Follow SQL best practices

SQL Query:"""

        return prompt

    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM API to generate SQL

        Args:
            prompt: Formatted prompt

        Returns:
            SQL query from LLM
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0,  # Deterministic output
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract text from response
            sql_query = response.content[0].text

            return sql_query

        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {str(e)}")

    def _clean_sql_output(self, sql: str) -> str:
        """
        Clean SQL output from LLM

        Removes markdown code blocks, comments, and extra whitespace

        Args:
            sql: Raw SQL from LLM

        Returns:
            Cleaned SQL string
        """
        # Remove markdown code blocks
        sql = re.sub(r'```sql\n?', '', sql)
        sql = re.sub(r'```\n?', '', sql)

        # Remove SQL comments
        sql = re.sub(r'--[^\n]*\n', '', sql)

        # Remove multi-line comments
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)

        # Remove extra whitespace
        sql = ' '.join(sql.split())

        return sql.strip()
