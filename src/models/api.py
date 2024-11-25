from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel, ConfigDict

from src.models.domain import Message


class MessagesResponse(BaseModel):
    """Model representing the response from the messages endpoint."""

    messages: list[Message]


class UsageEntry(BaseModel):
    """Model representing a single usage entry in the response."""

    message_id: int
    timestamp: str
    report_name: str | None = None
    credits_used: Decimal

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda value: float(
                value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            )
        },
    )


class UsageResponse(BaseModel):
    """Model representing the usage endpoint response."""

    usage: list[UsageEntry]
