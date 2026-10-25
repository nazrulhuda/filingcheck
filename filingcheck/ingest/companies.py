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


class CompanyResolutionError(LookupError):
    """Raised when a ticker cannot be matched to an SEC CIK."""


class JsonGetter(Protocol):
    """Anything that can fetch a URL as JSON, such as `SecClient`."""

    def get_json(self, url: str) -> Any:
        """Return the body of `url` parsed as JSON."""
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


class _Dumper(yaml.SafeDumper):
    """Quotes all-digit text such as CIKs, so no YAML reader turns them into numbers."""


def _represent_str(dumper: yaml.SafeDumper, data: str) -> yaml.ScalarNode:
    style = "'" if data.isdigit() else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_Dumper.add_representer(str, _represent_str)


def save_companies(path: Path, companies: list[Company]) -> None:
    """Write the company list, with the header that explains each field."""
    body = yaml.dump(
        {"companies": [c.model_dump() for c in companies]},
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


def update_companies_file(path: Path, client: JsonGetter) -> list[Company]:
    """Resolve every ticker in the file to its CIK and write the result back."""
    companies = resolve_ciks(load_companies(path), client.get_json(TICKERS_URL))
    save_companies(path, companies)
    return companies
