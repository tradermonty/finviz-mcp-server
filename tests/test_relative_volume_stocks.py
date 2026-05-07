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
    # Volume of exactly 0 must render as a numeric value, not "N/A".
    # The row format separates fields by whitespace, so the volume column
    # surfaces as a bare " 0 " between the % and the relvol "x" field.
    flat_row = text.split("FLAT", 1)[1].split("\n", 1)[0]
    assert " 0 " in flat_row, f"volume 0 not rendered as numeric in row: {flat_row!r}"
    assert "1.50x" in text
    assert "N/A" not in text
