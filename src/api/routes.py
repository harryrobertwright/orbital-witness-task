from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_usage_service
from src.core.exceptions import APIError, MessageParsingError
from src.models.api import UsageResponse
from src.services import UsageService

router = APIRouter()


@router.get("/usage")
async def get_usage(
    usage_service: UsageService = Depends(get_usage_service),  # noqa: B008, FAST002
) -> UsageResponse:
    """Get usage data for the current billing period.

    Returns:
        Object containing list of usage entries for each message.

    Raises:
        HTTPException: If there's an error fetching or processing the data.

    """
    try:
        return await usage_service.get_current_period_usage()
    except MessageParsingError as error:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Failed to parse messages response: {error!s}",
        ) from error
    except APIError as error:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch data: {error!s}",
        ) from error
