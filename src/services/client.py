from httpx import AsyncClient, HTTPError
from pydantic import ValidationError

from src.core.config import settings
from src.core.exceptions import APIError, MessageParsingError, ReportParsingError
from src.models import Message, Report


class Messages:
    """Messages resource for the OrbitalCopilot API."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def get_current_period(self) -> list["Message"]:
        """Fetch all messages from the current billing period.

        Returns:
            All messages from the current period.

        Raises:
            MessageParsingError: If the response data cannot be parsed.
            APIError: If the API request fails.

        """
        from src.models import MessagesResponse

        try:
            response = await self._client.http.get(
                f"{self._client.base_url}/messages/current-period"
            )
            response.raise_for_status()
            json_data = response.json()
        except HTTPError as error:
            error_message = "Failed to fetch messages"
            raise APIError(error_message, error) from error
        except ValueError as error:
            raise MessageParsingError(
                MessageParsingError.UNEXPECTED_ERROR, error
            ) from error

        try:
            return MessagesResponse.model_validate(json_data).messages
        except ValidationError as error:
            raise MessageParsingError(
                MessageParsingError.INVALID_FORMAT, error
            ) from error


class Reports:
    """Reports resource for the OrbitalCopilot API."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def get(self, report_id: int) -> "Report":
        """Fetch report details by ID.

        Args:
            report_id: The ID of the report to fetch.

        Returns:
            Report object containing name and credit cost.

        Raises:
            ReportParsingError: If the response data cannot be parsed.
            APIError: If the API request fails.

        """
        try:
            response = await self._client.http.get(
                f"{self._client.base_url}/reports/{report_id}"
            )
            response.raise_for_status()
            json_data = response.json()
        except HTTPError as error:
            error_message = f"Failed to fetch report {report_id}"
            raise APIError(error_message, error) from error
        except ValueError as error:
            raise ReportParsingError(
                report_id, ReportParsingError.UNEXPECTED_ERROR, error
            ) from error

        try:
            return Report.model_validate(json_data)
        except ValidationError as error:
            raise ReportParsingError(
                report_id, ReportParsingError.INVALID_FORMAT, error
            ) from error


# Structured the client to centralise all API interactions, with a shared
# HTTP client. Added the `messages` and `reports` resources to separate concerns
# (each resource is responsible for its own logic).
class Client:
    """Client for interacting with the Copilot API."""

    def __init__(self) -> None:
        """Initialise the client with resources."""
        self.http = AsyncClient()
        self.base_url = settings.COPILOT_API_BASE_URL
        self.messages = Messages(self)
        self.reports = Reports(self)

    async def __aenter__(self) -> "Client":
        """Enter the async context manager."""
        return self

    async def __aexit__(self, *_: object) -> None:
        """Exit the async context manager and close the HTTP client."""
        await self.http.aclose()
