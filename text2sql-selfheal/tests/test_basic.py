"""
Basic Test Suite for Text-to-SQL Self-Healing System

Tests core functionality of each component:
- Schema management
- Fuzzy matching
- Error detection
- Rule-based repair
- Validation
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.schema import DatabaseSchema, Table, Column
from src.utils.fuzzy_match import (
    levenshtein_distance,
    fuzzy_match,
    calculate_similarity_score
)
from src.utils.error_taxonomy import (
    get_error_category,
    is_simple_error,
    ErrorCategory
)
from src.detection.error_detector import ErrorDetector
from src.validation.validator import RepairValidator


# Test Schema Management
class TestSchema:
    """Test schema management functionality"""

    def test_create_schema(self):
        """Test creating a database schema"""
        schema = DatabaseSchema()
        schema.database_name = 'test_db'

        # Create table
        users = Table(name='users')
        users.add_column(Column(name='id', data_type='INTEGER', primary_key=True))
        users.add_column(Column(name='name', data_type='TEXT'))

        schema.add_table(users)

        assert schema.has_table('users')
        assert schema.has_column('id', 'users')
        assert schema.has_column('name', 'users')
        assert not schema.has_column('invalid', 'users')

    def test_foreign_keys(self):
        """Test foreign key relationships"""
        schema = DatabaseSchema()

        # Create leads table
        leads = Table(name='leads')
        leads.add_column(Column(name='lead_id', data_type='INTEGER', primary_key=True))
        schema.add_table(leads)

        # Create contracts table with FK
        contracts = Table(name='contracts')
        contracts.add_column(Column(name='contract_id', data_type='INTEGER', primary_key=True))
        contracts.add_column(Column(
            name='lead_id',
            data_type='INTEGER',
            foreign_key=('leads', 'lead_id')
        ))
        schema.add_table(contracts)

        # Test FK relationship
        assert schema.is_valid_foreign_key('contracts.lead_id', 'leads.lead_id')
        assert not schema.is_valid_foreign_key('contracts.contract_id', 'leads.lead_id')


# Test Fuzzy Matching
class TestFuzzyMatch:
    """Test fuzzy matching functionality"""

    def test_levenshtein_distance(self):
        """Test Levenshtein distance calculation"""
        assert levenshtein_distance("kitten", "sitting") == 3
        assert levenshtein_distance("hello", "hello") == 0
        assert levenshtein_distance("abc", "xyz") == 3

    def test_fuzzy_match(self):
        """Test fuzzy matching"""
        options = ["status", "name", "email", "country"]

        # Close match
        assert fuzzy_match("statuss", options, max_distance=2) == "status"

        # Exact match
        assert fuzzy_match("email", options, max_distance=2) == "email"

        # No match (distance too large)
        assert fuzzy_match("xyz", options, max_distance=2) is None

    def test_similarity_score(self):
        """Test similarity score calculation"""
        # Identical strings
        assert calculate_similarity_score("hello", "hello") == 1.0

        # Similar strings
        score = calculate_similarity_score("status", "statuss")
        assert 0.8 <= score <= 1.0

        # Very different strings
        score = calculate_similarity_score("abc", "xyz")
        assert score < 0.5


# Test Error Taxonomy
class TestErrorTaxonomy:
    """Test error taxonomy functionality"""

    def test_get_error_category(self):
        """Test error category classification"""
        assert get_error_category("S1") == ErrorCategory.SYNTAX
        assert get_error_category("SC2") == ErrorCategory.SCHEMA
        assert get_error_category("J1") == ErrorCategory.JOIN
        assert get_error_category("A1") == ErrorCategory.AGGREGATION
        assert get_error_category("L1") == ErrorCategory.LOGICAL

    def test_is_simple_error(self):
        """Test simple error classification"""
        # Simple errors (rule-based)
        assert is_simple_error(["SC1", "SC2", "A1"])

        # Complex errors (LLM-guided)
        assert not is_simple_error(["L1", "L2"])

        # Mixed
        assert not is_simple_error(["SC1", "L1"])


# Test Error Detection
class TestErrorDetection:
    """Test error detection functionality"""

    @pytest.fixture
    def schema(self):
        """Create test schema"""
        schema = DatabaseSchema()

        # Leads table
        leads = Table(name='leads')
        leads.add_column(Column(name='lead_id', data_type='INTEGER', primary_key=True))
        leads.add_column(Column(name='name', data_type='TEXT'))
        leads.add_column(Column(name='status', data_type='TEXT'))
        leads.add_column(Column(name='country', data_type='TEXT'))
        schema.add_table(leads)

        # Contracts table
        contracts = Table(name='contracts')
        contracts.add_column(Column(name='contract_id', data_type='INTEGER', primary_key=True))
        contracts.add_column(Column(
            name='lead_id',
            data_type='INTEGER',
            foreign_key=('leads', 'lead_id')
        ))
        contracts.add_column(Column(name='contract_value', data_type='REAL'))
        schema.add_table(contracts)

        return schema

    def test_detect_schema_error(self, schema):
        """Test detection of schema errors"""
        detector = ErrorDetector(schema)

        # Wrong table name
        sql = "SELECT * FROM lead"  # Should be 'leads'
        errors = detector.detect_errors(sql)

        assert len(errors) > 0
        assert any(e['type'] == 'SC1' for e in errors)

    def test_detect_missing_group_by(self, schema):
        """Test detection of missing GROUP BY"""
        detector = ErrorDetector(schema)

        # Aggregate without GROUP BY
        sql = "SELECT status, SUM(contract_value) FROM leads JOIN contracts ON leads.lead_id = contracts.lead_id"
        errors = detector.detect_errors(sql)

        # Should detect missing GROUP BY
        assert any(e['type'] == 'A1' for e in errors)

    def test_no_errors(self, schema):
        """Test that valid SQL has no errors"""
        detector = ErrorDetector(schema)

        # Valid SQL
        sql = "SELECT * FROM leads WHERE country = 'USA'"
        errors = detector.detect_errors(sql)

        assert len(errors) == 0


# Test Validation
class TestValidation:
    """Test validation functionality"""

    @pytest.fixture
    def schema(self):
        """Create test schema"""
        schema = DatabaseSchema()

        users = Table(name='users')
        users.add_column(Column(name='id', data_type='INTEGER', primary_key=True))
        users.add_column(Column(name='name', data_type='TEXT'))
        schema.add_table(users)

        return schema

    def test_validate_valid_repair(self, schema):
        """Test validation of a valid repair"""
        validator = RepairValidator(schema)

        original = "SELECT * FROM usrs"  # Typo
        repaired = "SELECT * FROM users"  # Fixed

        is_valid, reason = validator.validate_repair(original, repaired)

        assert is_valid
        assert "confidence" in reason.lower()

    def test_reject_invalid_repair(self, schema):
        """Test rejection of invalid repair"""
        validator = RepairValidator(schema)

        original = "SELECT * FROM users"
        repaired = "SELECT * FROM invalid_table"  # Introduces new error

        is_valid, reason = validator.validate_repair(original, repaired)

        assert not is_valid

    def test_reject_no_change(self, schema):
        """Test rejection of no actual change"""
        validator = RepairValidator(schema)

        original = "SELECT * FROM users"
        repaired = "SELECT * FROM users"  # No change

        is_valid, reason = validator.validate_repair(original, repaired)

        assert not is_valid
        assert "no actual modification" in reason.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
