from decimal import Decimal
from typing import Any, ClassVar
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from httpx import AsyncClient, HTTPError

from src.core.config import settings
from src.core.exceptions import APIError, MessageParsingError, ReportParsingError
from src.services.client import Client, Messages, Reports


class TestReports(IsolatedAsyncioTestCase):
    VALID_REPORT_DATA: ClassVar[dict[str, Any]] = {
        "id": 5392,
        "name": "Tenant Obligations Report",
        "credit_cost": "25.50",
    }

    async def asyncSetUp(self) -> None:
        self.mock_http = AsyncMock()
        self.mock_client = Mock(http=self.mock_http, base_url="https://api.test")
        self.reports = Reports(self.mock_client)

    async def test_should_return_parsed_report_when_request_succeeds(self) -> None:
        report_id = 5392
        mock_response = Mock(json=Mock(return_value=self.VALID_REPORT_DATA))
        self.mock_http.get.return_value = mock_response

        report = await self.reports.get(report_id)

        assert report.id == report_id
        assert report.name == "Tenant Obligations Report"
        assert report.credit_cost == Decimal("25.50")
        self.mock_http.get.assert_called_once_with(
            f"{self.mock_client.base_url}/reports/{report_id}"
        )

    async def test_should_raise_api_error_when_http_request_fails(self) -> None:
        report_id = 5392
        self.mock_http.get.side_effect = HTTPError("API error")

        with self.assertRaises(APIError) as ctx:
            await self.reports.get(report_id)

        assert f"Failed to fetch report {report_id}" in str(ctx.exception)
        self.mock_http.get.assert_called_once()

    async def test_should_raise_parsing_error_when_missing_required_fields(
        self,
    ) -> None:
        report_id = 5392
        invalid_data = {"id": report_id, "credit_cost": "25.50"}
        mock_response = Mock(json=Mock(return_value=invalid_data))
        self.mock_http.get.return_value = mock_response

        with self.assertRaises(ReportParsingError) as ctx:
            await self.reports.get(report_id)

        assert str(ctx.exception) == ReportParsingError.INVALID_FORMAT

    async def test_should_raise_parsing_error_when_credit_cost_invalid(self) -> None:
        report_id = 5392
        invalid_data = {
            "id": report_id,
            "name": "Tenant Obligations Report",
            "credit_cost": "invalid.amount",
        }
        mock_response = Mock(json=Mock(return_value=invalid_data))
        self.mock_http.get.return_value = mock_response

        with self.assertRaises(ReportParsingError) as ctx:
            await self.reports.get(report_id)

        assert str(ctx.exception) == ReportParsingError.INVALID_FORMAT

    async def test_should_raise_parsing_error_when_json_invalid(self) -> None:
        report_id = 5392
        mock_response = Mock(json=Mock(side_effect=ValueError("Invalid JSON")))
        self.mock_http.get.return_value = mock_response

        with self.assertRaises(ReportParsingError) as ctx:
            await self.reports.get(report_id)

        assert str(ctx.exception) == ReportParsingError.UNEXPECTED_ERROR


class TestMessages(IsolatedAsyncioTestCase):
    BASE_URL: ClassVar[str] = "https://api.test"
    ENDPOINT: ClassVar[str] = "/messages/current-period"
    VALID_MESSAGE: ClassVar[dict[str, Any]] = {
        "id": 1,
        "text": "Test message",
        "timestamp": "2024-01-01T00:00:00Z",
        "report_id": 123,
    }

    async def asyncSetUp(self) -> None:
        self.mock_http = AsyncMock()
        self.mock_client = Mock(http=self.mock_http, base_url=self.BASE_URL)
        self.messages = Messages(self.mock_client)

    def create_mock_response(
        self, json_data: dict | None = None, json_error: Exception | None = None
    ) -> Mock:
        mock_response = Mock()
        if json_data is not None:
            mock_response.json.return_value = json_data
        if json_error is not None:
            mock_response.json.side_effect = json_error
        return mock_response

    async def test_should_return_parsed_messages_when_request_succeeds(self) -> None:
        mock_response = self.create_mock_response({"messages": [self.VALID_MESSAGE]})
        self.mock_http.get.return_value = mock_response

        messages = await self.messages.get_current_period()

        assert len(messages) == 1
        message = messages[0]
        assert message.id == self.VALID_MESSAGE["id"]
        assert message.text == self.VALID_MESSAGE["text"]
        assert message.report_id == self.VALID_MESSAGE["report_id"]
        self.mock_http.get.assert_called_once_with(f"{self.BASE_URL}{self.ENDPOINT}")

    async def test_should_raise_api_error_when_http_request_fails(self) -> None:
        self.mock_http.get.side_effect = HTTPError("API error")

        with self.assertRaises(APIError) as ctx:
            await self.messages.get_current_period()

        assert "Failed to fetch messages" in str(ctx.exception)
        self.mock_http.get.assert_called_once()

    async def test_should_raise_parsing_error_when_data_invalid(self) -> None:
        mock_response = self.create_mock_response({"messages": [{"invalid": "data"}]})
        self.mock_http.get.return_value = mock_response

        with self.assertRaises(MessageParsingError) as ctx:
            await self.messages.get_current_period()

        assert str(ctx.exception) == MessageParsingError.INVALID_FORMAT

    async def test_should_raise_parsing_error_when_json_invalid(self) -> None:
        mock_response = self.create_mock_response(json_error=ValueError("Invalid JSON"))
        self.mock_http.get.return_value = mock_response

        with self.assertRaises(MessageParsingError) as ctx:
            await self.messages.get_current_period()

        assert str(ctx.exception) == MessageParsingError.UNEXPECTED_ERROR


class TestClient(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.client = Client()

    async def asyncTearDown(self) -> None:
        await self.client.__aexit__(None, None, None)

    @patch.object(AsyncClient, "__init__", return_value=None)
    async def test_should_initialise_with_required_resources(
        self, mock_init: Mock
    ) -> None:
        client = Client()

        assert client.messages is not None
        assert client.reports is not None
        assert client.base_url == settings.COPILOT_API_BASE_URL
        mock_init.assert_called_once()

    @patch.object(AsyncClient, "aclose")
    async def test_should_close_http_client_when_context_exited(
        self, mock_aclose: AsyncMock
    ) -> None:
        async with Client() as client:
            assert client is not None

        mock_aclose.assert_awaited_once()
