from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock

from src.core.exceptions import APIError
from src.services.usage import UsageService


class TestUsageService(IsolatedAsyncioTestCase):
    SAMPLE_TIMESTAMP = datetime(2024, 1, 1, tzinfo=UTC)
    SAMPLE_CREDITS = Decimal("5.00")
    EXPECTED_REPORT_COUNT = 2
    EXPECTED_MESSAGE_COUNT = 3
    EXPECTED_REPORTS_WITH_DATA = 2
    EXPECTED_CALC_CALLS = 3

    REPORT_ID_1 = 123
    REPORT_ID_2 = 456

    async def asyncSetUp(self) -> None:
        self.mock_client = Mock()
        self.mock_calculator = Mock()
        self.service = UsageService(
            client=self.mock_client, calculator=self.mock_calculator
        )

        # Setup common mocks
        self.mock_client.reports = AsyncMock()
        self.mock_client.messages = AsyncMock()

    def create_sample_message(
        self, id: int = 1, report_id: int | None = REPORT_ID_1
    ) -> Mock:
        mock_message = Mock()
        mock_message.id = id
        mock_message.text = "Test message"
        mock_message.timestamp = self.SAMPLE_TIMESTAMP
        mock_message.report_id = report_id
        return mock_message

    def create_sample_report(
        self, id: int = REPORT_ID_1, name: str = "Test Report"
    ) -> Mock:
        mock_report = Mock()
        mock_report.id = id
        mock_report.name = name
        mock_report.credit_cost = Decimal("10.00")
        return mock_report

    async def test_should_return_empty_dict_when_fetching_no_reports(self) -> None:
        result = await self.service.fetch_reports([])

        assert result == {}
        self.mock_client.reports.get.assert_not_called()

    async def test_should_return_mapped_reports_when_fetch_succeeds(self) -> None:
        report_ids = [self.REPORT_ID_1, self.REPORT_ID_2]
        reports = [
            self.create_sample_report(id=self.REPORT_ID_1, name="Report 1"),
            self.create_sample_report(id=self.REPORT_ID_2, name="Report 2"),
        ]

        self.mock_client.reports.get.side_effect = reports

        result = await self.service.fetch_reports(report_ids)

        assert len(result) == self.EXPECTED_REPORT_COUNT
        assert all(rid in result for rid in report_ids)
        assert self.mock_client.reports.get.call_count == self.EXPECTED_REPORT_COUNT

    async def test_should_exclude_not_found_reports_when_fetching(self) -> None:
        report_ids = [self.REPORT_ID_1, self.REPORT_ID_2]
        not_found_error = APIError(
            "Report not found",
            original_error=Mock(response=Mock(status_code=HTTPStatus.NOT_FOUND)),
        )

        self.mock_client.reports.get.side_effect = [
            self.create_sample_report(id=self.REPORT_ID_1),
            not_found_error,
        ]

        result = await self.service.fetch_reports(report_ids)

        assert len(result) == 1
        assert self.REPORT_ID_1 in result
        assert self.REPORT_ID_2 not in result
        assert self.mock_client.reports.get.call_count == self.EXPECTED_REPORT_COUNT

    async def test_should_raise_api_error_when_fetch_fails_with_server_error(
        self,
    ) -> None:
        server_error = APIError(
            "Internal server error",
            original_error=Mock(
                response=Mock(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
            ),
        )
        self.mock_client.reports.get.side_effect = server_error

        with self.assertRaises(APIError):
            await self.service.fetch_reports([self.REPORT_ID_1])

    def test_should_create_usage_entry_with_report_data(self) -> None:
        message = self.create_sample_message()
        report = self.create_sample_report()
        mock_usage_entry = Mock(
            message_id=message.id,
            timestamp=message.timestamp.isoformat(),
            credits_used=self.SAMPLE_CREDITS,
            report_name=report.name,
        )

        self.mock_calculator.calculate.return_value = self.SAMPLE_CREDITS

        result = self.service.create_usage_entry(message, report)

        assert result.message_id == mock_usage_entry.message_id
        assert result.timestamp == mock_usage_entry.timestamp
        assert result.credits_used == mock_usage_entry.credits_used
        assert result.report_name == mock_usage_entry.report_name
        self.mock_calculator.calculate.assert_called_once_with(message, report)

    def test_should_create_usage_entry_without_report_data(self) -> None:
        message = self.create_sample_message(report_id=None)
        mock_usage_entry = Mock(
            message_id=message.id,
            timestamp=message.timestamp.isoformat(),
            credits_used=self.SAMPLE_CREDITS,
            report_name=None,
        )

        self.mock_calculator.calculate.return_value = self.SAMPLE_CREDITS

        result = self.service.create_usage_entry(message, None)

        assert result.message_id == mock_usage_entry.message_id
        assert result.timestamp == mock_usage_entry.timestamp
        assert result.credits_used == mock_usage_entry.credits_used
        assert result.report_name == mock_usage_entry.report_name
        self.mock_calculator.calculate.assert_called_once_with(message, None)

    async def test_should_return_complete_usage_response_for_current_period(
        self,
    ) -> None:
        messages = [
            self.create_sample_message(id=1, report_id=self.REPORT_ID_1),
            self.create_sample_message(id=2, report_id=self.REPORT_ID_2),
            self.create_sample_message(id=3, report_id=None),
        ]
        reports = {
            self.REPORT_ID_1: self.create_sample_report(
                id=self.REPORT_ID_1, name="Report 1"
            ),
            self.REPORT_ID_2: self.create_sample_report(
                id=self.REPORT_ID_2, name="Report 2"
            ),
        }

        self.mock_client.messages.get_current_period.return_value = messages
        self.mock_client.reports.get.side_effect = list(reports.values())
        self.mock_calculator.calculate.return_value = self.SAMPLE_CREDITS

        result = await self.service.get_current_period_usage()

        assert len(result.usage) == self.EXPECTED_MESSAGE_COUNT

        # Verify entries with reports
        report_entries = [
            entry for entry in result.usage if entry.report_name is not None
        ]
        assert len(report_entries) == self.EXPECTED_REPORTS_WITH_DATA
        assert all(
            entry.credits_used == self.SAMPLE_CREDITS for entry in report_entries
        )

        no_report_entries = [
            entry for entry in result.usage if entry.report_name is None
        ]
        assert len(no_report_entries) == 1
        assert no_report_entries[0].credits_used == self.SAMPLE_CREDITS

        self.mock_client.messages.get_current_period.assert_called_once()
        assert (
            self.mock_client.reports.get.call_count == self.EXPECTED_REPORTS_WITH_DATA
        )
        assert self.mock_calculator.calculate.call_count == self.EXPECTED_CALC_CALLS

    async def test_should_return_empty_usage_response_when_no_messages_exist(
        self,
    ) -> None:
        self.mock_client.messages.get_current_period.return_value = []

        result = await self.service.get_current_period_usage()

        assert len(result.usage) == 0
        self.mock_client.messages.get_current_period.assert_called_once()
        self.mock_client.reports.get.assert_not_called()
        self.mock_calculator.calculate.assert_not_called()
