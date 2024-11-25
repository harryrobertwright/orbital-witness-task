from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class Report(BaseModel):
    """Model representing a report in the system."""

    id: int
    name: str
    credit_cost: Decimal


class Message(BaseModel):
    """Model representing a message in the system."""

    id: int
    text: str
    timestamp: datetime
    report_id: int | None = None
