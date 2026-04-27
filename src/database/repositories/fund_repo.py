"""Repository for fund data access."""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from src.database.models import Fund

logger = logging.getLogger(__name__)


class FundRepository:
    """Repository pattern for Fund data access."""

    @staticmethod
    def create_or_get_fund(
        name: str, category: str, inception_date: Optional[str] = None, session: Optional[Session] = None
    ) -> Fund:
        """
        Create a new fund or return existing fund by name.

        Args:
            name: Fund name
            category: Fund category (Equity, Debt, etc.)
            inception_date: Optional fund inception date (YYYY-MM-DD)
            session: SQLAlchemy session

        Returns:
            Fund object (newly created or existing)

        Raises:
            ValueError: If session not provided
            Exception: Database errors
        """
        if not session:
            raise ValueError("Database session required")

        # Check if fund already exists
        existing_fund = session.query(Fund).filter(Fund.name == name).first()
        if existing_fund:
            logger.debug(f"Fund '{name}' already exists (id={existing_fund.id})")
            return existing_fund

        # Create new fund
        try:
            fund = Fund(name=name, category=category, inception_date=inception_date)
            session.add(fund)
            session.flush()  # Flush to get the ID without committing
            logger.info(f"Created new fund: '{name}' (id={fund.id}, category={category})")
            return fund
        except Exception as e:
            logger.error(f"Failed to create fund '{name}': {e}")
            raise

    @staticmethod
    def get_fund_by_name(name: str, session: Optional[Session] = None) -> Optional[Fund]:
        """
        Get fund by name.

        Args:
            name: Fund name to search for
            session: SQLAlchemy session

        Returns:
            Fund object if found, None otherwise
        """
        if not session:
            raise ValueError("Database session required")

        fund = session.query(Fund).filter(Fund.name == name).first()
        if fund:
            logger.debug(f"Found fund '{name}' (id={fund.id})")
        else:
            logger.debug(f"Fund '{name}' not found")
        return fund

    @staticmethod
    def get_fund_by_id(fund_id: int, session: Optional[Session] = None) -> Optional[Fund]:
        """
        Get fund by ID.

        Args:
            fund_id: Fund ID
            session: SQLAlchemy session

        Returns:
            Fund object if found, None otherwise
        """
        if not session:
            raise ValueError("Database session required")

        fund = session.query(Fund).filter(Fund.id == fund_id).first()
        if fund:
            logger.debug(f"Found fund id={fund_id} ('{fund.name}')")
        else:
            logger.debug(f"Fund id={fund_id} not found")
        return fund

    @staticmethod
    def list_funds(session: Optional[Session] = None) -> List[Fund]:
        """
        Get all funds.

        Args:
            session: SQLAlchemy session

        Returns:
            List of Fund objects
        """
        if not session:
            raise ValueError("Database session required")

        funds = session.query(Fund).order_by(Fund.name).all()
        logger.debug(f"Retrieved {len(funds)} funds from database")
        return funds
