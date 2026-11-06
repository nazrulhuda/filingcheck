"""The company list: load it, resolve each ticker to its SEC CIK, and write it back."""

from pathlib import Path
from typing import Any, Literal, Protocol

import yaml
from pydantic import BaseModel, ConfigDict, Field

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

RevenueRule = Literal["standard", "bank"]

HEADER = """\
# The companies FilingCheck covers. Written by `python -m filingcheck.ingest companies`.
#
# cik: the SEC's 10-digit company ID, resolved from the ticker via the SEC's
#      company_tickers.json. Do not edit by hand.
# fiscal_year_end: the month the fiscal year ends, checked against each 10-K's period of report.
# revenue_rule: "standard" (us-gaap Revenues) or "bank" (net revenue, as banks report it).
# financebench: the company appears in the public FinanceBench questions.
# aliases: names people type for the company; used to resolve a name to one company.
# lookalikes: words that name this company and at least one other ("Morgan": JPMorgan Chase
#      and Morgan Stanley); the company check treats such a word on its own as ambiguous.
# segments: segment and product names people ask about; the fact tool returns company
#      totals only, so a question about one of them is turned down by name.
# not_covered (top level): well-known companies outside the dataset, so a question about one
#      of them is rejected by name instead of answered with another company's numbers.

"""


class Company(BaseModel):
    """One company in the dataset."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ticker: str
    name: str
    cik: str | None = Field(default=None, pattern=r"^\d{10}$")
    sector: str
    fiscal_year_end: int = Field(ge=1, le=12)
    revenue_rule: RevenueRule
    financebench: bool
    aliases: list[str]
    lookalikes: list[str] = Field(default_factory=list)
    segments: list[str] = Field(default_factory=list)


class CompanyResolutionError(LookupError):
    """Raised when a ticker cannot be matched to an SEC CIK."""


class JsonGetter(Protocol):
    """Anything that can fetch a URL as JSON, such as `SecClient`."""

    def get_json(self, url: str, refresh: bool = False) -> Any:
        """Return the body of `url` parsed as JSON; `refresh` skips the cache."""
        ...


def pad_cik(value: int | str) -> str:
    """Format a CIK as the 10-digit, zero-padded string the SEC uses in URLs."""
    text = f"{int(value):010d}"
    if len(text) != 10:
        raise ValueError(f"CIK has more than 10 digits: {value}")
    return text


def load_companies(path: Path) -> list[Company]:
    """Read and validate the company list."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [Company.model_validate(item) for item in data["companies"]]


def load_not_covered(path: Path) -> list[str]:
    """The top-level `not_covered` list: well-known companies outside the dataset."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [str(name) for name in data.get("not_covered") or []]


class _Dumper(yaml.SafeDumper):
    """Quotes all-digit text such as CIKs, so no YAML reader turns them into numbers."""


def _represent_str(dumper: yaml.SafeDumper, data: str) -> yaml.ScalarNode:
    style = "'" if data.isdigit() else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_Dumper.add_representer(str, _represent_str)


def _dump(company: Company) -> dict[str, Any]:
    data = company.model_dump()
    for name in ("lookalikes", "segments"):  # hand-written lists; empty ones stay unwritten
        if not data[name]:
            del data[name]
    return data


def save_companies(
    path: Path, companies: list[Company], not_covered: list[str] | None = None
) -> None:
    """Write the company list, with the header that explains each field."""
    document: dict[str, Any] = {}
    if not_covered:
        document["not_covered"] = list(not_covered)
    document["companies"] = [_dump(c) for c in companies]
    body = yaml.dump(
        document,
        Dumper=_Dumper,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=None,
        width=100,
    )
    path.write_text(HEADER + body, encoding="utf-8", newline="\n")


def resolve_ciks(companies: list[Company], tickers: dict[str, Any]) -> list[Company]:
    """Fill in each company's CIK from the SEC ticker list; fail if any is missing."""
    by_ticker = {str(row["ticker"]).upper(): row["cik_str"] for row in tickers.values()}
    missing = [c.ticker for c in companies if c.ticker.upper() not in by_ticker]
    if missing:
        raise CompanyResolutionError(f"not in the SEC ticker list: {', '.join(missing)}")
    return [c.model_copy(update={"cik": pad_cik(by_ticker[c.ticker.upper()])}) for c in companies]


def update_companies_file(path: Path, client: JsonGetter, refresh: bool = False) -> list[Company]:
    """Resolve every ticker in the file to its CIK and write the result back.

    `refresh=True` downloads the SEC ticker list again instead of reading the cached copy.
    """
    not_covered = load_not_covered(path)
    companies = resolve_ciks(load_companies(path), client.get_json(TICKERS_URL, refresh=refresh))
    save_companies(path, companies, not_covered)
    return companies
