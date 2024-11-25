class BaseError(Exception):
    """Base exception for client errors."""


class MessageParsingError(BaseError):
    """Raised when message data cannot be parsed."""

    INVALID_FORMAT = "Invalid message data format"
    UNEXPECTED_ERROR = "Unexpected error while parsing messages"

    def __init__(self, message: str, original_error: Exception) -> None:
        """Initialise message parsing error.

        Args:
            message: Error description.
            original_error: The original exception that was caught.

        """
        self.original_error = original_error
        super().__init__(message)


class ReportParsingError(BaseError):
    """Raised when report data cannot be parsed."""

    INVALID_FORMAT = "Invalid report data format"
    UNEXPECTED_ERROR = "Unexpected error while parsing report"

    def __init__(self, report_id: int, message: str, original_error: Exception) -> None:
        """Initialise report parsing error.

        Args:
            report_id: ID of the report that failed to parse.
            message: Error description.
            original_error: The original exception that was caught.

        """
        self.report_id = report_id
        self.original_error = original_error
        super().__init__(message)


class APIError(BaseError):
    """Raised when an API request fails."""

    def __init__(self, message: str, original_error: Exception) -> None:
        """Initialise API error.

        Args:
            message: Error description.
            original_error: The original exception that was caught.

        """
        super().__init__(f"API request failed: {message}")
        self.original_error = original_error
