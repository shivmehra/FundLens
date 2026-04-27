"""Tests for CSV parser."""

import pytest

from src.parsers.csv_parser import CSVParser


@pytest.mark.unit
class TestCSVParser:
    """Test suite for CSVParser."""

    def test_parse_valid_csv(self, test_csv_file):
        """Test parsing a valid CSV file."""
        parser = CSVParser()
        rows = parser.parse(str(test_csv_file))

        assert len(rows) == 10
        assert rows[0]["Fund Name"] == "Vanguard 500"
        assert rows[0]["Date"] == "2024-01-15"
        assert rows[0]["NAV"] == 150.25

    def test_extract_rows_with_line_numbers(self, test_csv_file):
        """Test extracting rows with line numbers."""
        parser = CSVParser()
        rows = parser.extract_rows_with_line_numbers(str(test_csv_file))

        assert len(rows) == 10
        # First element is (row_number, row_dict)
        row_num, row_dict = rows[0]
        assert row_num == 1
        assert row_dict["Fund Name"] == "Vanguard 500"

        # Check last row number
        last_row_num, _ = rows[-1]
        assert last_row_num == 10

    def test_parse_partial_csv(self, test_csv_partial):
        """Test parsing CSV with missing optional columns."""
        parser = CSVParser()
        rows = parser.parse(str(test_csv_partial))

        assert len(rows) == 10
        # Check that optional columns are not in the dict or are NaN
        assert "Manager" not in rows[0] or rows[0]["Manager"] != rows[0]["Manager"]  # NaN check

    def test_parse_with_duplicates(self, test_csv_duplicates):
        """Test parsing CSV with duplicate rows."""
        parser = CSVParser()
        rows = parser.parse(str(test_csv_duplicates))

        assert len(rows) == 10

    def test_parse_empty_csv(self, test_csv_empty):
        """Test parsing empty CSV (header only)."""
        parser = CSVParser()
        rows = parser.parse(str(test_csv_empty))

        # Empty CSV has no rows
        assert len(rows) == 0

    def test_parse_file_not_found(self):
        """Test error handling for missing file."""
        parser = CSVParser()

        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/file.csv")

    def test_parse_utf8_encoding(self, test_csv_utf8):
        """Test parsing UTF-8 encoded CSV."""
        parser = CSVParser()
        rows = parser.parse(str(test_csv_utf8))

        assert len(rows) == 3
        # Should handle special characters in "Société Générale"
        assert rows[1]["Fund Name"] == "Société Générale"

    def test_validate_structure_valid(self, test_csv_file):
        """Test CSV structure validation."""
        parser = CSVParser()
        result = parser.validate_structure(str(test_csv_file), required_columns=["Fund Name", "Date", "NAV"])

        assert result is True

    def test_validate_structure_missing_columns(self, test_csv_file):
        """Test CSV structure validation with missing required columns."""
        parser = CSVParser()

        with pytest.raises(ValueError, match="missing required columns"):
            parser.validate_structure(str(test_csv_file), required_columns=["NonExistent"])
