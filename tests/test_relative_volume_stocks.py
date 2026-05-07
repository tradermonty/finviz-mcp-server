from unittest.mock import patch

from src.models import StockData
from src.server import get_relative_volume_stocks


def test_relative_volume_output_formats_zero_values():
    stock = StockData(
        ticker="FLAT",
        company_name="Flat Corp",
        sector="Industrials",
        industry="Misc",
        price=10.0,
        price_change=0.0,
        volume=0,
        relative_volume=1.5,
    )

    with patch("src.server.finviz_screener.screen_stocks", return_value=[stock]):
        result = get_relative_volume_stocks(min_relative_volume=1.5)

    text = result[0].text
    assert "FLAT" in text
    assert "$10.00" in text
    assert "0.00%" in text
    assert "1.50x" in text
    assert "N/A" not in text
