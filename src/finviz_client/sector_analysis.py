import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from .base import FinvizClient, resolve_sector_code

logger = logging.getLogger(__name__)


class FinvizSectorAnalysisClient(FinvizClient):
    """Finviz groups (sector / industry / country / capitalization) client.

    All group requests go to ``grp_export.ashx`` with an **explicit** column
    list.  ``v=152`` without ``c=`` returns whatever custom layout the account
    happens to have saved, which is not stable across sessions
    (see tests/fixtures/GROUND_TRUTH.md).
    """

    # v=152 is the custom view; c= pins exactly which columns come back.
    GROUPS_VIEW = "152"

    # Verified groups column ids (GROUND_TRUTH.md "Groups export column ids"):
    # 0 No. | 1 Name | 2 Market Cap | 3 P/E | 4 Forward P/E | 10 Dividend Yield
    # 15..20 Performance Week/Month/Quarter/Half Year/Year/Year To Date
    # 21 Analyst Recom | 22 Average Volume | 23 Relative Volume | 24 Change
    # 25 Volume | 26 Stocks
    GROUPS_COLUMN_IDS = "0,1,2,3,4,10,15,16,17,18,19,20,21,22,23,24,25,26"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------
    def _groups_params(self, group: str, **extra: str) -> Dict[str, str]:
        """Build the query parameters for a groups export request."""
        # No `o=` sort token: the groups export already returns rows in name
        # order and no groups-specific sort token has been verified.
        params = {
            "g": group,
            "v": self.GROUPS_VIEW,
            "c": self.GROUPS_COLUMN_IDS,
        }
        params.update(extra)
        return params

    def _fetch_groups(self, group: str, **extra: str) -> List[Dict[str, Any]]:
        """Fetch a groups export and parse every row into a group dict.

        Request-level failures (missing key, transport error, HTML body)
        propagate as ``FinvizAPIError`` from ``_fetch_csv_from_url``; an
        empty list here means Finviz really returned no group rows.
        """
        params = self._groups_params(group, **extra)
        df = self._fetch_csv_from_url(self.GROUPS_EXPORT_URL, params)

        if df.empty:
            logger.info(f"Finviz returned no group rows for g={group}")
            return []

        rows: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            try:
                parsed = self._parse_group_row(row)
                if parsed:
                    rows.append(parsed)
            except Exception as e:  # pragma: no cover - defensive
                logger.warning(f"Failed to parse group row (g={group}): {e}")
                continue
        return rows

    @staticmethod
    def _filter_by_name(
        rows: List[Dict[str, Any]], names: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Keep only rows whose ``name`` matches one of ``names``.

        Matching is case-insensitive and ignores surrounding whitespace so
        ``["technology"]`` matches the exported ``"Technology"``.
        """
        if not names:
            return rows
        wanted = {str(n).strip().lower() for n in names}
        return [r for r in rows if str(r.get("name", "")).strip().lower() in wanted]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_sector_performance(
        self, sectors: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Sector performance (groups export, g=sector).

        Args:
            sectors: Sector names to keep (case-insensitive). None = all.

        Returns:
            List of group dicts (see ``_parse_group_row`` for the shape).
        """
        sector_data = self._filter_by_name(self._fetch_groups("sector"), sectors)
        logger.info(f"Retrieved performance data for {len(sector_data)} sectors")
        return sector_data

    def get_industry_performance(
        self, industries: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Industry performance (groups export, g=industry).

        Args:
            industries: Industry names to keep (case-insensitive). None = all.
        """
        industry_data = self._filter_by_name(self._fetch_groups("industry"), industries)
        logger.info(f"Retrieved performance data for {len(industry_data)} industries")
        return industry_data

    def get_country_performance(
        self, countries: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Country performance (groups export, g=country).

        Args:
            countries: Country names to keep (case-insensitive). None = all.
        """
        country_data = self._filter_by_name(self._fetch_groups("country"), countries)
        logger.info(f"Retrieved performance data for {len(country_data)} countries")
        return country_data

    def get_sector_specific_industry_performance(
        self, sector: str
    ) -> List[Dict[str, Any]]:
        """Industry performance inside one sector (g=industry&sg=<sector>).

        Args:
            sector: Sector name or code, e.g. ``energy`` / ``basic_materials``
                / ``Basic Materials``.
        """
        # セクター名を正規化（Finvizのsgコードは小文字連結）。
        # sg= と f=sec_ は同一のコード語彙なので、base.py の SECTOR_CODES を
        # 唯一の定義として共有する。未知の値は従来どおりそのまま渡す
        # （Finviz側で無視される）。
        sector_code = resolve_sector_code(sector) or sector.lower()

        industry_data = self._fetch_groups("industry", sg=sector_code)
        for industry in industry_data:
            industry["parent_sector"] = sector

        logger.info(
            f"Retrieved performance data for {len(industry_data)} industries "
            f"in {sector} sector"
        )
        return industry_data

    def get_capitalization_performance(self) -> List[Dict[str, Any]]:
        """Market-cap tier performance (groups export, g=capitalization)."""
        cap_data = self._fetch_groups("capitalization")
        logger.info(
            f"Retrieved performance data for {len(cap_data)} capitalization categories"
        )
        return cap_data

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------
    def _parse_group_row(self, row: "pd.Series") -> Optional[Dict[str, Any]]:
        """Convert one groups-export CSV row into a dict.

        The group label column is ``Name`` for every ``g=`` value.  Units
        follow the export (GROUND_TRUTH.md "Units"):

        * ``market_cap`` — **millions of USD**, as exported.
        * ``avg_volume`` — exported in thousands, normalized here to shares
          (same convention as the StockData parser).
        * ``volume`` — raw shares.
        * percent columns (``dividend_yield``, ``change``, ``performance_*``)
          — bare floats, the trailing ``%`` stripped.

        Missing values are ``None``, never 0.
        """
        try:
            name = str(row.get("Name", "")).strip()
            if not name or name.lower() == "nan":
                return None

            avg_volume_k = self._parse_number(row.get("Average Volume"))

            return {
                "name": name,
                # 単位: 百万ドル（Finvizのgroups exportそのまま）
                "market_cap": self._parse_number(row.get("Market Cap")),
                "pe_ratio": self._parse_number(row.get("P/E")),
                "forward_pe": self._parse_number(row.get("Forward P/E")),
                "dividend_yield": self._parse_percent(row.get("Dividend Yield")),
                "change": self._parse_percent(row.get("Change")),
                "performance_1w": self._parse_percent(row.get("Performance (Week)")),
                "performance_1m": self._parse_percent(row.get("Performance (Month)")),
                "performance_3m": self._parse_percent(row.get("Performance (Quarter)")),
                "performance_6m": self._parse_percent(
                    row.get("Performance (Half Year)")
                ),
                "performance_1y": self._parse_percent(row.get("Performance (Year)")),
                "performance_ytd": self._parse_percent(
                    row.get("Performance (Year To Date)")
                ),
                "analyst_recom": self._parse_number(row.get("Analyst Recom")),
                # 千株単位 → 株数に正規化
                "avg_volume": (
                    avg_volume_k * 1000 if avg_volume_k is not None else None
                ),
                "relative_volume": self._parse_number(row.get("Relative Volume")),
                "volume": self._parse_number(row.get("Volume")),
                "stock_count": self._parse_int(row.get("Stocks")),
            }

        except Exception as e:
            logger.warning(f"Failed to parse group data from CSV row: {e}")
            return None

    # ------------------------------------------------------------------
    # Value helpers — all return None for missing data, never a fake 0.
    # ------------------------------------------------------------------
    @staticmethod
    def _is_missing(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, float) and pd.isna(value):
            return True
        return str(value).strip() in ("", "-", "N/A", "nan", "NaN")

    def _parse_number(self, value: Any) -> Optional[float]:
        """Parse a numeric cell to float (commas tolerated)."""
        if self._is_missing(value):
            return None
        try:
            if isinstance(value, (int, float)):
                return float(value)
            return float(str(value).replace(",", "").strip())
        except (ValueError, TypeError):
            return None

    def _parse_percent(self, value: Any) -> Optional[float]:
        """Parse a percent cell ("-0.09%") to a bare float (-0.09)."""
        if self._is_missing(value):
            return None
        try:
            if isinstance(value, (int, float)):
                return float(value)
            return float(str(value).replace("%", "").replace(",", "").strip())
        except (ValueError, TypeError):
            return None

    def _parse_int(self, value: Any) -> Optional[int]:
        """Parse an integer cell (e.g. the ``Stocks`` count)."""
        number = self._parse_number(value)
        return int(number) if number is not None else None
