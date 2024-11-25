from abc import ABC, abstractmethod
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING, ClassVar, Optional

if TYPE_CHECKING:
    from src.models import Message, Report


class Handler(ABC):
    """Abstract base class for credit calculation handlers."""

    def __init__(self) -> None:
        """Initialise a new handler with no next handler set."""
        self._next_handler: Handler | None = None

    def set_next(self, handler: "Handler") -> "Handler":
        """Set the next handler in the chain.

        Args:
            handler: The handler to be set as the next in the chain.

        Returns:
            The handler that was set as next, allowing for method chaining.

        """
        self._next_handler = handler
        return handler

    def handle(self, message: "Message", credits: Decimal) -> Decimal:
        """Process the message and pass to next handler if it exists.

        Args:
            message: The message to be processed.
            credits: The current credit amount.

        Returns:
            The updated credit amount after processing through this handler
                and any subsequent handlers in the chain.

        """
        result = self.process(message, credits)

        if self._next_handler:
            return self._next_handler.handle(message, result)

        return result

    @abstractmethod
    def process(self, message: "Message", credits: Decimal) -> Decimal:
        """Process the message and return updated credits.

        Args:
            message: The message to be processed.
            credits: The current credit amount.

        Returns:
            The updated credit amount after processing through this handler.

        Raises:
            NotImplementedError: If the subclass does not implement this method.

        """


class BaseCostHandler(Handler):
    """Handles the base cost of 1 credit."""

    BASE_COST = Decimal("1.0")

    def process(self, _: "Message", credits: Decimal) -> Decimal:
        """Add the base cost to the credits.

        Args:
            _: Unused message parameter.
            credits: The current credit amount.

        Returns:
            The credits increased by the base cost.

        """
        return credits + self.BASE_COST


class CharacterCountHandler(Handler):
    """Handles the 0.05 credits per character rule."""

    CHARACTER_CREDIT = Decimal("0.05")

    def process(self, message: "Message", credits: Decimal) -> Decimal:
        """Calculate credits based on character count.

        Args:
            message: The message containing the text to analyze.
            credits: The current credit amount.

        Returns:
            The credits increased by the character credit for each character.

        """
        return credits + (self.CHARACTER_CREDIT * Decimal(str(len(message.text))))


class WordLengthHandler(Handler):
    """Handles credit calculation based on word lengths."""

    SHORT_WORD_LENGTH = 3
    MEDIUM_WORD_LENGTH = 7
    SHORT_WORD_CREDIT = Decimal("0.1")
    MEDIUM_WORD_CREDIT = Decimal("0.2")
    LONG_WORD_CREDIT = Decimal("0.3")

    def process(self, message: "Message", credits: Decimal) -> Decimal:
        """Calculate credits based on word lengths.

        Args:
            message: The message containing the text to analyze.
            credits: The current credit amount.

        Returns:
            The credits increased based on the length of each word.

        """
        # Assumption: Words with mixed alphanumeric characters (e.g. "COVID-19",
        # "Version2.0") are counted as single words with their full length if
        # they contain at least one letter.
        words = [
            word
            for word in message.text.split()
            if any(character.isalpha() for character in word)
        ]

        for word in words:
            word_length = len(word)
            if word_length <= self.SHORT_WORD_LENGTH:
                credits += self.SHORT_WORD_CREDIT
            elif word_length <= self.MEDIUM_WORD_LENGTH:
                credits += self.MEDIUM_WORD_CREDIT
            else:
                credits += self.LONG_WORD_CREDIT

        return credits


class ThirdVowelsHandler(Handler):
    """Handles credit calculation for vowels in every third position."""

    VOWEL_CREDIT = Decimal("0.3")
    VOWELS: ClassVar[set[str]] = set("aeiouAEIOU")

    def process(self, message: "Message", credits: Decimal) -> Decimal:
        """Calculate credits based on vowels in third positions.

        Args:
            message: The message containing the text to analyze.
            credits: The current credit amount.

        Returns:
            The credits increased by 0.3 for each vowel in a third position.

        """
        third_characters = message.text[2::3]
        vowel_count = sum(
            1 for character in third_characters if character in self.VOWELS
        )
        return credits + (self.VOWEL_CREDIT * Decimal(str(vowel_count)))


class LengthPenaltyHandler(Handler):
    """Handles the length penalty for messages over 100 characters."""

    MAX_LENGTH_WITHOUT_PENALTY = 100
    LENGTH_PENALTY = Decimal("5.0")

    def process(self, message: "Message", credits: Decimal) -> Decimal:
        """Apply length penalty if applicable.

        Args:
            message: The message containing the text to analyze.
            credits: The current credit amount.

        Returns:
            The credits increased by the length penalty if the message is over
                the maximum length without penalty.

        """
        if len(message.text) > self.MAX_LENGTH_WITHOUT_PENALTY:
            credits += self.LENGTH_PENALTY
        return credits


class UniqueWordBonusHandler(Handler):
    """Handles the unique word bonus calculation."""

    UNIQUE_WORD_DISCOUNT = Decimal("2.0")
    MINIMUM_CREDITS = Decimal("1.0")

    def process(self, message: "Message", credits: Decimal) -> Decimal:
        """Apply unique word bonus if applicable.

        Args:
            message: The message containing the text to analyze.
            credits: The current credit amount.

        Returns:
            The credits decreased by the unique word discount if all words are
                unique, with a minimum value of the minimum credits constant.

        """
        words = [
            word
            for word in message.text.split()
            if any(character.isalpha() for character in word)
        ]

        if len(words) == len(set(words)):
            credits -= self.UNIQUE_WORD_DISCOUNT

        return max(self.MINIMUM_CREDITS, credits)


class PalindromeHandler(Handler):
    """Handles palindrome detection and credit doubling."""

    PALINDROME_MULTIPLIER = Decimal("2.0")

    def _is_palindrome(self, text: str) -> bool:
        """Check if the given text is a palindrome.

        Args:
            text: The text to check.

        Returns:
            bool: True if the text is a palindrome, False otherwise.

        """
        cleaned = "".join(
            character.lower() for character in text if character.isalnum()
        )
        return cleaned == cleaned[::-1]

    def process(self, message: "Message", credits: Decimal) -> Decimal:
        """Double credits if message is a palindrome.

        Args:
            message: The message containing the text to analyze.
            credits: The current credit amount.

        Returns:
            The credits doubled if the message is a palindrome.

        """
        if self._is_palindrome(message.text):
            credits *= self.PALINDROME_MULTIPLIER
        return credits


class Calculator:
    """Calculate message credits based on various text characteristics."""

    def __init__(self) -> None:
        """Initialise the Calculator with a chain of handlers.

        Creates and links all handlers in the specified order to form
        a processing chain for credit calculation.
        """
        # Using Chain of Responsibility here for modularity, easy rule
        # addition, and clear debugging.
        base_cost = BaseCostHandler()
        character_count = CharacterCountHandler()
        word_length = WordLengthHandler()
        third_vowels = ThirdVowelsHandler()
        length_penalty = LengthPenaltyHandler()
        unique_bonus = UniqueWordBonusHandler()
        palindrome = PalindromeHandler()

        base_cost.set_next(character_count).set_next(word_length).set_next(
            third_vowels
        ).set_next(length_penalty).set_next(unique_bonus).set_next(palindrome)

        self.handler = base_cost

    def calculate(
        self, message: "Message", report: Optional["Report"] = None
    ) -> Decimal:
        """Calculate the total credits for a given message.

        Args:
            message: The message object to calculate credits for.
            report: Optional pre-calculated report containing
                credit cost. Defaults to None.

        Returns:
            The total calculated credits for the message rounded to 1 decimal place.

        Note:
            If a report is provided, the calculation chain is skipped and
            the report's credit_cost is returned directly.

        """
        if report is not None:
            return report.credit_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        calculated_credits = self.handler.handle(message, Decimal("0.0"))
        return calculated_credits.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
