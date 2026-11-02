"""`make examples`: the cached example answers, from a question file that can be swapped."""

import json
from pathlib import Path

from filingcheck.app.examples import load_example_questions, refresh_examples
from filingcheck.app.store import ExampleAnswer, MemoryStore
from filingcheck.llm import FakeChat
from tests.answer.test_baseline import FakeRetriever

QUESTIONS = [
    {"id": "demo-001", "question": "What are Walmart's main risks in Mexico?"},
    {"id": "demo-002", "question": "Who audits Apple?"},
]


def refresh(store: MemoryStore, model: FakeChat, degraded: bool = False) -> tuple[int, str]:
    printed: list[str] = []
    code = refresh_examples(
        QUESTIONS,
        retriever=FakeRetriever(degraded=degraded),
        model=model,
        store=store,
        out=printed.append,
    )
    return code, "\n".join(printed)


def test_the_examples_replace_the_cached_answers() -> None:
    old = ExampleAnswer(question="Old question?", answer={"text": "old"})
    store = MemoryStore(examples=[old])
    code, _ = refresh(store, FakeChat(["Peso swings [1].", "Deloitte? [2]."]))
    assert code == 0
    saved = store.examples()
    assert [e.question for e in saved] == [q["question"] for q in QUESTIONS]
    assert saved[0].answer["text"] == "Peso swings [1]." and saved[0].answer["citations"]


def test_a_degraded_answer_leaves_the_cached_answers_untouched(tmp_path: Path) -> None:
    old = ExampleAnswer(question="Old question?", answer={"text": "old"})
    store = MemoryStore(examples=[old])
    code, printed = refresh(store, FakeChat(["Peso swings [1]."]), degraded=True)
    assert code == 1 and store.examples() == [old] and "demo-001" in printed


def test_the_question_file_is_read_from_any_path(tmp_path: Path) -> None:
    path = tmp_path / "demo.jsonl"
    path.write_text("".join(json.dumps(q) + "\n\n" for q in QUESTIONS), encoding="utf-8")
    assert load_example_questions(path) == QUESTIONS
