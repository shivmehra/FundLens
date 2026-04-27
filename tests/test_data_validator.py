"""Tests for data validator."""

import pytest

from src.validators.data_validator import DataValidator


@pytest.mark.unit
class TestDataValidator:
    """Test suite for DataValidator."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return DataValidator()

    def test_validate_valid_row(self, validator):
        """Test validating a valid row."""
        row = {
            "Fund Name": "Vanguard 500",
            "Date": "2024-01-15",
            "NAV": "150.25",
            "Category": "Equity",
            "Manager": "Vanguard",
        }

        validated, error = validator.validate_row(row, 1)

        assert error is None
        assert validated is not None
        assert validated.fund_name == "Vanguard 500"
        assert str(validated.date) == "2024-01-15"

    def test_validate_partial_row(self, validator):
        """Test validating a row with missing optional fields."""
        row = {
            "Fund Name": "Vanguard 500",
            "Date": "2024-01-15",
            "NAV": "150.25",
            "Category": "Equity",
        }

        validated, error = validator.validate_row(row, 1)

        assert error is None
        assert validated is not None
        assert validated.inception_date is None
        assert validated.manager is None

    def test_validate_missing_required_field(self, validator):
        """Test error when required field is missing."""
        row = {
            "Fund Name": "Vanguard 500",
            "Date": "2024-01-15",
            # NAV missing
            "Category": "Equity",
        }

        validated, error = validator.validate_row(row, 1)

        assert error is not None
        assert validated is None
        assert error.row_number == 1

    def test_validate_negative_nav(self, validator):
        """Test error when NAV is negative."""
        row = {
            "Fund Name": "Vanguard 500",
            "Date": "2024-01-15",
            "NAV": "-150.25",
            "Category": "Equity",
        }

        validated, error = validator.validate_row(row, 1)

        assert error is not None
        assert validated is None
        assert ("positive" in error.error_message.lower() or "greater than 0" in error.error_message.lower())

    def test_validate_bad_date_format(self, validator):
        """Test error when date format is invalid."""
        row = {
            "Fund Name": "Vanguard 500",
            "Date": "01/15/2024",  # Wrong format
            "NAV": "150.25",
            "Category": "Equity",
        }

        validated, error = validator.validate_row(row, 1)

        assert error is not None
        assert validated is None

    def test_validate_empty_fund_name(self, validator):
        """Test error when fund name is empty."""
        row = {
            "Fund Name": "",
            "Date": "2024-01-15",
            "NAV": "150.25",
            "Category": "Equity",
        }

        validated, error = validator.validate_row(row, 1)

        assert error is not None
        assert validated is None

    def test_validate_batch(self, validator):
        """Test batch validation."""
        rows = [
            (1, {"Fund Name": "Vanguard 500", "Date": "2024-01-15", "NAV": "150.25", "Category": "Equity"}),
            (2, {"Fund Name": "Fidelity Growth", "Date": "2024-01-15", "NAV": "85.50", "Category": "Equity"}),
            (3, {"Fund Name": "", "Date": "2024-01-15", "NAV": "45.75", "Category": "Debt"}),
        ]

        valid, errors = validator.validate_batch(rows)

        assert len(valid) == 2
        assert len(errors) == 1
        assert errors[0].row_number == 3

    def test_validate_field_mapping(self, validator):
        """Test field mapping from CSV column names."""
        # Use different column name for same field
        row = {
            "Name": "Vanguard 500",  # Maps to fund_name
            "Date": "2024-01-15",
            "NAV": "150.25",
            "Type": "Equity",  # Maps to category
        }

        validated, error = validator.validate_row(row, 1)

        assert error is None
        assert validated is not None
        assert validated.fund_name == "Vanguard 500"
        assert validated.category == "Equity"
