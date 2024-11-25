from decimal import Decimal
from unittest import TestCase
from unittest.mock import Mock, patch

from src.utils.calculator import (
    BaseCostHandler,
    Calculator,
    CharacterCountHandler,
    LengthPenaltyHandler,
    PalindromeHandler,
    ThirdVowelsHandler,
    UniqueWordBonusHandler,
    WordLengthHandler,
)


class TestBaseCostHandler(TestCase):
    def setUp(self) -> None:
        self.handler = BaseCostHandler()
        self.message = Mock()
        self.message.text = "test message"

    def test_should_add_one_credit_to_initial_value(self) -> None:
        result = self.handler.process(self.message, Decimal("0.0"))
        assert result == Decimal("1.0")

    def test_should_properly_chain_to_next_handler(self) -> None:
        next_handler = Mock()
        next_handler.handle.return_value = Decimal("2.0")
        self.handler.set_next(next_handler)

        result = self.handler.handle(self.message, Decimal("0.0"))
        assert result == Decimal("2.0")
        next_handler.handle.assert_called_once_with(self.message, Decimal("1.0"))


class TestCharacterCountHandler(TestCase):
    def setUp(self) -> None:
        self.handler = CharacterCountHandler()
        self.message = Mock()

    def test_should_return_zero_credits_for_empty_message(self) -> None:
        self.message.text = ""
        result = self.handler.process(self.message, Decimal("0.0"))
        assert result == Decimal("0.0")

    def test_should_add_point_zero_five_credits_per_character(self) -> None:
        self.message.text = "test"
        result = self.handler.process(self.message, Decimal("0.0"))
        assert result == Decimal("0.2")

    def test_should_count_spaces_in_character_calculation(self) -> None:
        self.message.text = "test message"
        result = self.handler.process(self.message, Decimal("0.0"))
        assert result == Decimal("0.60")


class TestWordLengthHandler(TestCase):
    def setUp(self) -> None:
        self.handler = WordLengthHandler()
        self.message = Mock()

    def test_should_return_zero_credits_for_empty_message(self) -> None:
        self.message.text = ""
        result = self.handler.process(self.message, Decimal("0.0"))
        assert result == Decimal("0.0")

    def test_should_add_point_one_credit_for_words_up_to_three_chars(self) -> None:
        self.message.text = "a an the"
        result = self.handler.process(self.message, Decimal("0.0"))
        assert result == Decimal("0.3")

    def test_should_add_point_two_credits_for_words_four_to_seven_chars(self) -> None:
        self.message.text = "test hello"
        result = self.handler.process(self.message, Decimal("0.0"))
        assert result == Decimal("0.4")

    def test_should_add_point_three_credits_for_words_over_seven_chars(self) -> None:
        self.message.text = "beautiful excellent"
        result = self.handler.process(self.message, Decimal("0.0"))
        assert result == Decimal("0.6")


class TestThirdVowelsHandler(TestCase):
    def setUp(self) -> None:
        self.handler = ThirdVowelsHandler()
        self.message = Mock()

    def test_should_return_zero_credits_for_empty_message(self) -> None:
        self.message.text = ""
        result = self.handler.process(self.message, Decimal("0.0"))
        assert result == Decimal("0.0")

    def test_should_return_zero_credits_when_no_vowels_in_third_positions(self) -> None:
        self.message.text = "xyz"
        result = self.handler.process(self.message, Decimal("0.0"))
        assert result == Decimal("0.0")

    def test_should_add_point_three_credits_per_vowel_in_third_position(self) -> None:
        self.message.text = "abeba"
        result = self.handler.process(self.message, Decimal("0.0"))
        assert result == Decimal("0.3")


class TestLengthPenaltyHandler(TestCase):
    def setUp(self) -> None:
        self.handler = LengthPenaltyHandler()
        self.message = Mock()

    def test_should_not_add_penalty_for_message_under_hundred_chars(self) -> None:
        self.message.text = "short message"
        result = self.handler.process(self.message, Decimal("0.0"))
        assert result == Decimal("0.0")

    def test_should_add_five_credit_penalty_for_message_over_hundred_chars(
        self,
    ) -> None:
        self.message.text = "x" * 101
        result = self.handler.process(self.message, Decimal("0.0"))
        assert result == Decimal("5.0")


class TestUniqueWordBonusHandler(TestCase):
    def setUp(self) -> None:
        self.handler = UniqueWordBonusHandler()
        self.message = Mock()

    def test_should_apply_bonus_for_empty_message(self) -> None:
        self.message.text = ""
        result = self.handler.process(self.message, Decimal("5.0"))
        assert result == Decimal("3.0")

    def test_should_subtract_two_credits_for_all_unique_words(self) -> None:
        self.message.text = "the quick brown fox"
        result = self.handler.process(self.message, Decimal("5.0"))
        assert result == Decimal("3.0")

    def test_should_not_apply_bonus_when_duplicate_words_present(self) -> None:
        self.message.text = "the the quick quick"
        result = self.handler.process(self.message, Decimal("5.0"))
        assert result == Decimal("5.0")


class TestPalindromeHandler(TestCase):
    def setUp(self) -> None:
        self.handler = PalindromeHandler()
        self.message = Mock()

    def test_should_double_credits_for_empty_message(self) -> None:
        self.message.text = ""
        result = self.handler.process(self.message, Decimal("5.0"))
        assert result == Decimal("10.0")

    def test_should_double_credits_for_simple_palindrome(self) -> None:
        self.message.text = "racecar"
        result = self.handler.process(self.message, Decimal("5.0"))
        assert result == Decimal("10.0")

    def test_should_double_credits_for_complex_palindrome_with_spaces(self) -> None:
        self.message.text = "A man a plan a canal Panama"
        result = self.handler.process(self.message, Decimal("5.0"))
        assert result == Decimal("10.0")


class TestCalculator(TestCase):
    def setUp(self) -> None:
        self.calculator = Calculator()
        self.message = Mock()
        self.message.text = "test message"
        self.report = Mock()
        self.report.credit_cost = Decimal("5.0")

    def test_should_return_report_credit_cost_when_report_provided(self) -> None:
        result = self.calculator.calculate(self.message, self.report)
        self.assertEqual(result, Decimal("5.0"))

    @patch.object(BaseCostHandler, "handle")
    def test_should_use_handler_chain_when_no_report_provided(
        self, mock_handle: Mock
    ) -> None:
        expected_result = Decimal("10.0")
        mock_handle.return_value = expected_result

        result = self.calculator.calculate(self.message)

        mock_handle.assert_called_once_with(self.message, Decimal("0.0"))
        self.assertEqual(result, expected_result)

    def test_should_initialize_handler_chain_correctly(self) -> None:
        calculator = Calculator()

        current_handler = calculator.handler
        expected_chain = [
            BaseCostHandler,
            CharacterCountHandler,
            WordLengthHandler,
            ThirdVowelsHandler,
            LengthPenaltyHandler,
            UniqueWordBonusHandler,
            PalindromeHandler,
        ]

        for expected_type in expected_chain:
            self.assertIsInstance(current_handler, expected_type)
            if hasattr(current_handler, "next_handler"):
                current_handler = current_handler.next_handler
            else:
                break

    def test_should_handle_none_message_gracefully(self) -> None:
        with self.assertRaises(AttributeError):
            self.calculator.calculate(None)

    @patch.object(BaseCostHandler, "handle", side_effect=Exception("Handler error"))
    def test_should_propagate_handler_chain_exceptions(self, mock_handle: Mock) -> None:
        with self.assertRaises(Exception) as context:
            self.calculator.calculate(self.message)

        self.assertEqual(str(context.exception), "Handler error")
        mock_handle.assert_called_once()
