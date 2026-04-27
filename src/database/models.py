"""SQLAlchemy ORM models for fund data persistence."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Date,
)
from sqlalchemy.orm import relationship

from src.database.base import Base


class Fund(Base):
    """Fund master data."""

    __tablename__ = "funds"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False)
    inception_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    nav_history = relationship("NavHistory", back_populates="fund", cascade="all, delete-orphan")
    metadata_rel = relationship("FundMetadata", back_populates="fund", cascade="all, delete-orphan", uselist=False)

    def __repr__(self):
        return f"<Fund(id={self.id}, name={self.name}, category={self.category})>"


class NavHistory(Base):
    """NAV (Net Asset Value) history for funds."""

    __tablename__ = "nav_history"

    id = Column(Integer, primary_key=True)
    fund_id = Column(Integer, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    nav = Column(Numeric(15, 4), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint("fund_id", "date", name="uq_nav_history_fund_date"),
        Index("ix_nav_history_fund_id", "fund_id"),
        Index("ix_nav_history_date", "date"),
    )

    # Relationships
    fund = relationship("Fund", back_populates="nav_history")

    def __repr__(self):
        return f"<NavHistory(fund_id={self.fund_id}, date={self.date}, nav={self.nav})>"


class FundMetadata(Base):
    """Additional metadata and performance metrics for funds."""

    __tablename__ = "fund_metadata"

    id = Column(Integer, primary_key=True)
    fund_id = Column(Integer, ForeignKey("funds.id", ondelete="CASCADE"), unique=True, nullable=False)
    manager = Column(String(255), nullable=True)
    allocation = Column(Text, nullable=True)  # JSON or comma-separated allocation data
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    cagr = Column(Float, nullable=True)
    aum = Column(Numeric(20, 2), nullable=True)  # Assets Under Management
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    fund = relationship("Fund", back_populates="metadata_rel")

    def __repr__(self):
        return f"<FundMetadata(fund_id={self.fund_id}, manager={self.manager})>"


class UploadJob(Base):
    """Track file upload jobs and their processing status."""

    __tablename__ = "upload_jobs"

    id = Column(Integer, primary_key=True)
    status = Column(String(50), nullable=False, index=True)  # pending, processing, completed, failed
    file_name = Column(String(255), nullable=False)
    imported_count = Column(Integer, default=0, nullable=False)
    rejected_count = Column(Integer, default=0, nullable=False)
    error_json = Column(Text, nullable=True)  # Serialized JSON of validation errors
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<UploadJob(id={self.id}, status={self.status}, file_name={self.file_name})>"
