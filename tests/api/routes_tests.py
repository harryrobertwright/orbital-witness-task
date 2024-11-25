from decimal import ROUND_HALF_UP, Decimal
from http import HTTPStatus
from typing import Any, Final
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient
from httpx import HTTPError

from src.main import app
from src.services.client import Client
from src.utils import Calculator


class MockResponse:
    def __init__(
        self, status_code: int, json_data: dict | None = None, **_: object
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data or {}
        self.raise_for_status = Mock()
        if status_code >= HTTPStatus.BAD_REQUEST:
            self.raise_for_status.side_effect = HTTPError("Error")

    def json(self) -> dict:
        return self._json_data


class TestUsageEndpoint(IsolatedAsyncioTestCase):
    BASE_URL: Final[str] = "https://owpublic.blob.core.windows.net/tech-task"
    MESSAGES_ENDPOINT: Final[str] = f"{BASE_URL}/messages/current-period"
    REPORTS_ENDPOINT: Final[str] = f"{BASE_URL}/reports"

    def rounded_decimal(self, value: Any) -> Decimal:  # noqa: ANN401
        """Round a decimal value to the given precision."""
        return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    async def asyncSetUp(self) -> None:
        self.messages_mock = MockResponse(HTTPStatus.OK)
        self.report_mock = MockResponse(HTTPStatus.OK)

        app.state.calculator = Calculator()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.get = AsyncMock()
            app.state.client = Client()
            app.state.client.http = mock_instance
            app.state.client.base_url = self.BASE_URL

        self.mock_get = app.state.client.http.get
        self.client = TestClient(app)

    async def configure_mock_response(
        self,
        messages_response: dict,
        report_response: dict | None = None,
        report_status: int = HTTPStatus.OK,
    ) -> None:
        self.messages_mock = MockResponse(HTTPStatus.OK, messages_response)

        if report_response and report_status == HTTPStatus.OK:
            self.report_mock = MockResponse(HTTPStatus.OK, report_response)
        else:
            error_response = MockResponse(report_status)
            self.report_mock = error_response
            error = HTTPError("Not found")
            error.response = error_response
            self.report_mock.raise_for_status.side_effect = error

        async def mock_get(url: str) -> MockResponse:
            if url.startswith(self.REPORTS_ENDPOINT):
                return self.report_mock
            return self.messages_mock

        self.mock_get.side_effect = mock_get

    async def test_should_calculate_usage_for_various_message_types(self) -> None:
        expected_messages: Final[int] = 4
        messages_response = {
            "messages": [
                {
                    "id": 1,
                    "text": "Generate tenant report",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "report_id": 5392,
                },
                {
                    "id": 2,
                    "text": "What rental amount is specified?",
                    "timestamp": "2024-01-01T10:05:00Z",
                },
                {
                    "id": 3,
                    "text": "A man a plan a canal Panama",
                    "timestamp": "2024-01-01T10:10:00Z",
                },
                {
                    "id": 4,
                    "text": "Generate invalid report",
                    "timestamp": "2024-01-01T10:15:00Z",
                    "report_id": 9999,
                },
            ]
        }

        report_response = {
            "id": 5392,
            "name": "Tenant Obligations Report",
            "credit_cost": "25.50",
        }

        await self.configure_mock_response(messages_response, report_response)

        response = self.client.get("/usage")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "usage" in data
        usage = data["usage"]
        assert len(usage) == expected_messages

        report_msg_id: Final[int] = 1
        report_usage = next(u for u in usage if u["message_id"] == report_msg_id)
        assert report_usage["report_name"] == "Tenant Obligations Report"
        assert self.rounded_decimal(report_usage["credits_used"]) == Decimal("25.50")

        simple_msg_id: Final[int] = 2
        simple_usage = next(u for u in usage if u["message_id"] == simple_msg_id)
        assert simple_usage["report_name"] is None
        assert self.rounded_decimal(simple_usage["credits_used"]) == Decimal("2.8")

        palindrome_msg_id: Final[int] = 3
        palindrome_usage = next(
            u for u in usage if u["message_id"] == palindrome_msg_id
        )
        assert palindrome_usage["report_name"] is None
        assert self.rounded_decimal(palindrome_usage["credits_used"]) == Decimal("7.30")

    async def test_should_handle_messages_api_error(self) -> None:
        error_response = MockResponse(HTTPStatus.INTERNAL_SERVER_ERROR)
        error = HTTPError("API Error")
        error.response = error_response
        self.mock_get.side_effect = error

        response = self.client.get("/usage")

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert "Failed to fetch data" in response.json()["detail"]

    async def test_should_handle_invalid_messages_format(self) -> None:
        await self.configure_mock_response({"messages": [{"invalid": "format"}]})

        response = self.client.get("/usage")

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "Failed to parse messages" in response.json()["detail"]

    async def test_should_fallback_to_text_when_report_not_found(self) -> None:
        messages_response = {
            "messages": [
                {
                    "id": 1,
                    "text": "Generate tenant obligations report please",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "report_id": 5392,
                }
            ]
        }

        await self.configure_mock_response(
            messages_response, report_status=HTTPStatus.NOT_FOUND
        )

        response = self.client.get("/usage")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        usage = data["usage"][0]
        assert usage["report_name"] is None
        assert self.rounded_decimal(usage["credits_used"]) == Decimal("3.45")

    async def test_should_apply_length_penalty_for_long_messages(self) -> None:
        messages_response = {
            "messages": [
                {"id": 1, "text": "x" * 101, "timestamp": "2024-01-01T10:00:00Z"}
            ]
        }

        await self.configure_mock_response(messages_response)

        response = self.client.get("/usage")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        usage = data["usage"][0]
        assert self.rounded_decimal(usage["credits_used"]) == Decimal("18.7")

    async def test_should_apply_unique_words_bonus(self) -> None:
        messages_response = {
            "messages": [
                {
                    "id": 1,
                    "text": "The quick brown fox jumps over lazy dog",
                    "timestamp": "2024-01-01T10:00:00Z",
                }
            ]
        }

        await self.configure_mock_response(messages_response)

        response = self.client.get("/usage")

        data = response.json()
        usage = data["usage"][0]
        assert self.rounded_decimal(usage["credits_used"]) == Decimal("3.75")

    async def test_should_handle_multiple_messages_with_mixed_reports(self) -> None:
        expected_msgs: Final[int] = 2
        first_msg_id: Final[int] = 1
        second_msg_id: Final[int] = 2

        messages_response = {
            "messages": [
                {
                    "id": first_msg_id,
                    "text": "First report",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "report_id": 5392,
                },
                {
                    "id": second_msg_id,
                    "text": "Second report analysis required",
                    "timestamp": "2024-01-01T10:05:00Z",
                    "report_id": 9999,
                },
            ]
        }

        report_response = {"id": 5392, "name": "Test Report", "credit_cost": "15.75"}

        await self.configure_mock_response(messages_response, report_response)

        response = self.client.get("/usage")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        usage = data["usage"]
        assert len(usage) == expected_msgs

        first_usage = next(u for u in usage if u["message_id"] == first_msg_id)
        assert first_usage["report_name"] == "Test Report"
        assert self.rounded_decimal(first_usage["credits_used"]) == Decimal("15.75")

        second_usage = next(u for u in usage if u["message_id"] == second_msg_id)
        assert second_usage["report_name"] is None
        assert self.rounded_decimal(second_usage["credits_used"]) == Decimal("3.05")
