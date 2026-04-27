"""Pydantic schemas for data validation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class FundDataRow(BaseModel):
    """Schema for a single fund data row."""

    fund_name: str = Field(..., min_length=1, description="Fund name")
    date_: date = Field(..., alias="date", description="NAV date in YYYY-MM-DD format")
    nav: Decimal = Field(..., gt=0, description="Net Asset Value (must be positive)")
    category: str = Field(..., description="Fund category")
    inception_date: Optional[date] = Field(None, description="Fund inception date")
    manager: Optional[str] = Field(None, description="Fund manager")

    @field_validator("nav")
    @classmethod
    def validate_nav(cls, v):
        """Validate NAV is positive."""
        if v <= 0:
            raise ValueError("NAV must be a positive number")
        return v

    @field_validator("fund_name")
    @classmethod
    def validate_fund_name(cls, v):
        """Validate fund name is not empty."""
        if not v or not v.strip():
            raise ValueError("Fund name cannot be empty")
        return v.strip()

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        """Validate category is not empty."""
        if not v or not v.strip():
            raise ValueError("Category cannot be empty")
        return v.strip()

    model_config = {"populate_by_name": True}

    def __getattr__(self, name: str):
        """Provide convenience property for 'date' attribute."""
        if name == "date":
            return self.date_
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


# Keep old Config section for JSON schema
class _FundDataRowConfig:
    """Config for FundDataRow (legacy)."""

    json_schema_extra = {
        "example": {
            "fund_name": "Vanguard 500",
            "date": "2024-01-15",
            "nav": 150.25,
            "category": "Equity",
            "inception_date": "2020-01-01",
            "manager": "Vanguard",
        }
    }


class ErrorDetail(BaseModel):
    """Schema for validation error details."""

    row_number: int = Field(..., description="1-based row number")
    field: str = Field(..., description="Field name that failed validation")
    error_message: str = Field(..., description="Human-readable error message")
    value: str = Field(..., description="Original value that failed")


class UploadJobResponse(BaseModel):
    """Schema for upload job status."""

    id: int = Field(..., description="Upload job ID")
    status: str = Field(..., description="Job status: pending, processing, completed, failed")
    file_name: str = Field(..., description="Uploaded file name")
    imported_count: int = Field(0, description="Number of rows successfully imported")
    rejected_count: int = Field(0, description="Number of rows rejected")
    errors: List[ErrorDetail] = Field(default_factory=list, description="List of validation errors")
    created_at: str = Field(..., description="Job creation timestamp")
    completed_at: Optional[str] = Field(None, description="Job completion timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "status": "completed",
                "file_name": "funds.csv",
                "imported_count": 10,
                "rejected_count": 2,
                "errors": [
                    {
                        "row_number": 5,
                        "field": "nav",
                        "error_message": "NAV must be a positive number",
                        "value": "-100",
                    }
                ],
                "created_at": "2024-01-15T10:30:00Z",
                "completed_at": "2024-01-15T10:35:00Z",
            }
        }
    }
