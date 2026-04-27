"""Duplicate detection for fund data."""

import logging
from datetime import date
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.schemas.ingestion import FundDataRow

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Detect duplicate fund entries."""

    @staticmethod
    def detect_duplicates(rows: List[FundDataRow]) -> Dict[str, List[int]]:
        """
        Detect duplicate rows within a batch.

        Identifies rows with same (fund_name, date) combination.

        Args:
            rows: List of validated FundDataRow objects

        Returns:
            Dict mapping "fund_name, date" key to list of row numbers
            Example: {"Vanguard 500, 2024-01-15": [3, 7]}
        """
        # Group rows by (fund_name, date)
        groups: Dict[Tuple[str, date], List[int]] = {}

        for idx, row in enumerate(rows, start=1):
            key = (row.fund_name, row.date_)
            if key not in groups:
                groups[key] = []
            groups[key].append(idx)

        # Filter to only duplicates (groups with >1 row)
        duplicates = {}
        for (fund_name, nav_date), row_numbers in groups.items():
            if len(row_numbers) > 1:
                key = f"{fund_name}, {nav_date.isoformat()}"
                duplicates[key] = row_numbers
                logger.debug(f"Found duplicate: {key} in rows {row_numbers}")

        logger.info(f"Detected {len(duplicates)} duplicate groups in batch of {len(rows)} rows")
        return duplicates

    @staticmethod
    def detect_duplicates_in_database(
        rows: List[FundDataRow], db_session: Session
    ) -> Dict[str, List[Tuple[int, int]]]:
        """
        Detect rows that conflict with existing database entries.

        Args:
            rows: List of validated FundDataRow objects
            db_session: SQLAlchemy session for database queries

        Returns:
            Dict mapping "fund_name, date" key to list of (row_number, existing_id) tuples
            Example: {"Vanguard 500, 2024-01-15": [(3, 42)]}
        """
        from src.database.models import NavHistory, Fund

        conflicts = {}

        for idx, row in enumerate(rows, start=1):
            # Look up fund by name
            fund = db_session.query(Fund).filter(Fund.name == row.fund_name).first()

            if not fund:
                # Fund doesn't exist in DB, no conflict
                logger.debug(f"Row {idx}: Fund '{row.fund_name}' not in database")
                continue

            # Check if nav entry exists for this fund on this date
            existing_nav = (
                db_session.query(NavHistory)
                .filter(NavHistory.fund_id == fund.id, NavHistory.date == row.date_)
                .first()
            )

            if existing_nav:
                key = f"{row.fund_name}, {row.date_.isoformat()}"
                if key not in conflicts:
                    conflicts[key] = []
                conflicts[key].append((idx, existing_nav.id))
                logger.debug(f"Row {idx}: Conflict found - NAV entry {existing_nav.id} exists in DB")

        logger.info(f"Detected {len(conflicts)} database conflicts for {len(rows)} rows")
        return conflicts

    @staticmethod
    def get_unique_rows(rows: List[FundDataRow], duplicates: Dict[str, List[int]]) -> List[FundDataRow]:
        """
        Filter out duplicate rows, keeping only first occurrence of each (fund_name, date).

        Args:
            rows: List of rows
            duplicates: Result from detect_duplicates()

        Returns:
            Filtered list with only unique rows (first occurrence per key)
        """
        # Get all row numbers that are duplicates (not the first)
        duplicate_indices = set()
        for row_numbers in duplicates.values():
            # Keep first, mark rest as duplicates
            duplicate_indices.update(row_numbers[1:])

        # Return only non-duplicate rows (convert to 0-based indexing)
        unique_rows = [row for idx, row in enumerate(rows, start=1) if idx not in duplicate_indices]
        logger.info(f"Filtered {len(rows)} rows to {len(unique_rows)} unique rows")
        return unique_rows
