"""
LLM-Guided Correction Module (Phase 3B)

Handles complex logical errors requiring semantic understanding:
- Two-agent system: Diagnostic + Correction
- Chain-of-Thought reasoning
- Error taxonomy integration

Handles 5% of errors with 3-4 second latency
"""

from typing import List, Dict, Optional, Any
import json
from anthropic import Anthropic

from ..utils.schema import DatabaseSchema
from ..utils.error_taxonomy import format_compact_taxonomy, ERROR_TAXONOMY


class LLMGuidedCorrector:
    """
    LLM-guided SQL corrector

    Uses two-agent system with Chain-of-Thought reasoning:
    1. Diagnostic Agent: Analyzes errors and creates correction plan
    2. Correction Agent: Generates corrected SQL following the plan
    """

    def __init__(self, schema: DatabaseSchema, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize LLM-guided corrector

        Args:
            schema: Database schema
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.schema = schema
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def correct(
        self,
        sql: str,
        user_query: str,
        errors: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Correct SQL using LLM-guided approach

        Args:
            sql: Failed SQL query
            user_query: Original natural language question
            errors: Detected errors (may be empty for logical errors)

        Returns:
            Corrected SQL or None if correction fails
        """
        # Agent 1: Diagnostic Agent
        diagnostic_plan = self._diagnostic_agent(sql, user_query, errors)

        if not diagnostic_plan:
            return None

        # Agent 2: Correction Agent
        corrected_sql = self._correction_agent(sql, user_query, diagnostic_plan)

        return corrected_sql

    def _diagnostic_agent(
        self,
        sql: str,
        user_query: str,
        errors: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Diagnostic Agent: Analyze errors with Chain-of-Thought

        Purpose:
        - Understand user intent
        - Identify semantic/logical errors
        - Generate structured correction plan

        Returns:
            Dictionary with:
            - error_codes: List of error codes
            - diagnosis: Chain-of-Thought explanation
            - correction_strategy: List of correction steps
            - expected_outcome: What query should return
        """
        # Format detected errors
        errors_str = self._format_detected_errors(errors) if errors else "No errors detected by automated system"

        # Build diagnostic prompt
        prompt = f"""You are a SQL diagnostic expert using Chain-of-Thought reasoning.

USER QUERY (Natural Language):
{user_query}

DATABASE SCHEMA:
{self.schema.format_schema_compact()}

GENERATED SQL (FAILED):
{sql}

DETECTED ERRORS (if any):
{errors_str}

ERROR TAXONOMY (29 types, 7 categories):
{format_compact_taxonomy()}

TASK: Provide step-by-step diagnostic analysis.

Think through:
1. What does the user want to achieve?
2. What tables/columns should be involved?
3. What does the current SQL actually do?
4. What errors are present (use taxonomy codes)?
5. Why did these errors occur?
6. How to fix them step-by-step?

OUTPUT FORMAT (JSON only, no other text):
{{
    "error_codes": ["SC2", "L1", ...],
    "diagnosis": "Chain-of-Thought explanation of root causes",
    "correction_strategy": [
        "Step 1: ...",
        "Step 2: ...",
        "Step 3: ..."
    ],
    "expected_outcome": "What corrected query should return"
}}

Diagnostic Analysis:"""

        try:
            # Call LLM
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract text from response
            response_text = response.content[0].text

            # Parse JSON response
            try:
                diagnostic_plan = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                if '```json' in response_text:
                    json_str = response_text.split('```json')[1].split('```')[0].strip()
                    diagnostic_plan = json.loads(json_str)
                elif '```' in response_text:
                    json_str = response_text.split('```')[1].split('```')[0].strip()
                    diagnostic_plan = json.loads(json_str)
                else:
                    # Fallback: create basic plan
                    diagnostic_plan = {
                        'error_codes': [],
                        'diagnosis': response_text,
                        'correction_strategy': ['Fix errors based on diagnostic analysis'],
                        'expected_outcome': 'Corrected SQL query'
                    }

            return diagnostic_plan

        except Exception as e:
            print(f"Diagnostic agent error: {str(e)}")
            return None

    def _correction_agent(
        self,
        sql: str,
        user_query: str,
        diagnostic_plan: Dict[str, Any]
    ) -> Optional[str]:
        """
        Correction Agent: Generate corrected SQL following plan

        Purpose:
        - Follow diagnostic plan exactly
        - Generate corrected SQL
        - Avoid repeating same errors

        Returns:
            Corrected SQL string or None
        """
        # Build correction prompt with explicit guidance
        prompt = f"""You are a SQL correction expert.

USER QUERY (Natural Language):
{user_query}

DATABASE SCHEMA:
{self.schema.format_schema_compact()}

FAILED SQL:
{sql}

DIAGNOSTIC ANALYSIS:
Error Codes: {', '.join(diagnostic_plan.get('error_codes', []))}

Root Cause Diagnosis:
{diagnostic_plan.get('diagnosis', 'See correction strategy')}

CORRECTION STRATEGY (FOLLOW EXACTLY):
{self._format_correction_steps(diagnostic_plan.get('correction_strategy', []))}

Expected Outcome:
{diagnostic_plan.get('expected_outcome', 'Correct SQL query')}

CRITICAL INSTRUCTIONS:
1. Implement each correction step precisely
2. Output ONLY valid SQL (no explanations, no markdown, no code blocks)
3. Use only tables/columns from schema
4. Do NOT repeat the same errors
5. Ensure query answers the user's question

Corrected SQL:"""

        try:
            # Call LLM
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract text from response
            corrected_sql = response.content[0].text

            # Clean output (remove markdown, comments, etc.)
            corrected_sql = self._clean_sql_output(corrected_sql)

            return corrected_sql

        except Exception as e:
            print(f"Correction agent error: {str(e)}")
            return None

    # Helper methods

    def _format_detected_errors(self, errors: List[Dict[str, Any]]) -> str:
        """Format detected errors for LLM context"""
        if not errors:
            return "None"

        lines = []
        for i, error in enumerate(errors, 1):
            lines.append(f"{i}. [{error['type']}] {error['message']}")
            if error.get('suggestion'):
                lines.append(f"   Suggestion: {error['suggestion']}")

        return '\n'.join(lines)

    def _format_correction_steps(self, steps: List[str]) -> str:
        """Format correction steps for LLM context"""
        if not steps:
            return "No specific steps provided"

        return '\n'.join(f"{i}. {step}" for i, step in enumerate(steps, 1))

    def _clean_sql_output(self, sql: str) -> str:
        """
        Remove markdown, comments, and extra whitespace from SQL

        Args:
            sql: Raw SQL output from LLM

        Returns:
            Cleaned SQL string
        """
        import re

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
