"""`calculate`: exact arithmetic on + - * / ( ) and plain numbers, with no eval and no names."""

import re
from decimal import Decimal, DivisionByZero, InvalidOperation, localcontext

from pydantic import BaseModel, ConfigDict, Field

MAX_CHARS = 200
PRECISION = 28  # significant digits, Python's default decimal precision
_TOKEN = re.compile(r"\s*(?:(\d+(?:\.\d+)?|\.\d+)|([-+*/()]))")


class CalculationError(ValueError):
    """The expression is not plain arithmetic, or it divides by zero."""


class CalculateInput(BaseModel):
    """Arithmetic on numbers with + - * / and parentheses."""

    model_config = ConfigDict(extra="forbid")

    expression: str = Field(
        min_length=1,
        max_length=MAX_CHARS,
        description=(
            "Plain arithmetic: numbers (digits with an optional decimal point, no commas or "
            "exponents), + - * / and parentheses. Example: (713163 - 680985) / 680985 * 100"
        ),
    )


class CalculateResult(BaseModel):
    """The exact result of an expression."""

    expression: str
    value: Decimal


def _tokens(expression: str) -> list[str]:
    tokens: list[str] = []
    position = 0
    text = expression.rstrip()
    while position < len(text):
        match = _TOKEN.match(text, position)
        if match is None:
            raise CalculationError(f"not allowed at position {position}: {text[position:][:20]!r}")
        tokens.append(match.group(1) or match.group(2))
        position = match.end()
    if not tokens:
        raise CalculationError("the expression is empty")
    return tokens


class _Parser:
    """expr := term (+|- term)*; term := factor (*|/ factor)*; factor := (+|-) factor | number | ( expr )."""  # noqa: E501

    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.i = 0

    def peek(self) -> str | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self) -> str:
        token = self.peek()
        if token is None:
            raise CalculationError("the expression ends too early")
        self.i += 1
        return token

    def expr(self) -> Decimal:
        value = self.term()
        while self.peek() in ("+", "-"):
            value = value + self.term() if self.take() == "+" else value - self.term()
        return value

    def term(self) -> Decimal:
        value = self.factor()
        while self.peek() in ("*", "/"):
            if self.take() == "*":
                value = value * self.factor()
            else:
                divisor = self.factor()
                if divisor == 0:
                    raise CalculationError("division by zero")
                value = value / divisor
        return value

    def factor(self) -> Decimal:
        token = self.take()
        if token == "-":
            return -self.factor()
        if token == "+":
            return self.factor()
        if token == "(":
            value = self.expr()
            if self.take() != ")":
                raise CalculationError("a parenthesis is not closed")
            return value
        if token in ("*", "/", ")"):
            raise CalculationError(f"unexpected {token!r}")
        return Decimal(token)


def evaluate(expression: str) -> Decimal:
    """The exact value of a plain arithmetic expression (at most 200 characters)."""
    if len(expression) > MAX_CHARS:
        raise CalculationError(f"the expression is longer than {MAX_CHARS} characters")
    parser = _Parser(_tokens(expression))
    try:
        with localcontext() as context:
            context.prec = PRECISION
            value = parser.expr()
    except (DivisionByZero, InvalidOperation) as exc:
        raise CalculationError(f"cannot compute: {type(exc).__name__}") from exc
    if parser.peek() is not None:
        raise CalculationError(f"unexpected {parser.peek()!r} after a complete expression")
    return value


def calculate(arguments: CalculateInput) -> CalculateResult:
    """Run the tool: the exact result, or `CalculationError`."""
    return CalculateResult(expression=arguments.expression, value=evaluate(arguments.expression))
