"""CSV file parser for fund data ingestion."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class CSVParser:
    """Parse CSV files and extract fund data rows."""

    def __init__(self, encoding: str = None):
        """
        Initialize CSV parser.

        Args:
            encoding: Optional encoding override (default: auto-detect)
        """
        self.encoding = encoding

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse CSV file and return list of row dictionaries.

        Args:
            file_path: Path to CSV file

        Returns:
            List of dictionaries, one per row (header names as keys)

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed (encoding, format errors)
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"CSV file not found: {file_path}")
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        try:
            # Try specified encoding first, or auto-detect
            if self.encoding:
                df = pd.read_csv(file_path, encoding=self.encoding)
                logger.debug(f"Parsed CSV with encoding {self.encoding}: {file_path}")
            else:
                # Try UTF-8 first, fallback to ISO-8859-1/Latin-1
                try:
                    df = pd.read_csv(file_path, encoding="utf-8")
                    logger.debug(f"Parsed CSV with UTF-8 encoding: {file_path}")
                except (UnicodeDecodeError, pd.errors.ParserError):
                    logger.debug(f"UTF-8 failed, trying Latin-1: {file_path}")
                    df = pd.read_csv(file_path, encoding="iso-8859-1")
                    logger.debug(f"Parsed CSV with ISO-8859-1 encoding: {file_path}")

            # Convert to list of dicts
            rows = df.to_dict(orient="records")
            logger.info(f"Successfully parsed {len(rows)} rows from {file_path}")
            return rows

        except pd.errors.ParserError as e:
            logger.error(f"CSV parsing error in {file_path}: {e}")
            raise ValueError(f"CSV parsing error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing CSV {file_path}: {e}")
            raise ValueError(f"Error parsing CSV: {e}")

    def extract_rows_with_line_numbers(self, file_path: str) -> List[Tuple[int, Dict[str, Any]]]:
        """
        Parse CSV file and return list of (row_number, row_dict) tuples.

        Row numbers are 1-based (excluding header).

        Args:
            file_path: Path to CSV file

        Returns:
            List of (row_number, row_dict) tuples

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed
        """
        rows = self.parse(file_path)
        # Row numbers are 1-based (row 1 is first data row after header)
        return [(i + 1, row) for i, row in enumerate(rows)]

    def validate_structure(self, file_path: str, required_columns: List[str] = None) -> bool:
        """
        Validate CSV structure (header columns).

        Args:
            file_path: Path to CSV file
            required_columns: List of required column names (optional)

        Returns:
            True if valid, False otherwise

        Raises:
            ValueError: If required columns are missing
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        try:
            # Read just the header
            df = pd.read_csv(
                file_path,
                nrows=0,
                encoding=self.encoding or "utf-8",
            )
            columns = df.columns.tolist()

            if required_columns:
                missing = set(required_columns) - set(columns)
                if missing:
                    raise ValueError(f"CSV missing required columns: {missing}")

            logger.debug(f"CSV structure valid: {columns}")
            return True

        except Exception as e:
            logger.error(f"CSV structure validation failed: {e}")
            raise ValueError(f"CSV validation error: {e}")
