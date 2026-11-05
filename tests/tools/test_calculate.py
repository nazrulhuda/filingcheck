"""calculate: + - * / ( ) and numbers only, exact decimals, never eval."""

from decimal import Decimal

import pytest

from filingcheck.tools.calculate import CalculationError, evaluate


@pytest.mark.parametrize(
    ("expression", "value"),
    [
        ("1 + 2 * 3", "7"),
        ("(1 + 2) * 3", "9"),
        ("10 - 4 - 3", "3"),  # left to right
        ("2 * 3 / 4", "1.5"),
        ("-5 + 2", "-3"),
        ("-(2 + 3) * 2", "-10"),
        ("--4", "4"),
        ("0.1 + 0.2", "0.3"),  # exact, not floating point
        ("(713163 - 680985) / 680985 * 100", "4.725214211766779003942818124"),
        ("416161000000 / 1000000", "416161"),
        ("  7  ", "7"),
    ],
)
def test_arithmetic_with_precedence_and_parentheses(expression: str, value: str) -> None:
    assert evaluate(expression) == Decimal(value)


def test_division_by_zero_is_an_error() -> None:
    with pytest.raises(CalculationError, match="division by zero"):
        evaluate("5 / (2 - 2)")


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "2 ** 3",
        "2 ^ 3",
        "abs(-2)",
        "__import__('os')",
        "x + 1",
        "1e3",
        "(1 + 2",
        "1 + 2)",
        "1 +",
        "3 4",
        "1." + "0" * 300,
    ],
)
def test_anything_else_is_rejected(expression: str) -> None:
    with pytest.raises(CalculationError):
        evaluate(expression)


def test_an_expression_longer_than_200_characters_is_rejected() -> None:
    with pytest.raises(CalculationError, match="200"):
        evaluate("1 + " * 60 + "1")


@pytest.mark.parametrize(
    ("expression", "value"),
    [
        ("713,163,000,000 - 680,985,000,000", "32178000000"),
        (
            "(713,163,000,000 - 680,985,000,000) / 680,985,000,000 * 100",
            "4.725214211766779003942818124",
        ),
        ("1,234.5 * 2", "2469.0"),
    ],
)
def test_us_thousands_separators_are_accepted(expression: str, value: str) -> None:
    assert evaluate(expression) == Decimal(value)


@pytest.mark.parametrize("expression", ["1,23 + 1", "12,3456 + 1", ",123 + 1", "1,234,56"])
def test_digits_not_in_groups_of_three_are_rejected(expression: str) -> None:
    with pytest.raises(CalculationError):
        evaluate(expression)
