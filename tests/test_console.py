"""Terminal output is UTF-8 whatever the platform's default encoding is."""

import io
import sys

import pytest

from filingcheck.answer.baseline import answer_question
from filingcheck.answer.run import format_answer
from filingcheck.console import use_utf8_output
from filingcheck.llm import FakeChat
from tests.answer.test_baseline import FakeRetriever

NON_BREAKING_HYPHEN = chr(0x2011)


def test_a_cp1252_stream_prints_an_answer_with_a_non_breaking_hyphen() -> None:
    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="cp1252")
    use_utf8_output(stream)
    text = f"Walmart{NON_BREAKING_HYPHEN}Mexico faces peso risk [1]."
    answer = answer_question("Q?", retriever=FakeRetriever(), model=FakeChat([text]))
    print(format_answer(answer, None), file=stream)
    stream.flush()
    assert text in raw.getvalue().decode("utf-8")


def test_a_stream_without_reconfigure_is_skipped() -> None:
    stream = io.StringIO()
    use_utf8_output(stream)
    print(NON_BREAKING_HYPHEN, file=stream)
    assert stream.getvalue() == NON_BREAKING_HYPHEN + "\n"


def test_with_no_streams_given_stdout_and_stderr_are_used(monkeypatch: pytest.MonkeyPatch) -> None:
    out = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    err = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)
    use_utf8_output()
    assert (out.encoding, err.encoding) == ("utf-8", "utf-8")
