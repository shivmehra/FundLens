"""Tests for unified file parser."""

import pytest
from openpyxl import Workbook

from src.parsers import parse_file


@pytest.fixture
def test_excel_file_for_parser(fixtures_dir):
    """Create a test Excel file for unified parser."""
    path = fixtures_dir / "test_parse_file.xlsx"
    
    wb = Workbook()
    ws = wb.active
    ws.append(["Fund Name", "Date", "NAV", "Category"])
    ws.append(["Vanguard 500", "2024-01-15", 150.25, "Equity"])
    ws.append(["Fidelity Growth", "2024-01-15", 85.50, "Equity"])
    
    wb.save(path)
    return path


@pytest.mark.unit
class TestUnifiedFileParser:
    """Test suite for unified parse_file function."""

    def test_parse_csv_file(self, test_csv_file):
        """Test parsing a CSV file."""
        rows = parse_file(str(test_csv_file))

        assert len(rows) == 10
        row_num, row_dict = rows[0]
        assert row_num == 1
        assert row_dict["Fund Name"] == "Vanguard 500"

    def test_parse_xlsx_file(self, test_excel_file_for_parser):
        """Test parsing an Excel file."""
        rows = parse_file(str(test_excel_file_for_parser))

        assert len(rows) == 2
        row_num, row_dict = rows[0]
        assert row_num == 1
        assert row_dict["Fund Name"] == "Vanguard 500"

    def test_parse_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            parse_file("/nonexistent/file.csv")

    def test_parse_unsupported_file_type(self, tmp_path):
        """Test error handling for unsupported file type."""
        unsupported = tmp_path / "file.txt"
        unsupported.write_text("dummy data")

        with pytest.raises(ValueError, match="Unsupported file type"):
            parse_file(str(unsupported))

    def test_parse_json_file(self, tmp_path):
        """Test error handling for .json file."""
        json_file = tmp_path / "file.json"
        json_file.write_text('{"data": "test"}')

        with pytest.raises(ValueError, match="Unsupported file type"):
            parse_file(str(json_file))

    def test_parse_csv_with_encoding(self, test_csv_utf8):
        """Test parsing UTF-8 encoded CSV file."""
        rows = parse_file(str(test_csv_utf8))

        assert len(rows) == 3
        # Check special characters are handled
        assert "Société" in rows[1][1]["Fund Name"]
