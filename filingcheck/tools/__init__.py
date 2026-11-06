"""The agent's three read-only tools, their JSON schemas and one dispatcher.

`run_tool(name, arguments_json, deps)` validates the arguments with the tool's input model,
runs the tool and returns its result as JSON text. A wrong argument, unknown tool or failed
calculation comes back as `{"error": "..."}` for the model to read; nothing is repaired. A
failure inside a tool (the database, the search) is an error result too, never an exception.
"""

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ValidationError

from filingcheck.facts.lookup import FactsSource
from filingcheck.ingest.companies import Company
from filingcheck.ingest.filings import Manifest
from filingcheck.retrieval.models import Retriever
from filingcheck.tools.calculate import CalculateInput, CalculationError, calculate
from filingcheck.tools.financial_fact import GetFinancialFactInput, get_financial_fact
from filingcheck.tools.search_filings import SearchFilingsInput, search_filings

log = logging.getLogger(__name__)


@dataclass
class ToolDeps:
    """What the tools read, and what the checks read.

    The retriever (passages) and the facts source (numbers) for the tools; the company list,
    the not-covered list and the manifest for the checks.
    """

    retriever: Retriever
    facts: FactsSource
    companies: list[Company] | None = None
    not_covered: list[str] = field(default_factory=list)
    manifest: Manifest | None = None


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


class ToolInputError(Exception):
    """A call the tool cannot run (unknown tool, bad JSON, invalid arguments).

    `result` is the JSON text the model gets, the same text `run_tool` returns.
    """

    def __init__(self, result: str) -> None:
        super().__init__(result)
        self.result = result


def validate_call(name: str, arguments_json: str) -> tuple[Tool, BaseModel]:
    """The tool and its validated arguments, or `ToolInputError` with the result for the model."""
    tool = _BY_NAME.get(name)
    if tool is None:
        raise ToolInputError(
            json.dumps({"error": f"unknown tool {name!r}; the tools are {', '.join(TOOL_NAMES)}"})
        )
    try:
        raw = json.loads(arguments_json or "{}")
    except json.JSONDecodeError as exc:
        raise ToolInputError(
            json.dumps({"error": f"the arguments are not valid JSON ({exc.msg})"})
        ) from exc
    if not isinstance(raw, dict):
        raise ToolInputError(json.dumps({"error": "the arguments must be a JSON object"}))
    try:
        arguments = tool.input_model.model_validate(raw)
    except ValidationError as exc:
        raise ToolInputError(json.dumps({"error": _validation_message(exc)})) from exc
    return tool, arguments


def run_validated(tool: Tool, arguments: BaseModel, deps: ToolDeps) -> str:
    """Run a validated call and return its result as JSON text; failures are results too."""
    try:
        result = tool.run(arguments, deps)
    except CalculationError as exc:
        return json.dumps({"error": str(exc)})
    except Exception:  # a database or search failure: the model is told, the run goes on
        # The exception's text can name a host or a table, so it goes to the log only.
        log.exception("tool %s failed", tool.name)
        return json.dumps(
            {"error": f"{tool.name} failed inside the tool; try again or answer without it"}
        )
    return result.model_dump_json()


def run_tool(name: str, arguments_json: str, deps: ToolDeps) -> str:
    """Validate, run and return the result as JSON text; errors are results too."""
    try:
        tool, arguments = validate_call(name, arguments_json)
    except ToolInputError as exc:
        return exc.result
    return run_validated(tool, arguments, deps)


__all__ = [
    "TOOLS",
    "TOOL_NAMES",
    "Tool",
    "ToolDeps",
    "ToolInputError",
    "run_tool",
    "run_validated",
    "tool_schemas",
    "validate_call",
]
