"""Data validator for fund ingestion."""

import json
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from src.schemas.ingestion import ErrorDetail, FundDataRow

logger = logging.getLogger(__name__)


class DataValidator:
    """Validate fund data rows."""

    def __init__(self, schema_config_path: str = None):
        """
        Initialize data validator.

        Args:
            schema_config_path: Path to schema.json config file
        """
        self.schema_config_path = schema_config_path or Path(__file__).parent.parent.parent / "config" / "schema.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load schema configuration from JSON file."""
        try:
            with open(self.schema_config_path) as f:
                config = json.load(f)
            logger.debug(f"Loaded schema config from {self.schema_config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load schema config: {e}")
            raise ValueError(f"Cannot load schema config: {e}")

    def validate_row(self, row: Dict[str, Any], row_number: int) -> Tuple[Optional[FundDataRow], Optional[ErrorDetail]]:
        """
        Validate a single data row.

        Args:
            row: Raw dict from CSV/Excel parser
            row_number: 1-based row number for error reporting

        Returns:
            Tuple of (FundDataRow object, None) if valid
            or (None, ErrorDetail) if invalid
        """
        try:
            # Map CSV column names to schema fields
            mapped_row = self._map_fields(row, row_number)

            # Coerce string values to appropriate types
            coerced_row = self._coerce_types(mapped_row, row_number)

            # Validate with Pydantic
            validated_row = FundDataRow(**coerced_row)
            logger.debug(f"Row {row_number} validated successfully")
            return (validated_row, None)

        except ValidationError as e:
            # Extract first validation error for user-friendly message
            error_list = e.errors()
            if error_list:
                first_error = error_list[0]
                field = first_error["loc"][0] if first_error["loc"] else "unknown"
                original_value = str(row.get(field, ""))

                error_detail = ErrorDetail(
                    row_number=row_number,
                    field=str(field),
                    error_message=first_error["msg"],
                    value=original_value,
                )
                logger.debug(f"Row {row_number} validation failed: {error_detail.error_message}")
                return (None, error_detail)

        except Exception as e:
            error_detail = ErrorDetail(
                row_number=row_number,
                field="unknown",
                error_message=str(e),
                value=str(row),
            )
            logger.error(f"Row {row_number} validation error: {e}")
            return (None, error_detail)

    def _map_fields(self, row: Dict[str, Any], row_number: int) -> Dict[str, Any]:
        """
        Map CSV column names to schema field names.

        Args:
            row: Raw row dict from parser
            row_number: Row number for error reporting

        Returns:
            Dict with schema field names

        Raises:
            ValueError: If required fields are missing
        """
        mapping = self.config.get("field_mapping", {})
        required = self.config.get("required_fields", [])

        mapped = {}

        # Try to map all fields from the row
        for csv_col, value in row.items():
            schema_field = mapping.get(csv_col)
            if schema_field:
                mapped[schema_field] = value

        # Check for required fields
        missing = []
        for req_field in required:
            if req_field not in mapped:
                # Try to find which CSV column was expected
                for csv_col, schema_field in mapping.items():
                    if schema_field == req_field and csv_col not in row:
                        missing.append(csv_col)
                        break

        if missing:
            raise ValueError(f"Row {row_number} missing required fields: {missing}")

        return mapped

    def _coerce_types(self, row: Dict[str, Any], row_number: int) -> Dict[str, Any]:
        """
        Coerce string values to appropriate types.

        Args:
            row: Mapped row dict with string values
            row_number: Row number for error reporting

        Returns:
            Dict with coerced types

        Raises:
            ValueError: If type coercion fails
        """
        coerced = {}

        for key, value in row.items():
            if value is None or (isinstance(value, float) and value != value):  # NaN check
                coerced[key] = None
                continue

            # Type coercion based on field name
            try:
                if key == "nav":
                    # Convert to Decimal
                    if isinstance(value, str):
                        coerced[key] = Decimal(value.strip())
                    else:
                        coerced[key] = Decimal(str(value))
                elif key == "date":
                    # Rename to date_ for Pydantic model
                    coerced["date_"] = value
                elif key == "inception_date":
                    # Keep as string or datetime
                    coerced[key] = value
                else:
                    # String fields
                    coerced[key] = str(value).strip() if value else None

            except Exception as e:
                raise ValueError(f"Cannot coerce {key}='{value}' to appropriate type: {e}")

        return coerced

    def validate_batch(self, rows: List[Tuple[int, Dict[str, Any]]]) -> Tuple[List[FundDataRow], List[ErrorDetail]]:
        """
        Validate a batch of rows.

        Args:
            rows: List of raw dicts from parser (with row numbers)

        Returns:
            Tuple of (valid_rows, error_details)
        """
        valid_rows = []
        errors = []

        for row_num, row_dict in rows:
            validated_row, error = self.validate_row(row_dict, row_num)
            if error:
                errors.append(error)
            else:
                valid_rows.append(validated_row)

        logger.info(f"Batch validation: {len(valid_rows)} valid, {len(errors)} errors")
        return (valid_rows, errors)
