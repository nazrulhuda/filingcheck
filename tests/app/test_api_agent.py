"""The API's agent mode: the mode parameter, the request log, restarts and the stream."""

from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient

from filingcheck.app.api import Services, create_app
from filingcheck.app.store import MemoryStore
from filingcheck.llm import ChatModel, FakeChat, ProviderUnavailable, scripted_tool_calls
from filingcheck.retrieval import Retriever
from filingcheck.tools import ToolDeps
from tests.agent.test_agent import apple_deps
from tests.answer.test_baseline import FakeRetriever
from tests.app.test_api import QUESTION, WALMART, events, settings

APPLE_Q = "What were Apple's total net sales in fiscal 2025?"
FACT = {"ticker": "AAPL", "fiscal_year": 2025, "metric": "revenue"}


def make_agent(
    baseline: ChatModel, agent_models: list[ChatModel]
) -> tuple[TestClient, MemoryStore]:
    store = MemoryStore(companies=[WALMART])

    @contextmanager
    def retriever() -> Iterator[Retriever]:
        yield FakeRetriever()

    @contextmanager
    def tools() -> Iterator[ToolDeps]:
        yield apple_deps()

    services = Services(
        model=baseline,
        primary_name="fake:chat",
        store=store,
        retriever=retriever,
        settings=settings(),
        model_ready=lambda: True,
        agent_models=agent_models,
        tools=tools,
    )
    return TestClient(create_app(services)), store


def agent_script() -> FakeChat:
    return FakeChat(
        [scripted_tool_calls(("get_financial_fact", FACT)), "Sales were $416,161 million [F1]."]
    )


def test_the_default_mode_is_still_the_baseline() -> None:
    baseline = FakeChat(["Peso swings are a risk [1]."])
    agent = agent_script()
    client, store = make_agent(baseline, [agent])
    body = client.post("/ask", json={"question": QUESTION}).json()
    assert body["text"] == "Peso swings are a risk [1]." and "mode" not in body
    assert agent.calls == []
    assert (store.rows[0].mode, store.rows[0].tool_calls) == ("baseline", None)


def test_agent_mode_answers_with_the_agent_and_logs_its_tool_calls() -> None:
    client, store = make_agent(FakeChat([]), [agent_script()])
    response = client.post("/ask", json={"question": APPLE_Q, "mode": "agent"})
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "agent" and body["text"] == "Sales were $416,161 million [F1]."
    assert body["fact_citations"][0]["value"] == "416161000000"
    assert body["tool_calls"][0]["name"] == "get_financial_fact"
    (row,) = store.rows
    assert row.mode == "agent" and row.error is None
    assert row.tool_calls is not None
    assert [c["name"] for c in row.tool_calls["calls"]] == ["get_financial_fact"]
    assert row.tool_calls["restarts"] == []
    assert (row.prompt_tokens, row.completion_tokens) == (200, 40)  # summed over two calls


def test_a_provider_failure_mid_run_restarts_the_question_with_the_fallback() -> None:
    failing = FakeChat(
        [
            scripted_tool_calls(("get_financial_fact", FACT)),
            ProviderUnavailable("primary down", provider="fake", status=503, code="busy"),
        ]
    )
    fallback = agent_script()
    client, store = make_agent(FakeChat([]), [failing, fallback])
    body = client.post("/ask", json={"question": APPLE_Q, "mode": "agent"}).json()
    assert body["text"] == "Sales were $416,161 million [F1]."
    # The fallback starts again from the beginning: its first call holds only the system
    # prompt and the question, not the primary's tool calls.
    assert [m["role"] for m in fallback.calls[0]["messages"]] == ["system", "user"]
    assert body["restarts"] == ["fake 503 busy"]
    assert store.rows[0].tool_calls is not None and store.rows[0].tool_calls["restarts"] == [
        "fake 503 busy"
    ]


def test_when_every_model_fails_the_agent_answers_503_and_logs_the_code() -> None:
    down = ProviderUnavailable("down", provider="fake", status=503, code="busy")
    client, store = make_agent(FakeChat([]), [FakeChat([down]), FakeChat([down])])
    response = client.post("/ask", json={"question": APPLE_Q, "mode": "agent"})
    assert response.status_code == 503
    assert store.rows[0].error == "fake 503 busy" and store.rows[0].mode == "agent"


def test_the_agent_stream_sends_one_event_per_tool_call_then_only_the_final_text() -> None:
    client, store = make_agent(FakeChat([]), [agent_script()])
    response = client.post("/ask/stream", json={"question": APPLE_Q, "mode": "agent"})
    sent = events(response.text)
    names = [name for name, _ in sent]
    assert names[0] == "tool" and names[-1] == "final"
    tool = sent[0][1]
    assert (tool["name"], tool["status"]) == ("get_financial_fact", "ok")
    assert tool["label"] == "Looking up a reported number"
    text = "".join(data["text"] for name, data in sent if name == "token")
    assert text == "Sales were $416,161 million [F1]."
    assert sent[-1][1]["answer"]["mode"] == "agent"
    assert store.rows[0].mode == "agent"


def test_an_unknown_mode_is_refused() -> None:
    client, _ = make_agent(FakeChat([]), [agent_script()])
    assert client.post("/ask", json={"question": APPLE_Q, "mode": "tools"}).status_code == 422


def test_the_agent_counts_once_toward_the_daily_cap() -> None:
    client, store = make_agent(FakeChat([]), [agent_script(), agent_script()])
    client.post("/ask", json={"question": APPLE_Q, "mode": "agent"})
    assert len(store.rows) == 1  # one question, however many model calls it made
