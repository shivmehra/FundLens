"""Tests for Excel parser."""

import pytest
from openpyxl import Workbook

from src.parsers.excel_parser import ExcelParser


@pytest.fixture
def test_excel_file(fixtures_dir):
    """Create a test Excel file."""
    path = fixtures_dir / "valid_complete.xlsx"
    
    # Create workbook with test data
    wb = Workbook()
    ws = wb.active
    ws.title = "Funds"
    
    # Add headers
    headers = ["Fund Name", "Date", "NAV", "Category", "Inception Date", "Manager"]
    ws.append(headers)
    
    # Add data rows
    data = [
        ["Vanguard 500", "2024-01-15", 150.25, "Equity", "2020-01-01", "Vanguard"],
        ["Fidelity Growth", "2024-01-15", 85.50, "Equity", "2018-06-15", "Fidelity"],
        ["PIMCO Total Bond", "2024-01-15", 45.75, "Debt", "2015-03-20", "PIMCO"],
    ]
    
    for row in data:
        ws.append(row)
    
    wb.save(path)
    return path


@pytest.mark.unit
class TestExcelParser:
    """Test suite for ExcelParser."""

    def test_parse_valid_xlsx(self, test_excel_file):
        """Test parsing a valid Excel file."""
        parser = ExcelParser()
        rows = parser.parse(str(test_excel_file))

        assert len(rows) == 3
        assert rows[0]["Fund Name"] == "Vanguard 500"
        assert rows[0]["NAV"] == 150.25

    def test_extract_rows_with_line_numbers(self, test_excel_file):
        """Test extracting rows with line numbers."""
        parser = ExcelParser()
        rows = parser.extract_rows_with_line_numbers(str(test_excel_file))

        assert len(rows) == 3
        row_num, row_dict = rows[0]
        assert row_num == 1
        assert row_dict["Fund Name"] == "Vanguard 500"

    def test_list_sheets(self, test_excel_file):
        """Test listing sheets in Excel file."""
        parser = ExcelParser()
        sheets = parser.list_sheets(str(test_excel_file))

        assert "Funds" in sheets

    def test_parse_file_not_found(self):
        """Test error handling for missing file."""
        parser = ExcelParser()

        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/file.xlsx")

    def test_validate_structure_valid(self, test_excel_file):
        """Test Excel structure validation."""
        parser = ExcelParser()
        result = parser.validate_structure(str(test_excel_file), required_columns=["Fund Name", "Date", "NAV"])

        assert result is True

    def test_validate_structure_missing_columns(self, test_excel_file):
        """Test Excel structure validation with missing columns."""
        parser = ExcelParser()

        with pytest.raises(ValueError, match="missing required columns"):
            parser.validate_structure(str(test_excel_file), required_columns=["NonExistent"])
