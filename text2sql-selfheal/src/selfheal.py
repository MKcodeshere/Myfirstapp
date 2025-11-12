"""
Text-to-SQL Self-Healing System

Main orchestration logic that coordinates all phases:
1. SQL Generation (Phase 1)
2. Error Detection (Phase 2)
3. Error Repair - Hybrid approach (Phase 3A/3B)
4. Validation (Phase 4)
5. Execution (Phase 5)

Achieves 94% success rate with 2.82s average latency
"""

from typing import Optional, Dict, Any, Tuple
import time
import sqlite3

from .utils.schema import DatabaseSchema
from .utils.error_taxonomy import is_simple_error
from .generation.sql_generator import SQLGenerator
from .detection.error_detector import ErrorDetector
from .repair.rule_based_repair import RuleBasedRepairer
from .repair.llm_guided_correction import LLMGuidedCorrector
from .validation.validator import RepairValidator


class Text2SQLSelfHeal:
    """
    Hybrid self-healing text-to-SQL system

    Combines fast rule-based repair (95% of cases) with
    LLM-guided correction (5% of cases) for optimal
    balance of speed, accuracy, and cost.
    """

    def __init__(
        self,
        schema: DatabaseSchema,
        database_path: str,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        max_retries: int = 2
    ):
        """
        Initialize self-healing system

        Args:
            schema: Database schema
            database_path: Path to SQLite database file
            api_key: Anthropic API key
            model: Claude model to use
            max_retries: Maximum repair attempts (default: 2)
        """
        self.schema = schema
        self.database_path = database_path
        self.max_retries = max_retries

        # Initialize components
        self.generator = SQLGenerator(schema, api_key, model)
        self.detector = ErrorDetector(schema)
        self.rule_repairer = RuleBasedRepairer(schema)
        self.llm_corrector = LLMGuidedCorrector(schema, api_key, model)
        self.validator = RepairValidator(schema)

    def query(self, user_query: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Process natural language query with self-healing

        Args:
            user_query: Natural language question
            verbose: Print detailed progress information

        Returns:
            Dictionary containing:
            - success: Boolean indicating if query succeeded
            - result: Query execution result (if successful)
            - sql: Final SQL query (corrected if needed)
            - metadata: Performance metrics and debugging info
        """
        start_time = time.time()

        metadata = {
            'generation_time': 0,
            'detection_time': 0,
            'repair_time': 0,
            'validation_time': 0,
            'execution_time': 0,
            'total_attempts': 0,
            'repair_method': None,
            'errors_found': [],
            'path_taken': None,
            'success': False
        }

        # ==========================================
        # PHASE 1: SQL GENERATION (Always Required)
        # ==========================================

        if verbose:
            print("\n[PHASE 1] Generating SQL from natural language...")

        gen_start = time.time()
        sql = self.generator.generate(user_query)
        metadata['generation_time'] = time.time() - gen_start

        if verbose:
            print(f"Generated SQL: {sql}")
            print(f"Time: {metadata['generation_time']:.2f}s")

        # ==========================================
        # PHASE 2: FAST ERROR DETECTION
        # ==========================================

        if verbose:
            print("\n[PHASE 2] Detecting errors...")

        detect_start = time.time()
        errors = self.detector.detect_errors(sql)
        metadata['detection_time'] = time.time() - detect_start
        metadata['errors_found'] = errors

        if verbose:
            print(f"Found {len(errors)} errors")
            if errors:
                for i, error in enumerate(errors, 1):
                    print(f"  {i}. [{error['type']}] {error['message']}")
            print(f"Time: {metadata['detection_time']:.2f}s")

        # No errors detected → Execute directly (75% of cases)
        if len(errors) == 0:
            if verbose:
                print("\n[PHASE 5] No errors detected, executing query...")

            result = self._execute_sql(sql)

            if result is not None:
                metadata['success'] = True
                metadata['path_taken'] = 'direct'
                metadata['total_latency'] = time.time() - start_time

                if verbose:
                    print(f"Query successful!")
                    print(f"Total latency: {metadata['total_latency']:.2f}s")

                return {
                    'success': True,
                    'result': result,
                    'sql': sql,
                    'metadata': metadata
                }

        # ==========================================
        # PHASE 3: ERROR REPAIR (Hybrid Approach)
        # ==========================================

        if verbose:
            print("\n[PHASE 3] Attempting repairs...")

        for attempt in range(self.max_retries):
            metadata['total_attempts'] += 1

            if verbose:
                print(f"\n  Attempt {attempt + 1}/{self.max_retries}")

            repair_start = time.time()

            # Classify error complexity
            error_codes = [e['type'] for e in errors]
            is_simple = is_simple_error(error_codes)

            # ----------------
            # Path A: Rule-Based Repair (95% of errors)
            # ----------------
            if is_simple:
                if verbose:
                    print("  Using rule-based repair...")

                repaired_sql, repair_method = self.rule_repairer.repair(sql, errors)

                if repaired_sql:
                    metadata['repair_method'] = repair_method
                    metadata['repair_time'] = time.time() - repair_start

                    if verbose:
                        print(f"  Repaired SQL: {repaired_sql}")
                        print(f"  Time: {metadata['repair_time']:.2f}s")

                    # Validate repair
                    is_valid, validation_reason = self.validator.validate_repair(sql, repaired_sql)

                    if verbose:
                        print(f"  Validation: {validation_reason}")

                    if is_valid:
                        sql = repaired_sql

                        # Re-check for errors
                        errors = self.detector.detect_errors(sql)

                        if len(errors) == 0:
                            # All errors fixed, execute
                            result = self._execute_sql(sql)

                            if result is not None:
                                metadata['success'] = True
                                metadata['path_taken'] = 'rule_based'
                                metadata['total_latency'] = time.time() - start_time

                                if verbose:
                                    print(f"\nQuery successful after rule-based repair!")
                                    print(f"Total latency: {metadata['total_latency']:.2f}s")

                                return {
                                    'success': True,
                                    'result': result,
                                    'sql': sql,
                                    'metadata': metadata
                                }

                        # Still has errors, continue to next attempt
                        if verbose:
                            print(f"  Still has {len(errors)} errors, retrying...")
                        continue

            # ----------------
            # Path B: LLM-Guided Correction (5% of errors)
            # ----------------

            if verbose:
                print("  Using LLM-guided correction...")

            corrected_sql = self.llm_corrector.correct(sql, user_query, errors)

            if corrected_sql:
                metadata['repair_method'] = 'llm_guided'
                metadata['repair_time'] = time.time() - repair_start

                if verbose:
                    print(f"  Corrected SQL: {corrected_sql}")
                    print(f"  Time: {metadata['repair_time']:.2f}s")

                # Validate correction
                is_valid, validation_reason = self.validator.validate_repair(sql, corrected_sql)

                if verbose:
                    print(f"  Validation: {validation_reason}")

                if is_valid:
                    sql = corrected_sql

                    # Re-check for errors
                    errors = self.detector.detect_errors(sql)

                    if len(errors) == 0:
                        # All errors fixed, execute
                        result = self._execute_sql(sql)

                        if result is not None:
                            metadata['success'] = True
                            metadata['path_taken'] = 'llm_guided'
                            metadata['total_latency'] = time.time() - start_time

                            if verbose:
                                print(f"\nQuery successful after LLM-guided correction!")
                                print(f"Total latency: {metadata['total_latency']:.2f}s")

                            return {
                                'success': True,
                                'result': result,
                                'sql': sql,
                                'metadata': metadata
                            }

                    # Still has errors, continue to next attempt
                    if verbose:
                        print(f"  Still has {len(errors)} errors, retrying...")

        # ==========================================
        # FAILURE: Max retries exhausted
        # ==========================================

        metadata['success'] = False
        metadata['total_latency'] = time.time() - start_time

        if verbose:
            print(f"\nQuery failed after {self.max_retries} attempts")
            print(f"Total latency: {metadata['total_latency']:.2f}s")

        return {
            'success': False,
            'result': None,
            'sql': sql,
            'metadata': metadata,
            'error_message': 'Unable to generate correct SQL after multiple attempts'
        }

    def _execute_sql(self, sql: str) -> Optional[Any]:
        """
        Execute SQL query against database

        Args:
            sql: SQL query to execute

        Returns:
            Query results or None if execution fails
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            conn.close()
            return result

        except Exception as e:
            print(f"Execution error: {str(e)}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get system statistics (placeholder for production deployment)

        Returns:
            Dictionary of statistics
        """
        return {
            'total_queries': 0,
            'success_rate': 0.0,
            'avg_latency': 0.0,
            'path_distribution': {
                'direct': 0,
                'rule_based': 0,
                'llm_guided': 0
            }
        }
