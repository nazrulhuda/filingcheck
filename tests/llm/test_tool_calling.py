"""Tool calling in the chat client, the router and the fake chat (no network)."""

import json
from typing import Any

import httpx
import pytest

from filingcheck.llm import (
    Completion,
    FakeChat,
    IncompleteAnswer,
    ModelRouter,
    OpenAICompatibleChat,
    ToolCall,
    scripted_tool_calls,
)
from tests.llm.test_chat import USAGE, Script

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Exact arithmetic.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    }
]
CALL = {
    "id": "call_1",
    "type": "function",
    "function": {"name": "calculate", "arguments": '{"expression": "1 + 1"}'},
    # Gemini 3's thought signature rides on the tool call and must come back unchanged.
    "extra_content": {"google": {"thought_signature": "c2lnbmF0dXJl"}},
}


def tool_reply(finish: str = "tool_calls", content: Any = None) -> httpx.Response:
    message = {"role": "assistant", "content": content, "tool_calls": [CALL]}
    body = {"choices": [{"index": 0, "message": message, "finish_reason": finish}], "usage": USAGE}
    return httpx.Response(200, json=body)


def client(script: Script, tool_calls: bool = True) -> OpenAICompatibleChat:
    return OpenAICompatibleChat(
        "https://example.test/v1",
        "TEST_KEY",
        "openai/gpt-oss-20b",
        token_limit_param="max_tokens",
        name="openrouter:openai/gpt-oss-20b",
        tool_calls=tool_calls,
        api_key="test-key",
        transport=script.transport,
    )


def test_tools_and_tool_choice_are_sent_in_the_standard_fields() -> None:
    script = Script(tool_reply())
    client(script).complete(
        [{"role": "user", "content": "What is 1 + 1?"}],
        max_tokens=700,
        tools=TOOLS,
        tool_choice="auto",
    )
    body = script.body()
    assert body["tools"] == TOOLS
    assert body["tool_choice"] == "auto"


def test_no_tools_means_no_tool_fields() -> None:
    script = Script(tool_reply(finish="stop", content="2"))
    script.responses = [
        httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"role": "assistant", "content": "2"}, "finish_reason": "stop"}
                ],
                "usage": USAGE,
            },
        )
    ]
    client(script).complete([{"role": "user", "content": "1 + 1?"}], max_tokens=700)
    assert "tools" not in script.body() and "tool_choice" not in script.body()


def test_a_tool_call_reply_carries_the_calls_and_the_message_as_returned() -> None:
    completion = client(Script(tool_reply())).complete(
        [{"role": "user", "content": "What is 1 + 1?"}], max_tokens=700, tools=TOOLS
    )
    assert completion.tool_calls == [
        ToolCall(id="call_1", name="calculate", arguments='{"expression": "1 + 1"}')
    ]
    assert completion.text == ""
    assert completion.finish_reason == "tool_calls"
    # Kept exactly, so the provider's own fields (Gemini's thought signature) go back next turn.
    assert completion.message == {"role": "assistant", "content": None, "tool_calls": [CALL]}


def test_the_tool_result_turn_is_sent_with_the_assistant_message_unchanged() -> None:
    script = Script(
        tool_reply(),
        httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "It is 2."},
                        "finish_reason": "stop",
                    }
                ],
                "usage": USAGE,
            },
        ),
    )
    chat = client(script)
    messages: list[dict[str, Any]] = [{"role": "user", "content": "What is 1 + 1?"}]
    first = chat.complete(messages, max_tokens=700, tools=TOOLS)
    messages += [
        first.message,
        {"role": "tool", "tool_call_id": "call_1", "content": json.dumps({"value": "2"})},
    ]
    final = chat.complete(messages, max_tokens=700, tools=TOOLS)
    assert final.text == "It is 2." and final.tool_calls == []
    sent = script.body(1)["messages"]
    assert sent[1] == {"role": "assistant", "content": None, "tool_calls": [CALL]}
    assert sent[2] == {"role": "tool", "tool_call_id": "call_1", "content": '{"value": "2"}'}


def test_a_tool_call_cut_off_by_the_token_limit_is_incomplete() -> None:
    with pytest.raises(IncompleteAnswer):
        client(Script(tool_reply(finish="length"))).complete(
            [{"role": "user", "content": "x"}], max_tokens=10, tools=TOOLS
        )


def test_tools_are_refused_for_a_model_not_checked_for_tool_calling() -> None:
    with pytest.raises(ValueError, match="tool calling"):
        client(Script(tool_reply()), tool_calls=False).complete(
            [{"role": "user", "content": "x"}], max_tokens=700, tools=TOOLS
        )


def test_the_registry_marks_which_models_were_checked_for_tool_calling() -> None:
    from filingcheck.llm import load_registry

    models = load_registry().models
    assert all(isinstance(m.tool_calls, bool) for m in models.values())


# ---------------------------------------------------------------- the fake chat and the router


def test_the_fake_chat_scripts_tool_calls_then_an_answer() -> None:
    fake = FakeChat(
        [scripted_tool_calls(("calculate", {"expression": "1 + 1"})), "The answer is 2."]
    )
    first = fake.complete([{"role": "user", "content": "1 + 1?"}], max_tokens=700, tools=TOOLS)
    assert [(c.name, json.loads(c.arguments)) for c in first.tool_calls] == [
        ("calculate", {"expression": "1 + 1"})
    ]
    assert first.message["tool_calls"][0]["id"] == first.tool_calls[0].id
    second = fake.complete([], max_tokens=700, tools=TOOLS)
    assert (second.text, second.tool_calls) == ("The answer is 2.", [])
    assert fake.calls[0]["tools"] == TOOLS


def test_the_router_passes_the_tools_on() -> None:
    fake = FakeChat([scripted_tool_calls(("calculate", {"expression": "2 * 3"}))])
    router = ModelRouter(fake, mode="batch")
    completion = router.complete([], max_tokens=700, tools=TOOLS, tool_choice="auto")
    assert isinstance(completion, Completion) and completion.tool_calls[0].name == "calculate"
    assert (fake.calls[0]["tools"], fake.calls[0]["tool_choice"]) == (TOOLS, "auto")


def test_null_fields_are_left_out_of_the_kept_message_because_groq_rejects_them() -> None:
    # OpenRouter returns "refusal": null; Groq answers the next turn with HTTP 400
    # ("property 'refusal' is unsupported") if it is sent back. Real fields stay as returned.
    message = {"role": "assistant", "content": None, "refusal": None, "tool_calls": [CALL]}
    body = {"choices": [{"message": message, "finish_reason": "tool_calls"}], "usage": USAGE}
    completion = client(Script(httpx.Response(200, json=body))).complete(
        [{"role": "user", "content": "x"}], max_tokens=700, tools=TOOLS
    )
    assert completion.message == {"role": "assistant", "content": None, "tool_calls": [CALL]}
