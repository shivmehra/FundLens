"""Repository for NAV history data access."""

import logging
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database.models import NavHistory

logger = logging.getLogger(__name__)


class DuplicateEntryError(Exception):
    """Raised when attempting to create duplicate NAV entry."""

    pass


class NavHistoryRepository:
    """Repository pattern for NavHistory data access."""

    @staticmethod
    def create_nav_entry(
        fund_id: int, nav_date: date, nav: Decimal, session: Optional[Session] = None
    ) -> NavHistory:
        """
        Create a new NAV history entry.

        Args:
            fund_id: Fund ID (foreign key)
            nav_date: Date of NAV (YYYY-MM-DD)
            nav: NAV value (positive decimal)
            session: SQLAlchemy session

        Returns:
            NavHistory object

        Raises:
            ValueError: If session not provided or invalid input
            DuplicateEntryError: If entry with same (fund_id, date) already exists
            Exception: Database errors
        """
        if not session:
            raise ValueError("Database session required")

        if nav <= 0:
            raise ValueError(f"NAV must be positive, got {nav}")

        try:
            nav_entry = NavHistory(fund_id=fund_id, date=nav_date, nav=nav)
            session.add(nav_entry)
            session.flush()
            logger.info(f"Created NAV entry: fund_id={fund_id}, date={nav_date}, nav={nav}")
            return nav_entry

        except IntegrityError as e:
            logger.error(f"Duplicate entry for fund_id={fund_id}, date={nav_date}: {e}")
            session.rollback()
            raise DuplicateEntryError(f"NAV entry already exists for fund_id={fund_id} on {nav_date}") from e

    @staticmethod
    def get_nav_by_fund_and_date(
        fund_id: int, nav_date: date, session: Optional[Session] = None
    ) -> Optional[NavHistory]:
        """
        Get NAV entry by fund and date.

        Args:
            fund_id: Fund ID
            nav_date: Date to search for
            session: SQLAlchemy session

        Returns:
            NavHistory object if found, None otherwise
        """
        if not session:
            raise ValueError("Database session required")

        nav_entry = session.query(NavHistory).filter(
            NavHistory.fund_id == fund_id, NavHistory.date == nav_date
        ).first()

        if nav_entry:
            logger.debug(f"Found NAV for fund_id={fund_id} on {nav_date} (nav={nav_entry.nav})")
        else:
            logger.debug(f"NAV not found for fund_id={fund_id} on {nav_date}")

        return nav_entry

    @staticmethod
    def get_nav_history_by_fund(fund_id: int, session: Optional[Session] = None) -> List[NavHistory]:
        """
        Get all NAV entries for a fund, sorted by date.

        Args:
            fund_id: Fund ID
            session: SQLAlchemy session

        Returns:
            List of NavHistory objects sorted by date (ascending)
        """
        if not session:
            raise ValueError("Database session required")

        nav_history = (
            session.query(NavHistory)
            .filter(NavHistory.fund_id == fund_id)
            .order_by(NavHistory.date)
            .all()
        )

        logger.debug(f"Retrieved {len(nav_history)} NAV entries for fund_id={fund_id}")
        return nav_history

    @staticmethod
    def check_duplicate(fund_id: int, nav_date: date, session: Optional[Session] = None) -> bool:
        """
        Check if NAV entry already exists for fund on date.

        Args:
            fund_id: Fund ID
            nav_date: Date to check
            session: SQLAlchemy session

        Returns:
            True if entry exists, False otherwise
        """
        if not session:
            raise ValueError("Database session required")

        exists = (
            session.query(NavHistory)
            .filter(NavHistory.fund_id == fund_id, NavHistory.date == nav_date)
            .first()
            is not None
        )

        logger.debug(f"NAV duplicate check for fund_id={fund_id}, date={nav_date}: {exists}")
        return exists

    @staticmethod
    def delete_nav_entry(entry_id: int, session: Optional[Session] = None) -> bool:
        """
        Delete a NAV history entry by ID.

        Args:
            entry_id: NavHistory ID to delete
            session: SQLAlchemy session

        Returns:
            True if entry was deleted, False if not found
        """
        if not session:
            raise ValueError("Database session required")

        nav_entry = session.query(NavHistory).filter(NavHistory.id == entry_id).first()

        if not nav_entry:
            logger.debug(f"NAV entry id={entry_id} not found for deletion")
            return False

        session.delete(nav_entry)
        logger.info(f"Deleted NAV entry id={entry_id}")
        return True
