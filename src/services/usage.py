import asyncio
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from http import HTTPStatus

from src.core.exceptions import APIError
from src.models import Message, Report, UsageEntry, UsageResponse
from src.services.client import Client
from src.utils.calculator import Calculator


@dataclass
class UsageService:
    """Service class for managing usage-related operations.

    This class handles fetching reports, creating usage entries, and calculating
    usage for billing periods.
    """

    client: Client
    calculator: Calculator

    async def fetch_reports(self, report_ids: list[str]) -> dict[str, Report]:
        """Fetch multiple reports concurrently and returns them as a mapping.

        Args:
            report_ids: A list of report IDs to fetch.

        Returns:
            A dictionary mapping report IDs to Report objects. Reports that were
            not found are excluded from the result.

        Raises:
            APIError: If there is an API error other than NOT_FOUND when fetching
                reports.

        """
        if not report_ids:
            return {}

        async def fetch_report(report_id: str) -> Report | None:
            try:
                return await self.client.reports.get(report_id)
            except APIError as error:
                if error.original_error.response.status_code == HTTPStatus.NOT_FOUND:
                    return None
                raise
        
        # Doing these operations concurrently for a bit of a performance boost.
        reports = await asyncio.gather(
            *[fetch_report(rid) for rid in report_ids], return_exceptions=False
        )

        return {report.id: report for report in reports if report is not None}

    def create_usage_entry(self, message: Message, report: Report | None) -> UsageEntry:
        """Create a usage entry from a message and its associated report.

        Args:
            message: The Message object containing usage information.
            report: Optional Report object associated with the message.
                Can be None if no report is associated.

        Returns:
            A UsageEntry object containing the processed usage information.

        Note:
            The credits are calculated using the service's calculator instance,
            which takes into account both the message and report data.

        """
        credits = self.calculator.calculate(message, report).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return UsageEntry(
            message_id=message.id,
            timestamp=message.timestamp.isoformat(),
            credits_used=credits,
            report_name=report.name if report else None,
        )

    async def get_current_period_usage(self) -> UsageResponse:
        """Retrieve usage data for the current billing period.

        Returns:
            A UsageResponse object containing a list of usage entries for all
            messages in the current billing period.

        Raises:
            APIError: If there is an error fetching messages or reports from
                the API.

        Note:
            Messages without associated reports will still be included in the
            response, but their report_name field will be None.

        """
        messages = await self.client.messages.get_current_period()

        report_ids = [
            message.report_id for message in messages if message.report_id is not None
        ]
        report_map = await self.fetch_reports(report_ids)

        usage_entries = [
            self.create_usage_entry(message, report_map.get(message.report_id))
            for message in messages
        ]

        return UsageResponse(usage=usage_entries)
