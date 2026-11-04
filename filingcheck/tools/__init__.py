"""The agent's three read-only tools, their JSON schemas and one dispatcher.

`run_tool(name, arguments_json, deps)` validates the arguments with the tool's input model,
runs the tool and returns its result as JSON text. A wrong argument, unknown tool or failed
calculation comes back as `{"error": "..."}` for the model to read; nothing is repaired.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from filingcheck.facts.lookup import FactsSource
from filingcheck.retrieval.models import Retriever
from filingcheck.tools.calculate import CalculateInput, CalculationError, calculate
from filingcheck.tools.financial_fact import GetFinancialFactInput, get_financial_fact
from filingcheck.tools.search_filings import SearchFilingsInput, search_filings


@dataclass
class ToolDeps:
    """What the tools read: the retriever (passages) and the facts source (numbers)."""

    retriever: Retriever
    facts: FactsSource


@dataclass(frozen=True)
class Tool:
    """One tool: its name and description for the model, its input model and how it runs."""

    name: str
    description: str
    input_model: type[BaseModel]
    run: Callable[[Any, ToolDeps], BaseModel]


TOOLS: tuple[Tool, ...] = (
    Tool(
        "search_filings",
        "Search the text of the 10-K filings of 25 large US companies (three fiscal years "
        "each) and return the best-matching passages with their company, fiscal year, Item "
        "and source URL. Use it for questions about what a filing says.",
        SearchFilingsInput,
        lambda args, deps: search_filings(args, deps.retriever),
    ),
    Tool(
        "get_financial_fact",
        "Look up one company-total number (for example revenue or total assets) as reported "
        "in the company's 10-K for one fiscal year, from the filing's own XBRL data. Returns "
        "the value in the unit as filed (dollars, shares or dollars per share), its period, "
        "the statement line and the source, or says why it is unavailable.",
        GetFinancialFactInput,
        lambda args, deps: get_financial_fact(args, deps.facts),
    ),
    Tool(
        "calculate",
        "Exact arithmetic with + - * / and parentheses on plain numbers, for example a "
        "growth rate or a ratio. Use it for any arithmetic instead of computing in your head.",
        CalculateInput,
        lambda args, deps: calculate(args),
    ),
)
TOOL_NAMES: tuple[str, ...] = tuple(tool.name for tool in TOOLS)
_BY_NAME = {tool.name: tool for tool in TOOLS}


def _clean(schema: Any) -> Any:
    """The JSON schema without titles, defaults of null or "anyOf ... null" wrappers.

    An optional argument is simply one that is not required; providers' function schemas
    accept plain types more widely than unions with null.
    """
    if isinstance(schema, list):
        return [_clean(item) for item in schema]
    if not isinstance(schema, dict):
        return schema
    if "anyOf" in schema:
        options = [o for o in schema["anyOf"] if o.get("type") != "null"]
        if len(options) == 1:
            merged = {**options[0], **{k: v for k, v in schema.items() if k != "anyOf"}}
            return _clean(merged)
    cleaned = {}
    for key, value in schema.items():
        if key == "title" or (key == "default" and value is None):
            continue
        if key == "properties":
            cleaned[key] = {name: _clean(prop) for name, prop in value.items()}
        else:
            cleaned[key] = _clean(value)
    return cleaned


def tool_schemas() -> list[dict[str, Any]]:
    """The `tools` list for the chat model: name, description and parameters of each tool."""
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": _clean(tool.input_model.model_json_schema()),
            },
        }
        for tool in TOOLS
    ]


def _validation_message(error: ValidationError) -> str:
    parts = []
    for item in error.errors():
        where = ".".join(str(p) for p in item["loc"]) or "arguments"
        parts.append(f"{where}: {item['msg']}")
    return "invalid arguments: " + "; ".join(parts)


def run_tool(name: str, arguments_json: str, deps: ToolDeps) -> str:
    """Validate, run and return the result as JSON text; errors are results too."""
    tool = _BY_NAME.get(name)
    if tool is None:
        return json.dumps(
            {"error": f"unknown tool {name!r}; the tools are {', '.join(TOOL_NAMES)}"}
        )
    try:
        raw = json.loads(arguments_json or "{}")
    except json.JSONDecodeError as exc:
        return json.dumps({"error": f"the arguments are not valid JSON ({exc.msg})"})
    if not isinstance(raw, dict):
        return json.dumps({"error": "the arguments must be a JSON object"})
    try:
        arguments = tool.input_model.model_validate(raw)
    except ValidationError as exc:
        return json.dumps({"error": _validation_message(exc)})
    try:
        result = tool.run(arguments, deps)
    except CalculationError as exc:
        return json.dumps({"error": str(exc)})
    return result.model_dump_json()


__all__ = ["TOOLS", "TOOL_NAMES", "Tool", "ToolDeps", "run_tool", "tool_schemas"]
