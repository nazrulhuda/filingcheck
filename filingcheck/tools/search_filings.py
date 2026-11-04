"""`search_filings`: passages from the 10-K text, through the hybrid retriever."""

from pydantic import BaseModel, ConfigDict, Field

from filingcheck.answer.baseline import passage_header
from filingcheck.retrieval.models import Retriever
from filingcheck.tools.inputs import Item, Ticker


class SearchFilingsInput(BaseModel):
    """Search the 10-K text of the pinned filings."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=3, max_length=500, description="What to look for, in words.")
    ticker: Ticker | None = Field(
        default=None, description="Only this company's filings (its ticker)."
    )
    fiscal_year: int | None = Field(
        default=None, description="Only this fiscal year's 10-K (the company's own fiscal year)."
    )
    items: list[Item] | None = Field(
        default=None,
        description=(
            'Only these 10-K Items: "1" business, "1A" risk factors, "7" MD&A, "7A" market '
            'risk, "8" financial statements and notes ("1-7A" is used by some banks).'
        ),
    )
    k: int = Field(default=8, ge=1, le=10, description="How many passages to return (1 to 10).")


class Passage(BaseModel):
    """One passage, with where it comes from."""

    chunk_id: int
    header: str  # for example "WMT, fiscal year 2025 (ended 2025-01-31), Item 1A"
    ticker: str
    fiscal_year: int
    item: str
    text: str
    source_url: str


class SearchFilingsResult(BaseModel):
    """The passages of one search, best first."""

    passages: list[Passage]
    degraded: bool = False  # keyword search stood in because vector search failed


def search_filings(arguments: SearchFilingsInput, retriever: Retriever) -> SearchFilingsResult:
    """Run the tool: the retriever's hits as passages."""
    result = retriever.search(
        arguments.query,
        ticker=arguments.ticker,
        fiscal_year=arguments.fiscal_year,
        items=list(arguments.items) if arguments.items else None,
        k=arguments.k,
    )
    return SearchFilingsResult(
        passages=[
            Passage(
                chunk_id=hit.chunk_id,
                header=passage_header(hit),
                ticker=hit.ticker,
                fiscal_year=hit.fiscal_year,
                item=hit.item,
                text=hit.text,
                source_url=hit.source_url,
            )
            for hit in result.hits
        ],
        degraded=result.degraded,
    )
