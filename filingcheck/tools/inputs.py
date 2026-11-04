"""The values a tool argument may take: the 25 companies and the saved Items."""

from typing import Literal

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

# The saved 10-K Items; "1-7A" is the merged section of the banks that map Items to pages.
Item = Literal["1", "1A", "7", "7A", "8", "1-7A"]
ITEMS: tuple[str, ...] = ("1", "1A", "7", "7A", "8", "1-7A")
