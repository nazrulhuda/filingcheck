"""The values a tool argument may take: the 25 companies, the saved Items, whole numbers."""

import re
from typing import Annotated, Literal

from pydantic import BeforeValidator, Strict

# The 25 companies of data/companies.yaml (a test keeps the two equal). Written out here
# because the live app's image holds the code but not the data folder.
Ticker = Literal[
    "AAPL",
    "AMZN",
    "AXP",
    "C",
    "COF",
    "COST",
    "GOOGL",
    "GS",
    "IBM",
    "JNJ",
    "JPM",
    "KO",
    "MA",
    "MCO",
    "META",
    "MS",
    "MSFT",
    "NFLX",
    "NKE",
    "NVDA",
    "PFE",
    "SPGI",
    "UNH",
    "VZ",
    "WMT",
]

# Each ticker's official name in data/companies.yaml (a test keeps the two equal), written out
# for the same reason. The model sees only the tickers in the schema's enum, and without the
# names it often fails to map "Coca-Cola" to KO or "Verizon" to VZ and gives up.
TICKER_NAMES: dict[str, str] = {
    "AAPL": "Apple Inc.",
    "AMZN": "Amazon.com, Inc.",
    "AXP": "American Express Company",
    "C": "Citigroup Inc.",
    "COF": "Capital One Financial Corporation",
    "COST": "Costco Wholesale Corporation",
    "GOOGL": "Alphabet Inc.",
    "GS": "The Goldman Sachs Group, Inc.",
    "IBM": "International Business Machines Corporation",
    "JNJ": "Johnson & Johnson",
    "JPM": "JPMorgan Chase & Co.",
    "KO": "The Coca-Cola Company",
    "MA": "Mastercard Incorporated",
    "MCO": "Moody's Corporation",
    "META": "Meta Platforms, Inc.",
    "MS": "Morgan Stanley",
    "MSFT": "Microsoft Corporation",
    "NFLX": "Netflix, Inc.",
    "NKE": "NIKE, Inc.",
    "NVDA": "NVIDIA Corporation",
    "PFE": "Pfizer Inc.",
    "SPGI": "S&P Global Inc.",
    "UNH": "UnitedHealth Group Incorporated",
    "VZ": "Verizon Communications Inc.",
    "WMT": "Walmart Inc.",
}
# The two names people still use that are not the official ones.
EXTRA_NAMES: dict[str, str] = {"GOOGL": "Google", "META": "Facebook"}
# One list for both tools' ticker descriptions: "KO (The Coca-Cola Company); ...". Entries are
# separated by semicolons because some official names contain commas.
COMPANY_LIST = "; ".join(
    f"{ticker} ({name}{', ' + EXTRA_NAMES[ticker] if ticker in EXTRA_NAMES else ''})"
    for ticker, name in TICKER_NAMES.items()
)


_DIGITS = re.compile(r"-?[0-9]+")


def _whole_number_text(value: object) -> object:
    """A whole number written as text ("2025") is the same argument; nothing else is changed."""
    if isinstance(value, str) and _DIGITS.fullmatch(value):
        return int(value)
    return value


# An integer argument: a JSON integer, or the same digits written as text. Everything else
# (2025.0, true, "2025.0", "FY2025", " 2025") is refused with a type error for the model.
WholeNumber = Annotated[int, Strict(), BeforeValidator(_whole_number_text)]
