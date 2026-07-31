"""C1: the news CSV column is ``Url``, not ``URL``.

The parser read ``row.get("URL")``, so every article URL rendered empty in all
three news tools. Pinned against the raw ``news_export.ashx?v=3`` capture.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

from src.finviz_client.news import FinvizNewsClient

FIXTURES = Path(__file__).parent / "fixtures"


def test_url_column_is_parsed_from_the_real_header():
    df = pd.read_csv(FIXTURES / "news_v3_aapl.csv")
    assert "Url" in df.columns  # header sanity: the column really is "Url"
    assert "URL" not in df.columns

    client = FinvizNewsClient(api_key="test-key")
    # Cutoff far in the past so the row is never filtered out by date.
    news = client._parse_news_from_csv(df.iloc[0], "AAPL", datetime(2000, 1, 1))

    assert news is not None
    assert news.url
    assert news.url.startswith("http")
    assert news.url == df.iloc[0]["Url"]


def test_every_fixture_row_yields_a_url():
    df = pd.read_csv(FIXTURES / "news_v3_aapl.csv")
    client = FinvizNewsClient(api_key="test-key")

    parsed = [
        client._parse_news_from_csv(row, "AAPL", datetime(2000, 1, 1))
        for _, row in df.iterrows()
    ]
    parsed = [n for n in parsed if n is not None]

    assert parsed
    assert all(n.url.startswith("http") for n in parsed)
