"""File parsers module."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .csv_parser import CSVParser
from .excel_parser import ExcelParser

logger = logging.getLogger(__name__)


def parse_file(file_path: str) -> List[Tuple[int, Dict[str, Any]]]:
    """
    Parse a file and return list of (row_number, row_dict) tuples.

    Supports .csv and .xlsx files. Row numbers are 1-based.

    Args:
        file_path: Path to CSV or Excel file

    Returns:
        List of (row_number, row_dict) tuples

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file type unsupported or parsing fails
    """
    path = Path(file_path)

    if not path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    # Detect file type from extension
    suffix = path.suffix.lower()

    if suffix == ".csv":
        logger.info(f"Parsing CSV file: {file_path}")
        parser = CSVParser()
        return parser.extract_rows_with_line_numbers(file_path)

    elif suffix in [".xlsx", ".xls"]:
        logger.info(f"Parsing Excel file: {file_path}")
        parser = ExcelParser()
        return parser.extract_rows_with_line_numbers(file_path)

    else:
        logger.error(f"Unsupported file type: {suffix}")
        raise ValueError(f"Unsupported file type '{suffix}'. Supported: .csv, .xlsx, .xls")


__all__ = ["parse_file", "CSVParser", "ExcelParser"]

