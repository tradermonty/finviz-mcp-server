import logging
import math
import os
import re
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from zoneinfo import ZoneInfo

import pandas as pd
import requests
from dotenv import load_dotenv

from ..constants import FINVIZ_COMPREHENSIVE_FIELD_MAPPING, FINVIZ_FIELD_ALIASES
from ..models import (
    MARKET_CAP_ALIASES,
    MARKET_CAP_FILTERS,
    StockData,
    resolve_market_cap_code,
)
from ..utils.exceptions import FinvizAPIError
from ..utils.validators import normalize_ticker_param

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

# Finviz is a US market data source: its calendars ("this week", "next 5
# days", earnings-date windows) and its CSV timestamps are all US/Eastern.
# Anything that turns "today" into a filter value must use this zone, or a
# machine in Tokyo asks for tomorrow's window (and one in LA asks for
# yesterday's after 21:00 local).
EASTERN = ZoneInfo("America/New_York")


def eastern_today() -> date:
    """Today's date in US/Eastern - the only "today" Finviz filters mean."""
    return datetime.now(EASTERN).date()


def finviz_date_range(
    days: int, start_offset: int = 1, today: Optional[date] = None
) -> str:
    """Build a verified ``MM-DD-YYYYxMM-DD-YYYY`` earnings-date window.

    Probe-verified grammar (GROUND_TRUTH.md): ``earningsdate_08-03-2026x
    08-14-2026`` returned 1,607 rows, every earnings date inside the window.
    Used wherever a period has no real fixed token - inventing one
    (``earningsdate_nextmonth``) or substituting a shorter one
    (``nextdays5`` for "2 weeks") both mislabel what actually ran.
    """
    base = today or eastern_today()
    start = base + timedelta(days=start_offset)
    end = base + timedelta(days=days)
    return f"{start:%m-%d-%Y}x{end:%m-%d-%Y}"


# The Elite API key travels as an ``auth=`` query parameter, so it shows up in
# any text that echoes a request URL - notably ``requests`` exception messages,
# which FastMCP relays straight to the MCP caller. Everything that interpolates
# a URL or a params dict into a message must go through the helpers below.
_AUTH_IN_URL_RE = re.compile(r"(auth=)[^&\s'\"]+")

_REDACTED = "***"


def redact_auth(value: Any) -> str:
    """Return ``str(value)`` with any ``auth=<key>`` masked."""
    return _AUTH_IN_URL_RE.sub(rf"\1{_REDACTED}", str(value))


def redact_params(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Copy of ``params`` with the ``auth`` value masked (for logging)."""
    if not params:
        return {}
    return {k: (_REDACTED if k == "auth" else v) for k, v in params.items()}


# ---------------------------------------------------------------------------
# Sector name -> Finviz sector code (GROUND_TRUTH.md: lowercase concatenated).
# The stock screener's ``f=sec_<code>`` and the groups export's ``sg=<code>``
# share one code vocabulary (token sets verified identical), so both resolve
# through ``resolve_sector_code`` below and this table is the only place a
# sector code is spelled out.
# ---------------------------------------------------------------------------
SECTOR_CODES: Dict[str, str] = {
    "Basic Materials": "basicmaterials",
    "Communication Services": "communicationservices",
    "Consumer Cyclical": "consumercyclical",
    "Consumer Defensive": "consumerdefensive",
    "Energy": "energy",
    "Financial Services": "financial",
    "Healthcare": "healthcare",
    "Industrials": "industrials",
    "Real Estate": "realestate",
    "Technology": "technology",
    "Utilities": "utilities",
}

# Extra display names that map onto the same codes.
_SECTOR_NAME_SYNONYMS = {
    "financial": "financial",
    "finance": "financial",
    "health care": "healthcare",
}


def _sector_key(name: str) -> str:
    """Normalize a sector name/code for lookup (case/space/underscore free).

    Only separators are folded away - letters and digits are kept as-is, so a
    name carrying stray characters ("Technology™", "Technología") does NOT
    quietly resolve to a real sector. ``validate_sector`` is defined as "what
    this resolves", so leniency here would widen validation too.
    """
    return re.sub(r"[\s_\-./]", "", str(name).lower())


_SECTOR_LOOKUP: Dict[str, str] = {}
for _display, _code in SECTOR_CODES.items():
    _SECTOR_LOOKUP[_sector_key(_display)] = _code
    _SECTOR_LOOKUP[_code] = _code
for _alias, _code in _SECTOR_NAME_SYNONYMS.items():
    _SECTOR_LOOKUP[_sector_key(_alias)] = _code


def resolve_sector_code(sector: str) -> Optional[str]:
    """Return the Finviz ``sec_`` code for a sector name, or ``None``.

    Accepts display names (``"Consumer Cyclical"``), codes
    (``"consumercyclical"``) and snake/space variants, case-insensitively.
    """
    if not sector:
        return None
    return _SECTOR_LOOKUP.get(_sector_key(sector))


def sorted_none_last(items: List[Any], key, reverse: bool = False) -> List[Any]:
    """Sort ``items`` by ``key``, keeping rows whose key is None at the end.

    ``0``/``0.0`` are legitimate readings (a 0.00% expense ratio, a flat
    quarter), so they must never be folded into a ``or 0`` / ``or -999``
    sentinel - that would rank them as if the datum were missing, or rank
    missing data as if it were zero. Unranked rows are appended in their
    original order in both sort directions; a ``(value is None, value)``
    tuple key cannot do that, because ``reverse=True`` would flip the
    None-ness flag too and float the missing rows to the top.
    """
    ranked = [item for item in items if key(item) is not None]
    unranked = [item for item in items if key(item) is None]
    ranked.sort(key=key, reverse=reverse)
    return ranked + unranked


# Finviz renders earnings dates as "M/D/YYYY h:mm:ss AM/PM" (GROUND_TRUTH.md).
# Sorting those as strings puts 5/13 before 5/2 and 12/1 before 2/1, which is
# how the calendar order used to come out wrong (audit B16).
_EARNINGS_DATE_FORMATS = (
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%Y %I:%M %p",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y",
)


def parse_earnings_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse a Finviz earnings-date cell into a datetime (None if unparseable)."""
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    if not text or text in ("-", "N/A"):
        return None
    for fmt in _EARNINGS_DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    logger.warning("Unparseable earnings date %r - sorting it last", value)
    return None


# Raw ``o=`` sort token -> the parsed StockData field that reproduces it, so
# ``screen_stocks_raw`` can verify (and re-apply) the ordering client-side.
RAW_ORDER_FIELDS = {
    "ticker": "ticker",
    "marketcap": "market_cap",
    "change": "price_change",
    "volume": "volume",
    "relvol": "relative_volume",
    "price": "price",
    "perf1w": "performance_1w",
    "perfweek": "performance_1w",
    "perfmonth": "performance_1m",
    "perfytd": "performance_ytd",
    "pe": "pe_ratio",
    "dividendyield": "dividend_yield",
    "epssurprise": "eps_surprise",
    "revenuesurprise": "revenue_surprise",
    "rsi": "rsi",
}


def _first_present(filters: Dict[str, Any], keys) -> Any:
    """First non-None value among ``keys`` (aliases for one Finviz filter)."""
    for key in keys:
        value = filters.get(key)
        if value is not None:
            return value
    return None


# One Finviz filter key <- the internal min/max keys that feed it (aliases
# included). Emitting two tokens for one key silently loses one of them, so
# both bounds always collapse into a single range token.
FUNDAMENTAL_RANGE_KEYS = (
    ("fa_pb", ("pb_min", "pb_ratio_min"), ("pb_max", "pb_ratio_max")),
    ("fa_roe", ("roe_min",), ("roe_max",)),
    ("fa_debteq", ("debt_equity_min",), ("debt_equity_max",)),
    ("fa_payoutratio", ("payout_ratio_min",), ("payout_ratio_max",)),
)


def _finviz_filter_key(token: str) -> str:
    """The Finviz filter key a token belongs to (``fa_pe_u30`` -> ``fa_pe``)."""
    return token.rsplit("_", 1)[0] if "_" in token else token


def _finalize_filter_params(params: Dict[str, str]) -> Dict[str, str]:
    """Trim the ``f=`` string and refuse to send two tokens for one key.

    Finviz keeps only one token per filter key and drops the rest **without
    saying so**, so a query like ``fa_payoutratio_o10,fa_payoutratio_u80``
    silently applies half of what the criteria block claims. That is a bug in
    whichever filter builder produced the dict, and it must fail loudly here
    rather than ship a screen that does not match its own description.
    """
    raw = params.get("f", "")
    tokens = [token for token in raw.split(",") if token]

    seen: Dict[str, str] = {}
    for token in tokens:
        key = _finviz_filter_key(token)
        if key in seen:
            raise ValueError(
                f"Two filters for the same Finviz key {key!r}: "
                f"{seen[key]!r} and {token!r}. Finviz would silently apply only "
                f"one of them - combine the bounds into a single range token."
            )
        seen[key] = token

    if "f" in params:
        params["f"] = ",".join(tokens)
    return params


def _finviz_number(value: Any) -> str:
    """Render a numeric filter threshold the way Finviz spells it.

    Integers lose their ``.0`` (``fa_pe_u30``, not ``fa_pe_u30.0``); decimals
    are kept (``fa_debteq_u0.5`` is probe-verified).
    """
    number = float(value)
    return str(int(number)) if number == int(number) else str(number)


# Every stock-export column id verified in GROUND_TRUTH.md. The list used to
# stop at 128, so Performance (3/5/10 Years), Enterprise Value, EV/EBITDA,
# EV/Sales and the dividend-growth columns never arrived and the fields that
# map to them were permanently None.
SCREENER_COLUMN_IDS = ",".join(str(i) for i in range(150))

# ``o=`` server-side sort tokens. The export endpoint ignores ``ar`` but does
# honor ``o=`` - still, every screener re-sorts client-side before slicing, so
# these are an optimization, not the correctness guarantee (audit B7).
# ``earningsdate`` and ``perf1w`` are probe-verified (GROUND_TRUTH.md).
# Accepted ``earnings_date`` values -> the Finviz token they run as.
# ``None`` means "no fixed token exists": those run as an explicit
# ``MM-DD-YYYYxMM-DD-YYYY`` window of EARNINGS_DATE_WINDOW_DAYS days.
# This table is the single source for ``validate_earnings_date`` too, so the
# validator can never accept a value the converter would drop (audit B23 class).
EARNINGS_DATE_WINDOW_DAYS = {
    "within_2_weeks": 14,
    "next_2_weeks": 14,
    "next_month": 30,
}

EARNINGS_DATE_TOKENS: Dict[str, Optional[str]] = {
    # 内部形式 -> Finviz形式（プレフィックスなし）
    "today": "today",
    "today_before": "todaybefore",
    "today_after": "todayafter",
    "tomorrow": "tomorrow",
    "tomorrow_before": "tomorrowbefore",
    "tomorrow_after": "tomorrowafter",
    "yesterday": "yesterday",
    "yesterday_before": "yesterdaybefore",
    "yesterday_after": "yesterdayafter",
    "next_5_days": "nextdays5",
    "this_week": "thisweek",
    "next_week": "nextweek",
    "prev_week": "prevweek",
    "this_month": "thismonth",
    # 期間だけ広く、対応する固定トークンが無いもの（日付レンジで実行）
    "within_2_weeks": None,
    "next_2_weeks": None,
    "next_month": None,
    # 直接Finviz形式の値もサポート
    "nextweek": "nextweek",
    "todaybefore": "todaybefore",
    "todayafter": "todayafter",
    "tomorrowbefore": "tomorrowbefore",
    "tomorrowafter": "tomorrowafter",
    "yesterdaybefore": "yesterdaybefore",
    "yesterdayafter": "yesterdayafter",
    "nextdays5": "nextdays5",
    "thisweek": "thisweek",
    "prevweek": "prevweek",
    "thismonth": "thismonth",
}

SCREENER_SORT_TOKENS = {
    "eps_growth_yoy": "epsyoy1",
    "eps_growth_this_y": "epsthisy",
    "price_change": "change",
    "relative_volume": "relvol",
    "volume": "volume",
    "performance_1w": "perf1w",
    "market_cap": "marketcap",
    "ticker": "ticker",
    "eps_surprise": "epssurprise",
    "earnings_date": "earningsdate",
}


class FinvizClient:
    """Finviz APIクライアントの基本クラス"""

    BASE_URL = "https://elite.finviz.com"
    EXPORT_URL = f"{BASE_URL}/export.ashx"
    GROUPS_EXPORT_URL = f"{BASE_URL}/grp_export.ashx"
    NEWS_EXPORT_URL = f"{BASE_URL}/news_export.ashx"
    QUOTE_EXPORT_URL = f"{BASE_URL}/quote_export.ashx"

    def __init__(self, api_key: Optional[str] = None):
        """
        初期化

        Args:
            api_key: Finviz Elite API キー（環境変数FINVIZ_API_KEYからも取得可能）
        """
        self.api_key = api_key or os.getenv("FINVIZ_API_KEY")
        self.session = requests.Session()
        self.rate_limit_delay = 1.0  # 1秒のデフォルト遅延

        # ヘッダーの設定
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.session.headers.update(self.headers)

    def _make_request(
        self, url: str, params: Optional[Dict[str, Any]] = None, retries: int = 3
    ) -> requests.Response:
        """
        HTTPリクエストを実行

        Args:
            url: リクエストURL
            params: パラメータ
            retries: リトライ回数

        Returns:
            Response オブジェクト
        """
        # ``t=`` はティッカー（単体またはカンマ区切り）。Finviz はクラス株を
        # ``BRK-B`` と綴るため、ここで一度だけ正規化する。バリデータが
        # ``BRK.B`` 表記も受理する以上（audit E13）、リクエストを組み立てる
        # この 1 箇所で寄せないと "No data found" になる。
        if params and params.get("t"):
            params = dict(params)
            params["t"] = normalize_ticker_param(params["t"])

        for attempt in range(retries):
            try:
                # レート制限対応
                time.sleep(self.rate_limit_delay)

                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()

                logger.debug(f"Request successful: {url}")
                return response

            except requests.exceptions.RequestException as e:
                # requests embeds the full request URL - including
                # ``auth=<API KEY>`` - in its exception text, and FastMCP
                # surfaces the raised message to the caller. Mask it.
                detail = redact_auth(e)
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{retries}): {detail}"
                )
                if attempt == retries - 1:
                    raise FinvizAPIError(
                        f"Finviz request to {url} failed after {retries} "
                        f"attempts: {detail}"
                    ) from e
                time.sleep(2**attempt)  # 指数バックオフ

        raise FinvizAPIError(f"Finviz request to {url} failed: max retries exceeded")

    # ------------------------------------------------------------------
    # Request-level failure policy (GROUND_TRUTH.md house rule 3)
    #
    # A failed request must never look like an empty result set. Missing
    # credentials, transport failures, HTML-instead-of-CSV and unparseable
    # payloads raise ``FinvizAPIError``; only a real header-only CSV yields
    # an empty DataFrame.
    # ------------------------------------------------------------------
    HTML_INSTEAD_OF_CSV_MESSAGE = (
        "Finviz returned HTML instead of CSV - check FINVIZ_API_KEY / "
        "Elite subscription"
    )

    MISSING_API_KEY_MESSAGE = (
        "Finviz API key is required for CSV export - set FINVIZ_API_KEY "
        "(Finviz Elite subscription required)"
    )

    def _require_api_key(self) -> str:
        """Return the Finviz Elite API key or raise ``FinvizAPIError``."""
        api_key = self.api_key or os.getenv("FINVIZ_API_KEY")
        if not api_key:
            raise FinvizAPIError(self.MISSING_API_KEY_MESSAGE)
        return api_key

    def _require_csv_body(self, text: str, url: str) -> None:
        """Reject bodies that cannot be a CSV export.

        A CSV response always starts with its header row, so a body whose
        first non-blank character is ``<`` is markup (Finviz serves an HTML
        login/error page when the key is missing, wrong or not Elite).

        ``str.strip()`` does not remove a UTF-8 BOM, so it is stripped
        explicitly first: a BOM-prefixed error page would otherwise slip
        past this check and be parsed into a bogus one-column DataFrame -
        i.e. the swallow-to-empty bug coming back in disguise.
        """
        stripped = text.strip().lstrip("﻿").strip()

        if not stripped:
            raise FinvizAPIError(
                f"Finviz returned an empty response body from {url} - "
                "expected at least a CSV header row"
            )

        if stripped.startswith("<"):
            raise FinvizAPIError(f"{self.HTML_INSTEAD_OF_CSV_MESSAGE} (url: {url})")

    def _csv_response_to_dataframe(
        self, response: requests.Response, url: str
    ) -> pd.DataFrame:
        """Turn a CSV export response into a DataFrame.

        Raises ``FinvizAPIError`` when the body is not usable CSV. A CSV
        with a header and zero data rows is a legitimate "no matches"
        answer and comes back as an empty DataFrame.
        """
        text = response.text
        self._require_csv_body(text, url)

        from io import StringIO

        try:
            return pd.read_csv(StringIO(text))
        except pd.errors.EmptyDataError as e:
            raise FinvizAPIError(
                f"Finviz returned no CSV header from {url}: {e}"
            ) from e
        except pd.errors.ParserError as e:
            raise FinvizAPIError(
                f"Could not parse the Finviz response from {url} as CSV: {e}"
            ) from e

    def _safe_price_conversion(self, value: Any) -> str:
        """
        価格値をFinviz形式に安全に変換

        Args:
            value: 価格値（int, float, str）

        Returns:
            Finviz価格フィルター用の文字列値
        """
        try:
            if isinstance(value, str):
                # 既にFinviz形式の場合（例：'o5', 'u10'）
                if (
                    value.startswith(("o", "u"))
                    and value[1:].replace(".", "").isdigit()
                ):
                    return value  # Finviz形式はそのまま返す
                # 数値文字列の場合
                try:
                    float_val = float(value)
                    return (
                        str(int(float_val))
                        if float_val == int(float_val)
                        else str(float_val)
                    )
                except ValueError:
                    return str(value)
            elif isinstance(value, (int, float)):
                # 整数の場合は整数で返す、小数の場合は小数で返す
                return str(int(value)) if float(value) == int(value) else str(value)
            else:
                return str(value)
        except (ValueError, TypeError):
            return str(value)

    def _resolve_market_cap(self, market_cap: Any) -> Optional[str]:
        """Resolve a market-cap request to a real ``cap_`` code.

        Raises rather than emitting a token Finviz would ignore: an unknown
        ``cap_`` token silently returns the whole universe under a
        "market cap: X" heading (audit B5, house rule 1).
        """
        if market_cap is None or market_cap == "":
            return None
        code = resolve_market_cap_code(market_cap)
        if not code:
            raise ValueError(
                f"Unknown market_cap: {market_cap!r}. Valid values: "
                f"{', '.join(sorted(MARKET_CAP_FILTERS))}, an alias "
                f"({', '.join(sorted(MARKET_CAP_ALIASES))}) or a range like '10to20'."
            )
        return code

    def _shares_to_finviz_thousands(self, shares: float, tighten: str) -> int:
        """Convert a share count to Finviz's thousands unit, never loosening.

        Finviz volume tokens (``sh_avgvol_*``, ``sh_curvol_*``) count shares in
        **thousands** (probe-verified: ``sh_avgvol_50000to`` returned only the
        6 mega caps whose ``Average Volume`` column exceeds 50,000, and
        ``sh_curvol_100to200`` returned raw volumes of 119,550 / 163,928).
        Sub-thousand precision is not expressible, so a minimum rounds **up**
        and a maximum rounds **down**: the emitted filter is never weaker than
        the one that was asked for.
        """
        exact = float(shares) / 1000.0
        rounded = math.ceil(exact) if tighten == "min" else math.floor(exact)
        rounded = max(0, int(rounded))
        if rounded != exact:
            logger.info(
                "Volume threshold %s shares is not a whole thousand; using "
                "%dK (rounded %s so the filter is not loosened)",
                shares,
                rounded,
                "up" if tighten == "min" else "down",
            )
        return rounded

    def _convert_volume_to_finviz_format(self, volume_value: Any) -> str:
        """
        出来高の**下限**をFinvizのトークン値に変換（千株単位）

        Args:
            volume_value: 出来高値（生の株数、またはFinviz形式文字列）

        Returns:
            Finviz ``sh_avgvol``/``sh_curvol`` の値部分（例：``'o650'``）

        Note:
            以前はプリセットのバケットに**切り捨て**ていた（650,000株 →
            ``o500``＝50万株以上）ため、利用者の指定より緩いフィルタが
            黙って適用されていた（audit B20）。Eliteは任意の数値を受け付ける
            ことをプローブで確認済み（``sh_curvol_o20000`` は0件、
            ``sh_avgvol_50000to`` は6件）なので、バケット化はやめて指定値を
            そのまま使う。千株未満の端数だけは「緩めない方向」に丸める。
        """
        # 既にFinviz形式の場合はそのまま（呼び出し側が明示的に指定したトークン）
        if isinstance(volume_value, str):
            token = volume_value.strip()
            if token.startswith(("o", "u", "e")) or token in ("", "frange"):
                return token
            if "to" in token:
                return token
            try:
                volume_value = float(token)
            except ValueError:
                raise ValueError(
                    f"Unrecognized volume filter value: {volume_value!r}. Use a "
                    f"share count (e.g. 500000) or a Finviz token (e.g. 'o500')."
                )

        if isinstance(volume_value, bool) or not isinstance(volume_value, (int, float)):
            raise ValueError(f"Unrecognized volume filter value: {volume_value!r}")

        if volume_value < 0:
            raise ValueError(f"Volume threshold cannot be negative: {volume_value}")

        return f"o{self._shares_to_finviz_thousands(volume_value, 'min')}"

    def _range_filter_token(
        self, prefix: str, minimum: Any = None, maximum: Any = None
    ) -> Optional[str]:
        """Build ONE token for a numeric filter key from a min/max pair.

        Grammar (probe-verified per key in GROUND_TRUTH.md): ``_o<N>`` for a
        minimum, ``_u<N>`` for a maximum, ``_<A>to<B>`` when both bounds are
        given. Never two tokens for one key - Finviz keeps only one of them.
        """
        if minimum is None and maximum is None:
            return None

        # A Finviz-shaped string from the caller wins untouched.
        for explicit in (minimum, maximum):
            if isinstance(explicit, str) and (
                explicit.startswith(("o", "u", "e")) or "to" in explicit
            ):
                return f"{prefix}_{explicit}"

        if minimum is not None and maximum is not None:
            return f"{prefix}_{_finviz_number(minimum)}to{_finviz_number(maximum)}"
        if minimum is not None:
            return f"{prefix}_o{_finviz_number(minimum)}"
        return f"{prefix}_u{_finviz_number(maximum)}"

    def _volume_filter_token(
        self, prefix: str, minimum: Any = None, maximum: Any = None
    ) -> Optional[str]:
        """Build one ``sh_avgvol``/``sh_curvol`` token from a min/max pair.

        Only probe-verified grammar is emitted (GROUND_TRUTH.md):
        ``<prefix>_o<N>`` (min), ``<prefix>_<A>to<B>`` (range) and, for a bare
        maximum, the same range form anchored at zero (``<prefix>_0to<N>``) so
        no unverified ``u`` spelling is relied on. ``N`` is in thousands of
        shares.
        """
        if minimum is None and maximum is None:
            return None

        # An explicit Finviz token from the caller wins untouched.
        for explicit in (minimum, maximum):
            if isinstance(explicit, str):
                token = explicit.strip()
                if token.startswith(("o", "u", "e")) or "to" in token:
                    return f"{prefix}_{token}"

        min_k = (
            self._shares_to_finviz_thousands(float(minimum), "min")
            if minimum is not None
            else None
        )
        max_k = (
            self._shares_to_finviz_thousands(float(maximum), "max")
            if maximum is not None
            else None
        )

        if min_k is not None and max_k is not None:
            return f"{prefix}_{min_k}to{max_k}"
        if min_k is not None:
            return f"{prefix}_o{min_k}"
        return f"{prefix}_0to{max_k}"

    def _safe_numeric_conversion(self, value: Any) -> str:
        """
        数値をFinvizフィルター用に安全に変換

        Args:
            value: 数値（int, float, str）

        Returns:
            Finvizフィルター用の文字列値
        """
        try:
            if isinstance(value, str):
                # フィルター文字列の場合（例：'o10', 'u5'）
                if value.startswith(("o", "u", "e")):
                    return value[1:]  # プレフィックスを除去
                # 数値文字列の場合
                try:
                    return str(int(float(value)))
                except ValueError:
                    return str(value)
            elif isinstance(value, (int, float)):
                return str(int(value))
            else:
                return str(value)
        except (ValueError, TypeError):
            return str(value)

    def _clean_numeric_value(self, value: str) -> Optional[Union[float, int]]:
        """
        数値文字列をクリーンアップして数値に変換

        Args:
            value: 文字列値

        Returns:
            数値またはNone
        """
        if not value or value == "-" or value == "N/A":
            return None

        # パーセント記号を削除
        if value.endswith("%"):
            try:
                return float(value[:-1])
            except ValueError:
                return None

        # 通貨記号を削除
        if value.startswith("$"):
            value = value[1:]

        # カンマを削除
        value = value.replace(",", "")

        # 単位を処理 (B = billion, M = million, K = thousand)
        multipliers = {"B": 1e9, "M": 1e6, "K": 1e3}
        for suffix, multiplier in multipliers.items():
            if value.endswith(suffix):
                try:
                    return float(value[:-1]) * multiplier
                except ValueError:
                    return None

        # 普通の数値として処理
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            return None

    def get_stock_data(
        self, ticker: str, fields: Optional[List[str]] = None
    ) -> Optional[StockData]:
        """
        個別銘柄のデータを取得（CSV export使用）

        Args:
            ticker: 銘柄ティッカー
            fields: 取得するフィールドのリスト（Noneの場合は全フィールド）

        Returns:
            StockData オブジェクトまたはNone
        """
        try:
            params = {"t": ticker}

            # CSVから銘柄データを取得
            df = self._fetch_csv_from_url(self.QUOTE_EXPORT_URL, params)

            if df.empty:
                logger.warning(f"No data returned for ticker: {ticker}")
                return None

            # CSVの最初の行からStockDataオブジェクトを作成
            first_row = df.iloc[0]
            stock_data = self._parse_stock_data_from_csv(first_row)

            logger.info(f"Successfully retrieved data for {ticker}")
            return stock_data

        except FinvizAPIError:
            # リクエスト自体の失敗は「データ無し」に変換しない
            raise
        except Exception as e:
            logger.error(f"Error retrieving data for {ticker}: {e}")
            return None

    def screen_stocks(self, filters: Dict[str, Any]) -> List[StockData]:
        """
        株式スクリーニングを実行（CSV export使用）

        Args:
            filters: スクリーニングフィルタ

        Returns:
            StockData オブジェクトのリスト（該当なしの場合は空リスト）

        Raises:
            FinvizAPIError: the request itself failed (see ``_fetch_csv_data``).
                Request failures are never reported as "no stocks found".
        """
        # CSVデータを取得
        df = self._fetch_csv_data(filters)

        if df.empty:
            logger.info("Finviz returned no rows for these filters")
            return []

        # CSVデータからStockDataオブジェクトのリストに変換
        stocks = []
        total_rows = len(df)

        # 大量データの場合は進捗をログ出力
        log_interval = max(1, total_rows // 10) if total_rows > 100 else total_rows

        for idx, (_, row) in enumerate(df.iterrows()):
            # 行単位のパースエラーは1行だけ捨てる（レスポンス全体は返す）
            try:
                stock_data = self._parse_stock_data_from_csv(row)
                stocks.append(stock_data)

                # 進捗ログ（大量データの場合のみ）
                if total_rows > 100 and (idx + 1) % log_interval == 0:
                    logger.info(
                        f"Processing stocks: {idx + 1}/{total_rows} ({((idx + 1)/total_rows*100):.1f}%)"
                    )

            except Exception as e:
                logger.warning(
                    f"Failed to parse stock data from CSV row {idx + 1}: {e}"
                )
                continue

        logger.info(f"Successfully screened {len(stocks)} stocks using CSV export")
        return stocks

    def screen_stocks_raw(
        self,
        filters: str,
        signal: Optional[str] = None,
        order: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> Tuple[List[StockData], int, bool]:
        """
        Screen stocks using raw FinViz filter codes, bypassing _convert_filters_to_finviz().

        Args:
            filters: Pre-validated, normalized comma-separated FinViz filter string
                     (e.g. "cap_small,fa_div_o3,fa_pe_u20").
            signal: Optional FinViz signal (e.g. "ta_topgainers").
            order: Optional sort order (e.g. "-marketcap" for descending market cap).
            max_results: Maximum number of results (1-500). None means no limit.

        Returns:
            ``(rows, total_matches, order_verified)``:

            * ``rows`` - at most ``max_results`` StockData objects.
            * ``total_matches`` - how many rows Finviz actually returned, so
              the caller can say "N of M" instead of implying M == N.
            * ``order_verified`` - True when ``order`` maps to a parsed field
              and the rows were re-sorted here. When it is False the rows are
              in whatever order Finviz sent, which the caller must not
              describe as a ranking: ``ar`` is ignored by this endpoint and an
              unknown ``o=`` token is ignored silently, so slicing an
              unverified order is arbitrary selection (audit B7).

        Raises:
            FinvizAPIError: the request itself failed.
        """
        params = {
            "v": "151",
            "f": filters,
            "c": SCREENER_COLUMN_IDS,
        }

        if signal:
            params["s"] = signal
        if order:
            params["o"] = order

        # NOTE: no ``ar`` - this endpoint ignores it (GROUND_TRUTH.md).
        effective_max = None
        if max_results is not None:
            effective_max = max(1, min(max_results, 500))

        df = self._fetch_csv_from_url(self.EXPORT_URL, params)

        if df.empty:
            logger.info("Finviz returned no rows for these raw filters")
            return [], 0, False

        stocks = []
        for _, row in df.iterrows():
            # 行単位のパースエラーのみここで握る
            try:
                stock_data = self._parse_stock_data_from_csv(row)
                stocks.append(stock_data)
            except Exception as e:
                logger.warning(f"Failed to parse stock data from raw CSV row: {e}")
                continue

        total_matches = len(stocks)

        # Re-sort on parsed values when we can map the requested ``o=`` token
        # to a field, so the cut below keeps the real top N rather than
        # trusting an order we cannot verify.
        order_verified = False
        if order:
            descending = order.startswith("-")
            token = order.lstrip("-")
            field = RAW_ORDER_FIELDS.get(token)
            if field:
                stocks = sorted_none_last(
                    stocks, key=lambda s: getattr(s, field, None), reverse=descending
                )
                order_verified = True
            else:
                logger.info(
                    "order=%s has no client-side equivalent; rows stay in the "
                    "order Finviz returned (unverified)",
                    order,
                )

        if effective_max is not None:
            stocks = stocks[:effective_max]

        logger.info(f"Successfully screened {len(stocks)} stocks using raw filters")
        return stocks, total_matches, order_verified

    def _convert_filters_to_finviz(self, filters: Dict[str, Any]) -> Dict[str, str]:
        """
        内部フィルタ形式をFinviz URLパラメータに変換（強化版）

        Args:
            filters: 内部フィルタ形式

        Returns:
            Finviz URLパラメータ
        """

        params = {
            "v": "151",  # 決算情報を含むビュー
            "o": "-ticker",  # デフォルトソート（後で上書きされる可能性あり）
            # 決算日を含む全カラムを指定（0..149: GROUND_TRUTH.md の検証済みID）
            "c": SCREENER_COLUMN_IDS,
        }

        # ソート条件の処理
        if "sort_by" in filters:
            sort_field = filters["sort_by"]
            sort_order = filters.get("sort_order", "desc")

            if sort_field in SCREENER_SORT_TOKENS:
                finviz_sort_field = SCREENER_SORT_TOKENS[sort_field]
                if sort_order == "desc":
                    params["o"] = f"-{finviz_sort_field}"
                else:
                    params["o"] = finviz_sort_field

        # volume_surge_screenerの場合の特別処理（正しい順序で生成）
        if (
            "market_cap" in filters
            and filters["market_cap"] == "smallover"
            and "relative_volume_min" in filters
            and filters.get("stocks_only") is True
            and filters.get("price_change_min") == 2.0
        ):
            # volume_surge_screener専用の固定順序制御
            filter_parts = []

            # 1. 時価総額フィルタ: cap_smallover
            filter_parts.append("cap_smallover")

            # 2. 株式のみフィルタ: ind_stocksonly
            filter_parts.append("ind_stocksonly")

            # 3. 平均出来高フィルタ: sh_avgvol_o100
            filter_parts.append("sh_avgvol_o100")

            # 4. 価格フィルタ: sh_price_o10
            filter_parts.append("sh_price_o10")

            # 5. 相対出来高フィルタ: sh_relvol_o1.5
            filter_parts.append("sh_relvol_o1.5")

            # 6. 価格変動フィルタ: ta_change_u2
            filter_parts.append("ta_change_u2")

            # 7. 200日移動平均フィルタ: ta_sma200_pa
            filter_parts.append("ta_sma200_pa")

            # 順序通りに結合
            params["f"] = ",".join(filter_parts)

            # 株式のみフィルタ
            if "stocks_only" in filters and filters["stocks_only"]:
                params["ft"] = "4"

            # 価格変動降順ソート（既に上のsort処理で設定済みだが念のため）
            if "sort_by" in filters and filters["sort_by"] == "price_change":
                params["o"] = "-change"

            # 早期return: 汎用処理での重複追加・カンマなし連結を防止
            return _finalize_filter_params(params)

        # earnings_afterhours_screenerの場合の特別処理（正しい順序で生成）
        elif (
            "earnings_date" in filters
            and filters["earnings_date"] in ["today_after", "thisweek"]
            and ("afterhours_change_min" in filters or "price_change_min" in filters)
        ):
            # earnings_afterhours_screener専用の固定順序制御
            filter_parts = []

            # 1. 時間外変動フィルタ: ah_change_u2 または 価格変動フィルタ: ta_change_u2
            if (
                "afterhours_change_min" in filters
                and filters["afterhours_change_min"] is not None
            ):
                ah_change_value = self._safe_numeric_conversion(
                    filters["afterhours_change_min"]
                )
                filter_parts.append(f"ah_change_u{ah_change_value}")
            elif (
                "price_change_min" in filters
                and filters["price_change_min"] is not None
            ):
                price_change_value = self._safe_numeric_conversion(
                    filters["price_change_min"]
                )
                filter_parts.append(f"ta_change_u{price_change_value}")

            # 2. 時価総額フィルタ: cap_smallover
            if "market_cap" in filters and filters["market_cap"]:
                cap_code = self._resolve_market_cap(filters["market_cap"])
                if cap_code:
                    filter_parts.append(f"cap_{cap_code}")

            # 3. 決算発表フィルタ: earningsdate_todayafter or earningsdate_thisweek
            if "earnings_date" in filters:
                if filters["earnings_date"] == "today_after":
                    filter_parts.append("earningsdate_todayafter")
                elif filters["earnings_date"] == "thisweek":
                    filter_parts.append("earningsdate_thisweek")

            # 4. 平均出来高フィルタ: sh_avgvol_o100
            if "avg_volume_min" in filters and filters["avg_volume_min"] is not None:
                volume_value = self._convert_volume_to_finviz_format(
                    filters["avg_volume_min"]
                )
                filter_parts.append(f"sh_avgvol_{volume_value}")

            # 5. 株価フィルタ: sh_price_o10
            if "price_min" in filters and filters["price_min"] is not None:
                price_value = self._safe_price_conversion(filters["price_min"])
                filter_parts.append(f"sh_price_o{price_value}")

            # 順序通りに結合
            params["f"] = ",".join(filter_parts)

            # 株式のみフィルタ
            if "stocks_only" in filters and filters["stocks_only"]:
                params["ft"] = "4"

            # 時間外変動降順ソート
            if "sort_by" in filters and filters["sort_by"] == "afterhours_change":
                params["o"] = "-afterchange"

            # 最大結果件数
            if "max_results" in filters and filters["max_results"]:
                params["ar"] = str(filters["max_results"])

            # 早期return: 汎用処理での重複追加・カンマなし連結を防止
            return _finalize_filter_params(params)

        # earnings_trading_screenerの場合の特別処理（正しい順序で生成）
        elif filters.get("screener_type") == "earnings_trading":
            # earnings_trading_screener専用の正確な順序制御
            filter_parts = []

            # 1. 時価総額フィルタ: cap_<value>
            if "market_cap" in filters and filters["market_cap"]:
                cap_code = self._resolve_market_cap(filters["market_cap"])
                if cap_code:
                    filter_parts.append(f"cap_{cap_code}")

            # 2. 決算発表期間フィルタ: earningsdate_yesterdayafter|todaybefore
            if "earnings_recent" in filters and filters["earnings_recent"]:
                filter_parts.append("earningsdate_yesterdayafter|todaybefore")

            # 3. EPS予想改訂フィルタ: fa_epsrev_ep
            if (
                "earnings_revision_positive" in filters
                and filters["earnings_revision_positive"]
            ):
                filter_parts.append("fa_epsrev_ep")

            # 4. ネットマージンフィルタ: fa_netmargin_3to
            if "net_margin_min" in filters and filters["net_margin_min"] == 3.0:
                filter_parts.append("fa_netmargin_3to")

            # 5. 平均出来高フィルタ: sh_avgvol_o200
            if "avg_volume_min" in filters and filters["avg_volume_min"] == 200000:
                filter_parts.append("sh_avgvol_o200")

            # 6. 株価フィルタ: sh_price_o<value>
            if "price_min" in filters and filters["price_min"] is not None:
                price_min = filters["price_min"]
                price_int = int(price_min) if price_min == int(price_min) else price_min
                filter_parts.append(f"sh_price_o{price_int}")

            # 7. 価格変動上昇フィルタ: ta_change_u
            if "price_change_positive" in filters and filters["price_change_positive"]:
                filter_parts.append("ta_change_u")

            # 8. 4週パフォーマンスフィルタ（4週騰落率が0%以上）: ta_perf_0to-4w
            if (
                "performance_4w_range" in filters
                and filters["performance_4w_range"] == "0_to_negative_4w"
            ):
                filter_parts.append("ta_perf_0to-4w")

            # 9. ボラティリティフィルタ: ta_volatility_1tox
            if "volatility_min" in filters and filters["volatility_min"] == 1.0:
                filter_parts.append("ta_volatility_1tox")

            # 順序通りに結合
            params["f"] = ",".join(filter_parts)

            # 株式のみフィルタ
            if "stocks_only" in filters and filters["stocks_only"]:
                params["ft"] = "4"

            # EPSサプライズ降順ソート
            if "sort_by" in filters and filters["sort_by"] == "eps_surprise":
                params["o"] = "-epssurprise"

            # 最大結果件数
            if "max_results" in filters and filters["max_results"]:
                params["ar"] = str(filters["max_results"])

            # 早期return: 汎用処理での重複追加・カンマなし連結を防止
            return _finalize_filter_params(params)

        # uptrend_screenerの場合の特別処理（正しい順序で生成）
        elif (
            "market_cap" in filters
            and filters["market_cap"] == "microover"
            and "near_52w_high" in filters
        ):
            # uptrend_screener専用の順序制御
            filter_parts = []

            # 1. 時価総額フィルタ
            if "market_cap" in filters and filters["market_cap"]:
                cap_code = self._resolve_market_cap(filters["market_cap"])
                if cap_code:
                    filter_parts.append(f"cap_{cap_code}")

            # 2. 平均出来高フィルタ
            if "avg_volume_min" in filters and filters["avg_volume_min"] is not None:
                volume_value = self._safe_numeric_conversion(filters["avg_volume_min"])
                # Finviz形式での処理分け
                if volume_value.startswith(("o", "u")):
                    filter_parts.append(f"sh_avgvol_{volume_value}")
                else:
                    filter_parts.append(f"sh_avgvol_{volume_value}to")

            # 3. 価格フィルタ
            if "price_min" in filters and filters["price_min"] is not None:
                price_value = self._safe_price_conversion(filters["price_min"])
                # Finviz形式での処理分け
                if price_value.startswith(("o", "u")):
                    filter_parts.append(f"sh_price_{price_value}")
                else:
                    filter_parts.append(f"sh_price_{price_value}to")

            # 4. 52週高値フィルタ
            if "near_52w_high" in filters and filters["near_52w_high"] is not None:
                high_value = self._safe_numeric_conversion(filters["near_52w_high"])
                filter_parts.append(f"ta_highlow52w_a{high_value}h")

            # 5. 4週パフォーマンスフィルタ
            if (
                "performance_4w_positive" in filters
                and filters["performance_4w_positive"]
            ):
                filter_parts.append("ta_perf2_4wup")

            # 6. 20日移動平均フィルタ
            if "sma20_above" in filters and filters["sma20_above"]:
                filter_parts.append("ta_sma20_pa")

            # 7. 200日移動平均フィルタ
            if "sma200_above" in filters and filters["sma200_above"]:
                filter_parts.append("ta_sma200_pa")

            # 8. 50日移動平均線が200日移動平均線上フィルタ
            if "sma50_above_sma200" in filters and filters["sma50_above_sma200"]:
                filter_parts.append("ta_sma50_sa200")

            # 順序通りに結合
            if filter_parts:
                params["f"] = params.get("f", "") + ",".join(filter_parts) + ","

        else:
            # 従来の処理（その他のスクリーナー用）

            # 時価総額フィルタ（プリセット + 数値レンジ対応）
            if "market_cap" in filters and filters["market_cap"]:
                cap_code = self._resolve_market_cap(filters["market_cap"])
                if cap_code:
                    params["f"] = params.get("f", "") + f"cap_{cap_code},"

            # 時価総額レンジフィルタ（min/max指定）
            market_cap_min = filters.get("market_cap_min")
            market_cap_max = filters.get("market_cap_max")

            if market_cap_min is not None or market_cap_max is not None:
                if market_cap_min and market_cap_max:
                    # レンジ指定: cap_10to20 (単位: B)
                    params["f"] = (
                        params.get("f", "") + f"cap_{market_cap_min}to{market_cap_max},"
                    )
                elif market_cap_min:
                    # 下限のみ: cap_10to
                    params["f"] = params.get("f", "") + f"cap_{market_cap_min}to,"

            # 価格フィルタ - Finviz形式完全対応 (sh_price_o5, sh_price_10.5to, sh_price_10.5to20.11)
            price_min = filters.get("price_min")
            price_max = filters.get("price_max")

            if price_min is not None or price_max is not None:
                price_min_val = (
                    self._safe_price_conversion(price_min)
                    if price_min is not None
                    else None
                )
                price_max_val = (
                    self._safe_price_conversion(price_max)
                    if price_max is not None
                    else None
                )

                # Finviz形式での処理分け
                if price_min_val and price_min_val.startswith(("o", "u")):
                    # Finvizプリセット形式 (o5, u10)
                    params["f"] = params.get("f", "") + f"sh_price_{price_min_val},"
                elif price_max_val and price_max_val.startswith(("o", "u")):
                    # Finvizプリセット形式 (o5, u10)
                    params["f"] = params.get("f", "") + f"sh_price_{price_max_val},"
                elif price_min_val and price_max_val:
                    # レンジ指定: sh_price_10.5to20.11
                    params["f"] = (
                        params.get("f", "")
                        + f"sh_price_{price_min_val}to{price_max_val},"
                    )
                elif price_min_val:
                    # 下限のみ: sh_price_o{value} (Finvizでは o<value> が "Over <value>")
                    params["f"] = params.get("f", "") + f"sh_price_o{price_min_val},"
                elif price_max_val:
                    # 上限のみ: sh_price_u{value} (Finvizでは u<value> が "Under <value>")
                    params["f"] = params.get("f", "") + f"sh_price_u{price_max_val},"

            # 当日出来高フィルタ: sh_curvol_*（千株単位）
            #
            # 以前は存在しない ``sh_volume_*`` を生成しており、Finvizは未知の
            # トークンを黙って無視するため min_volume は常に無効だった
            # （audit B1）。実在するのは ``sh_curvol_*`` で、単位は千株
            # （プローブ: ``sh_curvol_100to200`` の Volume は 119,550〜163,928）。
            curvol_token = self._volume_filter_token(
                "sh_curvol",
                minimum=filters.get("volume_min"),
                maximum=filters.get("volume_max"),
            )
            if curvol_token:
                params["f"] = params.get("f", "") + f"{curvol_token},"

            # 平均出来高フィルタ: sh_avgvol_*（千株単位）
            avgvol_token = self._volume_filter_token(
                "sh_avgvol",
                minimum=filters.get("avg_volume_min"),
                maximum=filters.get("avg_volume_max"),
            )
            if avgvol_token:
                params["f"] = params.get("f", "") + f"{avgvol_token},"
            # 相対出来高フィルタ - Finviz形式完全対応
            relative_volume_min = filters.get("relative_volume_min")
            relative_volume_max = filters.get("relative_volume_max")

            if relative_volume_min is not None or relative_volume_max is not None:
                rel_vol_min_val = (
                    self._safe_numeric_conversion(relative_volume_min)
                    if relative_volume_min is not None
                    else None
                )
                rel_vol_max_val = (
                    self._safe_numeric_conversion(relative_volume_max)
                    if relative_volume_max is not None
                    else None
                )

                # Finviz形式での処理分け
                if rel_vol_min_val and rel_vol_min_val.startswith(("o", "u")):
                    # Finvizプリセット形式 (o2, u1.5)
                    params["f"] = params.get("f", "") + f"sh_relvol_{rel_vol_min_val},"
                elif rel_vol_max_val and rel_vol_max_val.startswith(("o", "u")):
                    # Finvizプリセット形式 (o2, u1.5)
                    params["f"] = params.get("f", "") + f"sh_relvol_{rel_vol_max_val},"
                elif rel_vol_min_val and rel_vol_max_val:
                    # レンジ指定: sh_relvol_1.5to3.0
                    params["f"] = (
                        params.get("f", "")
                        + f"sh_relvol_{rel_vol_min_val}to{rel_vol_max_val},"
                    )
                elif rel_vol_min_val:
                    # 下限のみ: sh_relvol_1.5to
                    params["f"] = (
                        params.get("f", "") + f"sh_relvol_{rel_vol_min_val}to,"
                    )
                elif rel_vol_max_val:
                    # 上限のみ: sh_relvol_to2.0
                    params["f"] = (
                        params.get("f", "") + f"sh_relvol_to{rel_vol_max_val},"
                    )

            # 価格変動フィルタ - Finviz形式完全対応
            # 注意: プリセット判定は生入力で行う（_safe_numeric_conversion はプリフィックスを剥がすため）
            price_change_min = filters.get("price_change_min")
            price_change_max = filters.get("price_change_max")

            if price_change_min is not None or price_change_max is not None:
                # 生入力がプリセット形式（'o5', 'u2' など）の場合はそのまま使用
                min_is_preset = isinstance(
                    price_change_min, str
                ) and price_change_min.startswith(("o", "u"))
                max_is_preset = isinstance(
                    price_change_max, str
                ) and price_change_max.startswith(("o", "u"))

                change_min_val = (
                    self._safe_numeric_conversion(price_change_min)
                    if price_change_min is not None
                    else None
                )
                change_max_val = (
                    self._safe_numeric_conversion(price_change_max)
                    if price_change_max is not None
                    else None
                )

                if min_is_preset and change_min_val is not None:
                    # Finvizプリセット形式 (例: 'o5' → ta_change_o5)
                    params["f"] = params.get("f", "") + f"ta_change_{price_change_min},"
                elif max_is_preset and change_max_val is not None:
                    # Finvizプリセット形式
                    params["f"] = params.get("f", "") + f"ta_change_{price_change_max},"
                elif change_min_val and change_max_val:
                    # レンジ指定: ta_change_2to10
                    params["f"] = (
                        params.get("f", "")
                        + f"ta_change_{change_min_val}to{change_max_val},"
                    )
                elif change_min_val:
                    # 下限のみ: ta_change_u<N>（Finvizの"Up N%"プリセット形式に統一）
                    params["f"] = params.get("f", "") + f"ta_change_u{change_min_val},"
                elif change_max_val:
                    # 上限のみ: ta_change_to10
                    params["f"] = params.get("f", "") + f"ta_change_to{change_max_val},"

            # 52週高値からの距離フィルタ
            if "near_52w_high" in filters and filters["near_52w_high"] is not None:
                high_value = self._safe_numeric_conversion(filters["near_52w_high"])
                params["f"] = params.get("f", "") + f"ta_highlow52w_a{high_value}h,"

            # 4週パフォーマンスフィルタ
            if (
                "performance_4w_positive" in filters
                and filters["performance_4w_positive"]
            ):
                params["f"] = params.get("f", "") + "ta_perf2_4wup,"

        # RSIフィルタ - Finviz形式完全対応
        rsi_min = filters.get("rsi_min")
        rsi_max = filters.get("rsi_max")

        if rsi_min is not None or rsi_max is not None:
            rsi_min_val = (
                self._safe_numeric_conversion(rsi_min) if rsi_min is not None else None
            )
            rsi_max_val = (
                self._safe_numeric_conversion(rsi_max) if rsi_max is not None else None
            )

            # Finviz形式での処理分け
            if rsi_min_val and rsi_min_val.startswith(("o", "u")):
                # Finvizプリセット形式 (o30, u70)
                params["f"] = params.get("f", "") + f"ta_rsi_{rsi_min_val},"
            elif rsi_max_val and rsi_max_val.startswith(("o", "u")):
                # Finvizプリセット形式 (o30, u70)
                params["f"] = params.get("f", "") + f"ta_rsi_{rsi_max_val},"
            elif rsi_min_val and rsi_max_val:
                # レンジ指定: ta_rsi_30to70
                params["f"] = (
                    params.get("f", "") + f"ta_rsi_{rsi_min_val}to{rsi_max_val},"
                )
            elif rsi_min_val:
                # 下限のみ: ta_rsi_30to
                params["f"] = params.get("f", "") + f"ta_rsi_{rsi_min_val}to,"
            elif rsi_max_val:
                # 上限のみ: ta_rsi_to70
                params["f"] = params.get("f", "") + f"ta_rsi_to{rsi_max_val},"

        # 移動平均フィルタ（特別処理スクリーナー以外の場合のみ処理）
        if not (
            (
                "market_cap" in filters
                and filters["market_cap"] == "microover"
                and "near_52w_high" in filters
            )
            or (
                "market_cap" in filters
                and filters["market_cap"] == "smallover"
                and "relative_volume_min" in filters
                and filters.get("stocks_only") is True
                and filters.get("price_change_min") == 2.0
            )
        ):
            if "sma20_above" in filters and filters["sma20_above"]:
                params["f"] = params.get("f", "") + "ta_sma20_pa,"
            if "sma50_above" in filters and filters["sma50_above"]:
                params["f"] = params.get("f", "") + "ta_sma50_pa,"
            if "sma200_above" in filters and filters["sma200_above"]:
                params["f"] = params.get("f", "") + "ta_sma200_pa,"
            if "sma50_above_sma200" in filters and filters["sma50_above_sma200"]:
                params["f"] = params.get("f", "") + "ta_sma50_sa200,"
            # 「移動平均線の下」: ``_pb`` (price below) がFinvizの実トークン。
            # 以前はこれらのキーを読む処理が無く、"below" 指定は無フィルタの
            # 全銘柄を返していた（audit B6）。プローブ検証済み: cap_mega に
            # ta_sma20_pb/ta_sma50_pb/ta_sma200_pb を掛けると10銘柄まで絞られ、
            # 3列とも乖離率がすべて負値だった。
            if "sma20_below" in filters and filters["sma20_below"]:
                params["f"] = params.get("f", "") + "ta_sma20_pb,"
            if "sma50_below" in filters and filters["sma50_below"]:
                params["f"] = params.get("f", "") + "ta_sma50_pb,"
            if "sma200_below" in filters and filters["sma200_below"]:
                params["f"] = params.get("f", "") + "ta_sma200_pb,"

        # PEフィルタ - Finviz形式完全対応 (正しいプレフィックス: fa_pe_)
        # ``pe_ratio_max`` は dividend_growth が使う別名。別々に処理すると
        # 同一キー(fa_pe)のトークンが二つ出るため、ここで一本化する。
        pe_min = filters.get("pe_min")
        pe_max = _first_present(filters, ("pe_max", "pe_ratio_max"))

        # 上限のみは probe 検証済みの ``fa_pe_u<N>`` を使う（旧実装の
        # ``fa_pe_to<N>`` は未検証の綴りだった）。
        pe_token = self._range_filter_token("fa_pe", pe_min, pe_max)
        if pe_token:
            params["f"] = params.get("f", "") + f"{pe_token},"

        # 配当利回りフィルタ - Finviz形式完全対応
        dividend_yield_min = filters.get("dividend_yield_min")
        dividend_yield_max = filters.get("dividend_yield_max")

        if dividend_yield_min is not None or dividend_yield_max is not None:
            div_yield_min_val = (
                self._safe_numeric_conversion(dividend_yield_min)
                if dividend_yield_min is not None
                else None
            )
            div_yield_max_val = (
                self._safe_numeric_conversion(dividend_yield_max)
                if dividend_yield_max is not None
                else None
            )

            # Finviz形式での処理分け
            if div_yield_min_val and div_yield_min_val.startswith(("o", "u")):
                # Finvizプリセット形式 (o2, u10)
                params["f"] = params.get("f", "") + f"fa_div_{div_yield_min_val},"
            elif div_yield_max_val and div_yield_max_val.startswith(("o", "u")):
                # Finvizプリセット形式 (o2, u10)
                params["f"] = params.get("f", "") + f"fa_div_{div_yield_max_val},"
            elif div_yield_min_val and div_yield_max_val:
                # レンジ指定: fa_div_2to5
                params["f"] = (
                    params.get("f", "")
                    + f"fa_div_{div_yield_min_val}to{div_yield_max_val},"
                )
            elif div_yield_min_val:
                # 下限のみ: fa_div_2to
                params["f"] = params.get("f", "") + f"fa_div_{div_yield_min_val}to,"
            elif div_yield_max_val:
                # 上限のみ: fa_div_to5
                params["f"] = params.get("f", "") + f"fa_div_to{div_yield_max_val},"

        # セクターフィルタ
        if "sectors" in filters and filters["sectors"]:
            sector_codes = []
            for sector in filters["sectors"]:
                sector_code = self._get_sector_code(sector)
                if not sector_code:
                    # 未知のセクターを黙って捨てると「指定より広い結果」を
                    # 指定どおりと偽ることになる（audit B23）。
                    raise ValueError(
                        f"Unknown sector: {sector!r}. Valid sectors: "
                        f"{', '.join(sorted(SECTOR_CODES))}"
                    )
                sector_codes.append(sector_code)
            if sector_codes:
                params["f"] = params.get("f", "") + f'sec_{"|".join(sector_codes)},'

        # ---------------------------------------------------------------
        # ファンダメンタル系フィルタ（すべてライブプローブで検証済み。
        # 検証結果は tests/fixtures/GROUND_TRUTH.md に記録）。
        # これらのキーは dividend_growth_screener が以前から設定していたが
        # 対応する変換処理が無く、実際には効いていなかった（audit B2）。
        # ---------------------------------------------------------------
        # 一つのFinvizキーには一つのトークンしか送れない。min/max の両方が
        # 指定されたら**レンジ**にまとめる: `fa_payoutratio_o10` と
        # `fa_payoutratio_u80` を並べて送ると Finviz は片方（下限）を捨て、
        # こちらは両方を「適用済み」と表示してしまう（レビュー指摘 #1）。
        for finviz_key, min_keys, max_keys in FUNDAMENTAL_RANGE_KEYS:
            minimum = _first_present(filters, min_keys)
            maximum = _first_present(filters, max_keys)
            token = self._range_filter_token(finviz_key, minimum, maximum)
            if token:
                params["f"] = params.get("f", "") + f"{token},"

        # 「プラス成長」系のブールフラグ（fa_*_pos）。同じFinvizキーに数値
        # 下限が指定されている場合はそちらが厳密なので、フラグは出さない
        # （両方出すと同一キーの二重トークンになる）。
        for key, token, numeric_keys in (
            ("eps_growth_5y_positive", "fa_eps5years_pos", ()),
            ("eps_growth_qoq_positive", "fa_epsqoq_pos", ("eps_growth_qoq_min",)),
            ("eps_growth_yoy_positive", "fa_epsyoy_pos", ()),
            ("sales_growth_5y_positive", "fa_sales5years_pos", ()),
            (
                "sales_growth_qoq_positive",
                "fa_salesqoq_pos",
                ("sales_growth_qoq_min", "revenue_growth_qoq_min"),
            ),
        ):
            if not filters.get(key):
                continue
            overriding = _first_present(filters, numeric_keys)
            if overriding is not None:
                logger.info(
                    "%s is implied by the numeric minimum %s; sending only the "
                    "numeric filter (one token per Finviz key)",
                    token,
                    overriding,
                )
                continue
            params["f"] = params.get("f", "") + f"{token},"

        # 国フィルタ: geo_usa のみ検証済み。他国コードは未検証なので、
        # 黙って無視される可能性のあるトークンを組み立てるのではなく落とす。
        country = filters.get("country")
        if country:
            if _sector_key(country) in ("usa", "us", "unitedstates", "america"):
                params["f"] = params.get("f", "") + "geo_usa,"
            else:
                raise ValueError(
                    f"Unsupported country filter: {country!r}. Only 'USA' "
                    f"(geo_usa) is verified against the live API."
                )

        # 銘柄種別: 株式のみ / ETFのみ（どちらもプローブ検証済み）
        instrument_type = filters.get("instrument_type")
        if instrument_type:
            instrument_tokens = {
                "stock": "ind_stocksonly",
                "stocks": "ind_stocksonly",
                "etf": "ind_exchangetradedfund",
            }
            token = instrument_tokens.get(str(instrument_type).lower())
            if not token:
                raise ValueError(
                    f"Unsupported instrument_type: {instrument_type!r}. "
                    f"Use 'stock' or 'etf'."
                )
            params["f"] = params.get("f", "") + f"{token},"

        # 決算関連フィルタ
        if "earnings_date" in filters and filters["earnings_date"]:
            earnings_date_value = filters["earnings_date"]

            # 日付範囲指定の場合（例：{"start": "2025-06-30", "end": "2025-07-04"}）
            if (
                isinstance(earnings_date_value, dict)
                and "start" in earnings_date_value
                and "end" in earnings_date_value
            ):
                start_date = earnings_date_value["start"]
                end_date = earnings_date_value["end"]
                # Finviz形式: MM-DD-YYYYxMM-DD-YYYY
                start_formatted = self._format_date_for_finviz(start_date)
                end_formatted = self._format_date_for_finviz(end_date)
                if start_formatted and end_formatted:
                    params["f"] = (
                        params.get("f", "")
                        + f"earningsdate_{start_formatted}x{end_formatted},"
                    )

            # 直接の日付範囲文字列の場合（例：「06-30-2025x07-04-2025」）
            elif isinstance(earnings_date_value, str) and "x" in earnings_date_value:
                params["f"] = (
                    params.get("f", "") + f"earningsdate_{earnings_date_value},"
                )

            # 従来の固定期間指定の場合
            else:
                # Finvizの特殊な仕様: 複数のearnings_date値を|で結合する場合、
                # 最初の値だけearningsdate_プレフィックスが付き、残りは値のみ
                earnings_values = EARNINGS_DATE_TOKENS

                # 単一の値の場合
                if (
                    isinstance(earnings_date_value, str)
                    and earnings_date_value in earnings_values
                ):
                    token = earnings_values[earnings_date_value]
                    if token is None:
                        # 固定トークンが存在しない期間は日付レンジで表現する
                        # （"within_2_weeks" を nextdays5 = 5営業日にすり替える
                        # のは、要求より短い期間を要求どおりと偽ること: audit B15）
                        token = finviz_date_range(
                            EARNINGS_DATE_WINDOW_DAYS[earnings_date_value]
                        )
                    params["f"] = params.get("f", "") + f"earningsdate_{token},"
                # リストの場合（複数条件のOR）
                elif isinstance(earnings_date_value, list):
                    valid_values = [
                        earnings_values[v]
                        for v in earnings_date_value
                        if earnings_values.get(v) is not None
                    ]
                    if valid_values:
                        # 最初の値だけearningsdate_プレフィックスを付ける
                        earnings_filter = f"earningsdate_{valid_values[0]}"
                        if len(valid_values) > 1:
                            # 残りの値は|で結合（プレフィックスなし）
                            earnings_filter += "|" + "|".join(valid_values[1:])
                        params["f"] = params.get("f", "") + f"{earnings_filter},"

        # EPS前四半期比成長率フィルタ
        if (
            "eps_growth_qoq_min" in filters
            and filters["eps_growth_qoq_min"] is not None
        ):
            eps_value = self._safe_numeric_conversion(filters["eps_growth_qoq_min"])
            params["f"] = params.get("f", "") + f"fa_epsqoq_o{eps_value},"

        # EPS予想改訂フィルタ
        if "eps_revision_min" in filters and filters["eps_revision_min"] is not None:
            eps_rev_value = self._safe_numeric_conversion(filters["eps_revision_min"])
            params["f"] = params.get("f", "") + f"fa_epsrev_eo{eps_rev_value},"

        # 売上前四半期比成長率フィルタ
        # ``revenue_growth_qoq_min`` は同義の別名（trend_reversion が使う）。
        # 別名を読む処理が無かったため、そちらは黙って無視されていた（audit B5）。
        sales_growth_qoq_min = filters.get(
            "sales_growth_qoq_min", filters.get("revenue_growth_qoq_min")
        )
        if sales_growth_qoq_min is not None:
            sales_value = self._safe_numeric_conversion(sales_growth_qoq_min)
            params["f"] = params.get("f", "") + f"fa_salesqoq_o{sales_value},"

        # earnings_recentフィルタ（決算トレード用）
        if "earnings_recent" in filters and filters["earnings_recent"]:
            # earnings_recent: True → earningsdate_yesterdayafter|todaybefore
            params["f"] = (
                params.get("f", "") + "earningsdate_yesterdayafter|todaybefore,"
            )

        # EPS予想改訂フィルタ（EPS Revision Positive）
        if (
            "earnings_revision_positive" in filters
            and filters["earnings_revision_positive"]
        ):
            params["f"] = params.get("f", "") + "fa_epsrev_ep,"

        # 価格変動上昇フィルタ
        # 注意: 専用パス（earnings_trading 等）は早期returnでここに来ない
        if "price_change_positive" in filters and filters["price_change_positive"]:
            params["f"] = params.get("f", "") + "ta_change_u,"

        # 注意: price_change_min は line 787-815 の汎用パスで一元処理する
        # （プリセット判定は生入力で行うため、そちらの実装を参照）

        # 4週パフォーマンス範囲フィルタ（4週騰落率が0%以上。
        # GROUND_TRUTH.md: `<N>to-<tf>` = 「tf期間の騰落率 >= N%」: audit B19）
        if (
            "performance_4w_range" in filters
            and filters["performance_4w_range"] == "0_to_negative_4w"
        ):
            params["f"] = params.get("f", "") + "ta_perf_0to-4w,"

        # ボラティリティフィルタ
        if "volatility_min" in filters and filters["volatility_min"] is not None:
            volatility_value = self._safe_numeric_conversion(filters["volatility_min"])
            params["f"] = params.get("f", "") + f"ta_volatility_{volatility_value}tox,"

        # 週次パフォーマンスフィルタ
        if "weekly_performance" in filters and filters["weekly_performance"]:
            params["f"] = (
                params.get("f", "") + f'ta_perf_{filters["weekly_performance"]},'
            )

        # 時間外変動フィルタ (afterhours_change_min)
        if (
            "afterhours_change_min" in filters
            and filters["afterhours_change_min"] is not None
        ):
            ah_change_value = self._safe_numeric_conversion(
                filters["afterhours_change_min"]
            )
            params["f"] = params.get("f", "") + f"ah_change_u{ah_change_value},"

        # ETF除外フィルタ。以前はなぜか geo_usa（米国株のみ）を出していた
        # ため、ETFは除外されず地域だけが勝手に絞られていた。
        if filters.get("exclude_etfs") and not filters.get("instrument_type"):
            params["f"] = params.get("f", "") + "ind_stocksonly,"

        return _finalize_filter_params(params)

    def _get_sector_code(self, sector: str) -> Optional[str]:
        """
        セクター名をFinvizコードに変換（唯一の定義は module 冒頭の SECTOR_CODES）

        Args:
            sector: セクター名またはコード

        Returns:
            Finvizセクターコード（未知の場合は None）
        """
        return resolve_sector_code(sector)

    def get_sector_constituent_tickers(self, sector: str, limit: int = 40) -> List[str]:
        """Return the sector's largest constituents by market cap.

        One lightweight screener export (``f=sec_<code>``, ``c=1,2,6``,
        ``o=-marketcap``). ``ar`` is ignored by Finviz (GROUND_TRUTH.md), so
        the cap is applied client-side *after* sorting. The ``Market Cap``
        column is fetched and re-sorted on client-side rather than trusting
        ``o=-marketcap`` blindly: a silently ignored ``o=`` would otherwise
        turn "top 40 by size" into "first 40 in whatever order Finviz felt
        like", which is exactly the failure mode house rule 1 warns about.

        Args:
            sector: Sector display name or Finviz code.
            limit: Maximum number of tickers to return.

        Returns:
            Ticker symbols, largest market cap first.

        Raises:
            ValueError: unknown sector name, or the sector matched no stocks.
            FinvizAPIError: the request itself failed.
        """
        code = resolve_sector_code(sector)
        if not code:
            raise ValueError(
                f"Unknown sector: {sector!r}. Valid sectors: "
                f"{', '.join(sorted(SECTOR_CODES))}"
            )

        params = {
            "v": "151",
            "f": f"sec_{code}",
            "c": "1,2,6",  # Ticker, Company, Market Cap
            "o": "-marketcap",
        }
        df = self._fetch_csv_from_url(self.EXPORT_URL, params)

        if df.empty or "Ticker" not in df.columns:
            raise ValueError(
                f"Finviz returned no constituents for sector {sector!r} "
                f"(f=sec_{code})"
            )

        # Client-side re-sort: only trust the ordering we can verify ourselves.
        # Rows with an unparseable/missing Market Cap sort last rather than
        # being dropped - they are still real constituents.
        if "Market Cap" in df.columns:
            market_cap = pd.to_numeric(df["Market Cap"], errors="coerce")
            if market_cap.notna().any():
                df = df.assign(_market_cap=market_cap).sort_values(
                    "_market_cap", ascending=False, na_position="last", kind="stable"
                )
            else:
                logger.warning(
                    "Market Cap column for sector %s is not numeric - keeping "
                    "the order Finviz returned",
                    sector,
                )

        tickers = [
            str(t).strip()
            for t in df["Ticker"].tolist()
            if not pd.isna(t) and str(t).strip()
        ]
        if not tickers:
            raise ValueError(
                f"Finviz returned no constituents for sector {sector!r} "
                f"(f=sec_{code})"
            )

        return tickers[: max(1, limit)]

    def _format_date_for_finviz(self, date_str: str) -> Optional[str]:
        """
        日付文字列をFinviz形式（MM-DD-YYYY）に変換

        Args:
            date_str: 日付文字列（YYYY-MM-DD、MM-DD-YYYY、MM/DD/YYYY等）

        Returns:
            Finviz形式の日付文字列（MM-DD-YYYY）またはNone
        """
        import re
        from datetime import datetime

        try:
            # 既にFinviz形式（MM-DD-YYYY）の場合
            if re.match(r"^\d{2}-\d{2}-\d{4}$", date_str):
                return date_str

            # ISO形式（YYYY-MM-DD）の場合
            if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                return date_obj.strftime("%m-%d-%Y")

            # スラッシュ区切り（MM/DD/YYYY）の場合
            if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", date_str):
                date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                return date_obj.strftime("%m-%d-%Y")

            # その他の形式もサポート
            for fmt in ["%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime("%m-%d-%Y")
                except ValueError:
                    continue

            logger.warning(f"Unsupported date format: {date_str}")
            return None

        except Exception as e:
            logger.error(f"Error formatting date {date_str}: {e}")
            return None

    def _fetch_csv_data(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        FinvizからCSVデータを取得

        Args:
            filters: スクリーニングフィルタ

        Returns:
            pandas DataFrame (empty only when Finviz returned a header-only CSV)

        Raises:
            FinvizAPIError: missing API key, transport failure, HTML body or
                an unparseable payload. Never converted to an empty result.
        """
        # フィルタをFinviz形式に変換
        finviz_params = self._convert_filters_to_finviz(filters)

        # CSV export用のパラメータを追加
        finviz_params["ft"] = "4"  # CSV形式を指定

        # 結果数制限はここでは行わない。``ar`` はこのエンドポイントでは無視され
        # （GROUND_TRUTH.md）、代わりに行っていたCSVの先頭切り出しは、Finvizの
        # 返却順（既定は逆ティッカー順）のままN件に削ってから呼び出し側が
        # ソートする形になっていた ＝ 「上位N件」ではなく「任意のN件を並べた
        # もの」（audit B7）。件数の絞り込みは各スクリーナーがソート後に行う。
        if filters.get("max_results"):
            logger.debug(
                "max_results=%s is applied client-side after sorting, not by the "
                "export endpoint (ar= is ignored)",
                filters["max_results"],
            )

        # CSV export用のAPIキーパラメータを追加（無い場合はここで失敗させる）
        finviz_params["auth"] = self._require_api_key()

        # CSV データを取得
        logger.info(f"Finviz CSV export URL: {self.EXPORT_URL}")
        # auth はマスクしてからログに出す
        logger.info(f"Finviz CSV export params: {redact_params(finviz_params)}")
        response = self._make_request(self.EXPORT_URL, finviz_params)

        df = self._csv_response_to_dataframe(response, self.EXPORT_URL)

        logger.info(f"Successfully fetched CSV data with {len(df)} rows")
        # デバッグ: CSVのカラムを確認（大量データの場合は省略）
        if len(df) <= 100:
            logger.debug(f"CSV columns: {list(df.columns)}")
            if len(df) > 0:
                logger.debug(f"First row sample: {df.iloc[0].to_dict()}")
        else:
            logger.info(
                f"Large dataset ({len(df)} rows), skipping detailed debug output"
            )

        return df

    def _parse_stock_data_from_csv(self, row: pd.Series) -> StockData:
        """
        CSV行からStockDataオブジェクトを作成

        Args:
            row: pandasのSeries（CSV行データ）

        Returns:
            StockData オブジェクト
        """
        # 基本情報
        ticker = str(row.get("Ticker", ""))
        company = str(row.get("Company", ""))
        sector = str(row.get("Sector", ""))
        industry = str(row.get("Industry", ""))

        # StockDataオブジェクトを作成
        stock_data = StockData(
            ticker=ticker, company_name=company, sector=sector, industry=industry
        )

        # 数値フィールドのマッピング（完全版 - 128カラム対応）
        numeric_fields = {
            # 基本価格・出来高
            "price": "Price",
            "market_cap": "Market Cap",
            "volume": "Volume",
            "avg_volume": "Average Volume",
            "relative_volume": "Relative Volume",
            "price_change": "Change",
            "price_change_percent": "Change",  # パーセント値として処理
            "prev_close": "Prev Close",
            "open_price": "Open",
            "high_price": "High",
            "low_price": "Low",
            "change_from_open": "Change from Open",
            "trades_count": "Trades",
            # 時間外取引データ
            "premarket_price": "After-Hours Close",  # Note: Finviz doesn't separate pre/after
            "premarket_change": "After-Hours Change",
            "premarket_change_percent": "After-Hours Change",  # Same column, processed as %
            "afterhours_price": "After-Hours Close",
            "afterhours_change": "After-Hours Change",
            "afterhours_change_percent": "After-Hours Change",  # Same column, processed as %
            # 市場データ
            "income": "Income",
            "sales": "Sales",
            "book_value_per_share": "Book/sh",
            "cash_per_share": "Cash/sh",
            "dividend": "Dividend",
            "dividend_yield": "Dividend Yield",
            "employees": "Employees",
            # バリュエーション指標
            "pe_ratio": "P/E",
            "forward_pe": "Forward P/E",
            "peg": "PEG",
            "ps_ratio": "P/S",
            "pb_ratio": "P/B",
            "price_to_cash": "P/Cash",
            "price_to_free_cash_flow": "P/Free Cash Flow",
            # 収益性指標
            "eps": "EPS (ttm)",
            # eps_this_y / eps_next_y / eps_past_5y / eps_next_5y /
            # sales_past_5y have no column in any export view: Finviz ships
            # only the *growth* percentages below ("EPS Growth ..."), never a
            # bare EPS level per horizon. The StockData attributes stay None.
            "eps_next_q": "EPS Next Q",  # 次四半期EPS予想（ドル建て、column id 77）
            "eps_growth_this_y": "EPS Growth This Year",
            "eps_growth_next_y": "EPS Growth Next Year",
            "eps_growth_past_5y": "EPS Growth Past 5 Years",
            "eps_growth_next_5y": "EPS Growth Next 5 Years",
            # NOTE: the export also carries "Sales Growth Past 5 Years"
            # (column id 21) but StockData has no attribute for it — the
            # similarly named ``sales_past_5y`` means a sales level, not a
            # growth rate. Add a field before mapping it.
            # 決算関連（重要）
            "eps_surprise": "EPS Surprise",
            "revenue_surprise": "Revenue Surprise",
            "eps_growth_qtr": "EPS Growth Quarter Over Quarter",
            "sales_growth_qtr": "Sales Growth Quarter Over Quarter",
            "sales_qoq_growth": "Sales Growth Quarter Over Quarter",  # 別名
            "eps_qoq_growth": "EPS Growth Quarter Over Quarter",  # 別名
            # eps_estimate / eps_actual / revenue_estimate / revenue_actual:
            # the export has no estimate/actual columns at all (only the
            # realized "EPS Surprise" / "Revenue Surprise" percentages).
            # Those attributes stay None.
            # eps_revision / revenue_revision: kept for forward
            # compatibility, but the Finviz Elite CSV export does not
            # expose these columns under any view (v=151, v=152 verified
            # to return 151 columns with no "Revision" entry). The
            # filter tokens (fa_epsrev_ep, fa_epsrev_eo<X>) still apply
            # server-side; this mapping is a no-op for screener results.
            # See issue #19. Re-enable once Finviz adds the column.
            "eps_revision": "EPS Revision",
            "revenue_revision": "Revenue Revision",
            # パフォーマンス指標（完全版）
            "performance_1min": "Performance (1 Minute)",
            "performance_2min": "Performance (2 Minutes)",
            "performance_3min": "Performance (3 Minutes)",
            "performance_5min": "Performance (5 Minutes)",
            "performance_10min": "Performance (10 Minutes)",
            "performance_15min": "Performance (15 Minutes)",
            "performance_30min": "Performance (30 Minutes)",
            "performance_1h": "Performance (1 Hour)",
            "performance_2h": "Performance (2 Hours)",
            "performance_4h": "Performance (4 Hours)",
            "performance_1w": "Performance (Week)",
            "performance_1m": "Performance (Month)",
            "performance_3m": "Performance (Quarter)",
            "performance_6m": "Performance (Half Year)",
            "performance_ytd": "Performance (YTD)",
            "performance_1y": "Performance (Year)",
            # performance_2y: the export has no 2-year performance column
            # (ids 138-140 jump from 3 to 5 to 10 years). It used to read
            # "Performance (Year)", i.e. 1-year data under a 2-year name;
            # the attribute now stays None rather than lying.
            # Stocks carry "Performance (3 Years)" (column ids 138-140), ETFs
            # carry "Return 3 Year" (121-123). Both are requested now that the
            # column list runs to 149, so take whichever the row has.
            "performance_3y": ("Performance (3 Years)", "Return 3 Year"),
            "performance_5y": ("Performance (5 Years)", "Return 5 Year"),
            "performance_10y": ("Performance (10 Years)", "Return 10 Year"),
            "performance_since_inception": "Return Since Inception",
            # 財務健全性指標
            "debt_to_equity": "Total Debt/Equity",
            "current_ratio": "Current Ratio",
            "quick_ratio": "Quick Ratio",
            "lt_debt_to_equity": "LT Debt/Equity",
            # 収益性マージン
            "gross_margin": "Gross Margin",
            "operating_margin": "Operating Margin",
            "profit_margin": "Profit Margin",
            # ROE・ROA・ROI
            "roe": "Return on Equity",
            "roa": "Return on Assets",
            "roi": "Return on Invested Capital",  # Note: ROI maps to ROIC in Finviz
            "roic": "Return on Invested Capital",
            # 配当関連
            "payout_ratio": "Payout Ratio",
            # 持株構造
            "insider_ownership": "Insider Ownership",
            "insider_transactions": "Insider Transactions",
            "institutional_ownership": "Institutional Ownership",
            "institutional_transactions": "Institutional Transactions",
            "float_short": "Short Float",
            "short_ratio": "Short Ratio",
            "short_interest": "Short Interest",
            "shares_outstanding": "Shares Outstanding",
            "shares_float": "Shares Float",
            "float_percentage": "Float %",
            # テクニカル・ボラティリティ指標
            # No bare "Volatility" column exists; the generic attribute is
            # fed from the weekly figure, matching models.FINVIZ_FIELD_MAPPING.
            "volatility": "Volatility (Week)",
            "volatility_week": "Volatility (Week)",
            "volatility_month": "Volatility (Month)",
            "beta": "Beta",
            "atr": "Average True Range",
            "rsi": "Relative Strength Index (14)",
            "rsi_14": "Relative Strength Index (14)",
            "rel_volume": "Relative Volume",
            "avg_true_range": "Average True Range",
            # 移動平均線
            #
            # Finviz Elite screener CSV (v=151) では "20-Day Simple Moving Average"
            # 等のカラムは絶対 SMA 価格ではなく current price からの relative
            # percentage を返す。そのため sma_20 / sma_50 / sma_200 (絶対価格) は
            # このカラムから直接取得できない。necessary なら row 解析後に price と
            # sma_*_relative から復元する（_compute_sma_fields 参照）。
            "sma_20_relative": "20-Day Simple Moving Average",
            "sma_50_relative": "50-Day Simple Moving Average",
            "sma_200_relative": "200-Day Simple Moving Average",
            # 高値・安値
            #
            # Finviz Elite screener CSV (v=151) では "52-Week High" / "52-Week Low"
            # カラムは絶対価格ではなく現在価格からの relative percentage を返す。
            # そのため week_52_high / week_52_low (絶対価格) はこのカラムから取得できない。
            # 必要なら row 解析後に price と high_52w_relative / low_52w_relative から
            # 算出する（_compute_absolute_52w_extremes 参照）。
            "day_50_high": "50-Day High",
            "day_50_low": "50-Day Low",
            "all_time_high": "All-Time High",
            "all_time_low": "All-Time Low",
            "high_52w_relative": "52-Week High",  # percent: 現在価格と 52w high の relative distance
            "low_52w_relative": "52-Week Low",  # percent: 現在価格と 52w low の relative distance
            # アナリスト関連
            "target_price": "Target Price",
            # ETF関連
            "net_expense_ratio": "Net Expense Ratio",
            "total_holdings": "Total Holdings",
            "aum": "Assets Under Management",
            "nav": "Net Asset Value",
            "nav_percent": "Net Asset Value %",
            "net_flows_1m": "Net Flows (1 Month)",
            "net_flows_1m_percent": "Net Flows % (1 Month)",
            "net_flows_3m": "Net Flows (3 Month)",
            "net_flows_3m_percent": "Net Flows % (3 Month)",
            "net_flows_ytd": "Net Flows (YTD)",
            "net_flows_ytd_percent": "Net Flows % (YTD)",
            "net_flows_1y": "Net Flows (1 Year)",
            "net_flows_1y_percent": "Net Flows % (1 Year)",
            # その他指標
            "gap": "Gap",
            "average_volume": "Average Volume",
        }

        # 数値フィールドを設定
        for field, csv_column in numeric_fields.items():
            # A field may list several candidate headers (stock vs ETF
            # spellings of the same metric); the first one the row actually
            # carries wins.
            candidates = (
                (csv_column,) if isinstance(csv_column, str) else tuple(csv_column)
            )
            for candidate in candidates:
                if candidate not in row.index:
                    continue
                value = row[candidate]
                if not pd.notna(value):
                    continue
                # 数値変換
                if isinstance(value, str):
                    cleaned_value = self._clean_numeric_value(value)
                    setattr(stock_data, field, cleaned_value)
                else:
                    # 0 / 0.0 are legitimate readings (a flat Change, a
                    # non-dividend payer). pd.notna above already filtered
                    # NaN, so convert unconditionally.
                    setattr(stock_data, field, float(value))
                break

        # Finviz's "Average Volume" column is in thousands of shares while
        # "Volume" is raw shares; normalize to shares so ratios like
        # volume/avg_volume are correct.
        for attr in ("avg_volume", "average_volume"):
            value = getattr(stock_data, attr, None)
            if isinstance(value, (int, float)):
                setattr(stock_data, attr, int(round(value * 1000)))

        # 文字列フィールドを設定（拡張版）
        string_fields = {
            "country": "Country",
            "index": "Index",
            "analyst_recommendation": "Analyst Recom",  # 数値スコア(1.0-5.0)を文字列で保持
            "ipo_date": "IPO Date",
            # earnings_timing (before/after market): no column carries it —
            # "Earnings Date" is a timestamp and there is no "Earnings Time"
            # column. The attribute stays None.
            "single_category": "Single Category",
            "asset_type": "Asset Type",
            "etf_type": "ETF Type",
            "sector_theme": "Sector/Theme",
            "region": "Region",
            "active_passive": "Active/Passive",
            "tags": "Tags",
        }

        # 決算日フィールドの代替名も確認（拡張版）
        # "Earnings Date" ("M/D/YYYY h:mm:ss AM/PM") が実際の export カラム。
        # 残りは他ソース由来の別名フォールバック。
        earnings_columns = [
            "Earnings Date",
            "Earnings",
            "earnings_date",
            "Earnings_Date",
            "Next Earnings Date",
        ]

        for field, csv_column in string_fields.items():
            if field == "earnings_date":
                # 複数の可能なカラム名をチェック
                for col in earnings_columns:
                    if col in row.index:
                        value = row[col]
                        if pd.notna(value) and str(value) != "-" and str(value) != "":
                            setattr(stock_data, field, str(value))
                            break
            elif csv_column in row.index:
                value = row[csv_column]
                if pd.notna(value) and str(value) != "-":
                    setattr(stock_data, field, str(value))

        # 決算日の処理（特別処理）
        for col in earnings_columns:
            if col in row.index:
                value = row[col]
                if pd.notna(value) and str(value) != "-" and str(value) != "":
                    stock_data.earnings_date = str(value)
                    break

        # Boolean フィールドの設定（拡張版）
        # 注意: above_sma_* は v=151 に SMA20/SMA50/SMA200 カラムが存在しない
        # ため、_compute_sma_fields で sma_*_relative （% from SMA）から判定する。
        boolean_fields = {
            "optionable": "Optionable",
            "shortable": "Shortable",
        }

        for field, csv_column in boolean_fields.items():
            if csv_column in row.index:
                value = row[csv_column]
                if pd.notna(value):
                    setattr(
                        stock_data, field, str(value).lower() in ["yes", "true", "1"]
                    )

        # SMA boolean および絶対 SMA 価格を relative percentage から復元
        self._compute_sma_fields(stock_data)

        # 52週高値・安値の絶対価格を relative percentage から復元
        self._compute_absolute_52w_extremes(stock_data)

        return stock_data

    @staticmethod
    def _compute_sma_fields(stock_data: StockData) -> None:
        """
        Finviz screener CSV view では 20/50/200-Day Simple Moving Average は
        relative percentage（% from SMA）で返ってくる。sma_*_relative に
        生の % が入っている前提で:
        - above_sma_*: 0 以上なら True、負なら False
        - sma_*: price と % から絶対価格を復元

        Boundary note: the relative % is rounded to 2 decimals by Finviz, so a
        price sitting on its SMA reports as ``0.00`` and its true sign is
        unrecoverable. We treat ``>= 0`` as "at or above" to mirror Finviz's
        own ``ta_sma*_pa`` (price-above) screener filter, which includes such
        boundary rows.
        """
        price = stock_data.price
        relatives = [
            ("sma_20_relative", "sma_20", "above_sma_20"),
            ("sma_50_relative", "sma_50", "above_sma_50"),
            ("sma_200_relative", "sma_200", "above_sma_200"),
        ]
        for rel_field, abs_field, bool_field in relatives:
            rel = getattr(stock_data, rel_field, None)
            if rel is None:
                continue
            # above_sma: 現在価格が SMA 以上か（relative >= 0 なら True）
            # See the boundary note above for why this is >= rather than >.
            setattr(stock_data, bool_field, rel >= 0)
            # 絶対 SMA 価格を復元: price が SMA より rel% 上 → SMA = price / (1 + rel/100)
            if price and getattr(stock_data, abs_field, None) is None:
                denom = 1 + rel / 100.0
                if denom > 0:
                    setattr(stock_data, abs_field, round(price / denom, 2))

    @staticmethod
    def _compute_absolute_52w_extremes(stock_data: StockData) -> None:
        """
        Finviz screener CSV view では 52-Week High/Low は relative percentage で
        返ってくる（current price からの距離）ため、絶対価格を直接取得できない。
        price と relative% から復元してフィールドを populate する。

        Convention assumed (Finviz Elite v=151 で観測された値より):
        - high_52w_relative > 0: current price は 52w high より低く、% 分だけ離れている
        - low_52w_relative  > 0: current price は 52w low  より高く、% 分だけ離れている

        どちらも convention は "abs(distance / price) * 100" の形と推定。
        """
        price = stock_data.price
        if not price:
            return

        rel_high = stock_data.high_52w_relative
        if rel_high is not None and stock_data.week_52_high is None:
            # current price から +rel_high% 上にあるのが 52w high
            stock_data.week_52_high = round(price * (1 + rel_high / 100.0), 2)

        rel_low = stock_data.low_52w_relative
        if rel_low is not None and stock_data.week_52_low is None:
            # current price から rel_low% 下にあるのが 52w low
            # rel_low が "current は low より rel_low% 上" の場合: low = price / (1 + rel_low/100)
            denom = 1 + rel_low / 100.0
            if denom > 0:
                stock_data.week_52_low = round(price / denom, 2)

    @staticmethod
    def _compute_absolute_52w_prices(result: Dict[str, Any]) -> None:
        """Dict-based twin of :meth:`_compute_absolute_52w_extremes` for the
        fundamentals export path.

        The fundamentals CSV export (v=152) returns "52-Week High" /
        "52-Week Low" as the *relative* percent distance from the current
        price (parsed into ``52_week_high`` / ``52_week_low``), not absolute
        prices. Recover the absolute prices as ``week_52_high`` /
        ``week_52_low``.

        NOTE: unlike ``_compute_absolute_52w_extremes`` (which reads the v=151
        screener's ``high_52w_relative`` where price-below-high is a *positive*
        distance), the v=152 export reports this distance as a *signed* ratio
        ``(price / extreme - 1) * 100`` — negative for the high, positive for
        the low. So both extremes use ``price / (1 + relative / 100)`` here;
        do not "unify" this with the sibling's multiply-for-high convention.
        Verified against Finviz's own displayed prices. Values round-trip to
        within a couple of cents (the relative percent is itself rounded to two
        decimals).
        """
        price = result.get("price")
        if not isinstance(price, (int, float)):
            return
        for rel_key, abs_key in (
            ("52_week_high", "week_52_high"),
            ("52_week_low", "week_52_low"),
        ):
            rel = result.get(rel_key)
            if isinstance(rel, (int, float)):
                denom = 1 + rel / 100
                if denom != 0:
                    result[abs_key] = round(price / denom, 2)

    def _fetch_csv_from_url(
        self, export_url: str, params: Dict[str, Any] = None
    ) -> pd.DataFrame:
        """
        指定されたエクスポートURLからCSVデータを取得

        Args:
            export_url: エクスポートURL
            params: パラメータ（オプション）

        Returns:
            pandas DataFrame (empty only when Finviz returned a header-only CSV)

        Raises:
            FinvizAPIError: missing API key, transport failure, HTML body or
                an unparseable payload. Never converted to an empty result.
        """
        # パラメータを準備
        export_params = params.copy() if params else {}

        # CSV形式を指定
        export_params["ft"] = "4"

        # APIキーを追加（無い場合はここで失敗させる）
        export_params["auth"] = self._require_api_key()

        # CSV データを取得
        response = self._make_request(export_url, export_params)

        return self._csv_response_to_dataframe(response, export_url)

    # Legacy/public aliases that resolve to a canonical field name before the
    # comprehensive mapping is consulted. Defined in constants so the
    # validator accepts exactly the names this client can resolve.
    _FIELD_ALIASES = FINVIZ_FIELD_ALIASES

    @staticmethod
    def _normalize_field_name(name: str) -> str:
        """Normalize a name to the key form used in the CSV-derived result dict.

        Mirrors exactly how raw CSV column headers are normalized when the
        result dict is built, so both sides land on the same key.
        """
        return (
            str(name)
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("(", "")
            .replace(")", "")
            .replace(".", "")
            .replace("-", "_")
            .replace("%", "percent")
        )

    def _resolve_result_key(self, field: str) -> str:
        """Resolve a requested field name to the key it has in the result dict.

        The result dict is keyed by the *normalized CSV header*, so a public
        field name (e.g. ``pe_ratio``) must be translated through its
        ``csv_name`` in ``FINVIZ_COMPREHENSIVE_FIELD_MAPPING`` (``P/E`` →
        ``p_e``). Matching on the public name directly does not work, which is
        why requests for such fields previously vanished or matched the wrong
        column via a loose substring search.
        """
        canonical = self._FIELD_ALIASES.get(field, field)
        entry = FINVIZ_COMPREHENSIVE_FIELD_MAPPING.get(canonical)
        if entry and entry.get("csv_name"):
            return self._normalize_field_name(entry["csv_name"])
        # Already an internal/canonical name (e.g. "p_e", "week_52_high",
        # "relative_strength_index_14") — normalize and use as-is.
        return self._normalize_field_name(canonical)

    # Derived keys computed from another column: when the source key is
    # requested, the derived twin must ride along or it dies in projection.
    # (The "52-Week High/Low" CSV columns are *relative* percentages; the
    # absolute prices week_52_high/week_52_low are computed from price +
    # relative and are what the display layer's "52W High/Low" slots read.)
    _DERIVED_RESULT_KEYS = {
        "52_week_high": ("week_52_high",),
        "52_week_low": ("week_52_low",),
    }

    def _filter_fundamental_fields(
        self,
        result: Dict[str, Any],
        data_fields: List[str],
        include_ticker: bool = False,
    ) -> Dict[str, Any]:
        """Project ``result`` down to the requested ``data_fields``.

        Each requested field is resolved to its canonical result key so the
        value is stored under the key the display/formatting layer reads. A
        requested field with no matching column resolves to ``None`` (an honest
        miss) rather than silently borrowing another column's value.
        """
        filtered: Dict[str, Any] = {}
        if include_ticker and result.get("ticker") is not None:
            filtered["ticker"] = result["ticker"]
        for field in data_fields:
            result_key = self._resolve_result_key(field)
            if result_key not in result:
                logger.warning(
                    f"Field '{field}' (result key '{result_key}') not found in data"
                )
            filtered[result_key] = result.get(result_key)
            for derived_key in self._DERIVED_RESULT_KEYS.get(result_key, ()):
                if derived_key in result:
                    filtered[derived_key] = result[derived_key]
        return filtered

    def _parse_fundamentals_row(
        self, row: "pd.Series", columns: List[str]
    ) -> Dict[str, Any]:
        """Build a fundamentals result dict from one CSV row.

        Shared by the single- and multi-ticker paths. Keys are normalized CSV
        headers; every column is present (null cells become ``None`` so the
        structure is stable across tickers).

        Values: numeric-looking strings ("62.64", "1,234", "5.1%", "$3.2B")
        are converted to numbers — uniformly, not per an incidental keyword
        list, so e.g. ``after_hours_close`` gets the same type as ``price``.
        Anything unparseable (dates, ranges, names, Yes/No) stays a string.
        """
        result: Dict[str, Any] = {}
        for col in columns:
            field_name = self._normalize_field_name(col)
            value = row[col]
            if pd.isna(value) or str(value).strip() in ("", "-"):
                result[field_name] = None
            elif isinstance(value, str):
                converted = self._clean_numeric_value(value)
                result[field_name] = converted if converted is not None else value
            elif hasattr(value, "item"):  # numpy scalar -> plain Python
                result[field_name] = value.item()
            else:
                result[field_name] = value

        # Finviz reports "Average Volume" in thousands of shares while
        # "Volume" is raw shares. Normalize to shares so the two agree.
        avg_volume = result.get("average_volume")
        if isinstance(avg_volume, (int, float)):
            result["average_volume"] = int(round(avg_volume * 1000))
        return result

    def get_stock_fundamentals(
        self, ticker: str, data_fields: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        個別銘柄のファンダメンタルデータを取得（全150フィールド対応）

        Args:
            ticker: 銘柄ティッカー
            data_fields: 取得するデータフィールド（指定しない場合は全フィールド）

        Returns:
            ファンダメンタルデータ辞書またはNone
        """
        try:
            # 全フィールドを取得するためのコラムインデックス（ユーザー提供のURL参考）
            all_columns_param = "0,1,2,79,3,4,5,129,6,7,8,9,10,11,12,13,73,74,75,14,130,131,147,148,149,15,16,77,17,18,142,19,20,143,21,23,22,132,133,82,78,127,128,144,145,146,24,25,85,26,27,28,29,30,31,84,32,33,34,35,36,37,38,39,40,41,90,91,92,93,94,95,96,97,98,99,42,43,44,45,47,46,138,139,140,48,49,50,51,52,53,54,55,56,57,58,134,125,126,59,68,70,80,83,76,60,61,62,63,64,67,89,69,81,86,87,88,65,66,71,72,141,135,136,137,103,100,101,104,102,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,105"

            # 正しいFinviz形式で特定ティッカーを指定（ユーザー提供URLと同じ形式）
            params = {
                "v": "152",  # 最新バージョン指定（ユーザー提供URLと同じ）
                "t": ticker.upper(),  # 特定ティッカーを直接指定
                "c": all_columns_param,  # 全カラム指定
                "ft": "4",  # CSV形式
            }

            # APIキーがある場合は追加
            if self.api_key:
                params["auth"] = self.api_key

            # export.ashx（スクリーニング用）を使用
            df = self._fetch_csv_from_url(self.EXPORT_URL, params)

            if df.empty:
                logger.warning(f"No data returned for ticker: {ticker}")
                return None

            # 特定ティッカーを指定しているので、最初の行を使用
            first_row = df.iloc[0]
            logger.info(f"Retrieved data for {ticker} with {len(df.columns)} columns")

            result = self._parse_fundamentals_row(first_row, df.columns.tolist())

            # 常に基本情報は含める
            result["ticker"] = ticker.upper()

            # 52週高値・安値の絶対価格を price + relative % から復元
            self._compute_absolute_52w_prices(result)

            # 指定されたフィールドのみ返す
            if data_fields:
                return self._filter_fundamental_fields(result, data_fields)

            # すべての利用可能フィールドを返す
            return result

        except FinvizAPIError:
            # リクエスト自体の失敗は「データ無し」に変換しない
            raise
        except Exception as e:
            logger.error(f"Error getting fundamentals for {ticker}: {e}")
            return None

    def get_multiple_stocks_fundamentals(
        self, tickers: List[str], data_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        複数銘柄のファンダメンタルデータ一括取得（全150フィールド対応）

        Args:
            tickers: 銘柄ティッカーリスト
            data_fields: 取得するデータフィールド（指定しない場合は全フィールド）

        Returns:
            ファンダメンタルデータのリスト
        """
        results = []

        logger.info(
            f"Getting fundamentals for {len(tickers)} stocks with full field support"
        )

        try:
            # ユーザー提供の一括取得URLと同じ形式で実装
            # 全フィールドを取得するためのコラムインデックス（ユーザー提供のURL参考）
            all_columns_param = "0,1,2,79,3,4,5,129,6,7,8,9,10,11,12,13,73,74,75,14,130,131,147,148,149,15,16,77,17,18,142,19,20,143,21,23,22,132,133,82,78,127,128,144,145,146,24,25,85,26,27,28,29,30,31,84,32,33,34,35,36,37,38,39,40,41,90,91,92,93,94,95,96,97,98,99,42,43,44,45,47,46,138,139,140,48,49,50,51,52,53,54,55,56,57,58,134,125,126,59,68,70,80,83,76,60,61,62,63,64,67,89,69,81,86,87,88,65,66,71,72,141,135,136,137,103,100,101,104,102,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,105"

            # 複数ティッカーをカンマ区切りで指定（ユーザー提供URLと同じ形式）
            tickers_str = ",".join([t.upper() for t in tickers])

            params = {
                "v": "152",  # 最新バージョン指定（ユーザー提供URLと同じ）
                "t": tickers_str,  # 複数ティッカーをカンマ区切りで指定
                "c": all_columns_param,  # 全カラム指定
                "ft": "4",  # CSV形式
            }

            # APIキーがある場合は追加
            if self.api_key:
                params["auth"] = self.api_key

            # 一括取得を実行
            df = self._fetch_csv_from_url(self.EXPORT_URL, params)

            if df.empty:
                logger.warning(f"No data returned for tickers: {tickers}")
                # 空データの場合は個別取得にフォールバック
                logger.info("Falling back to individual ticker fetching...")
                for ticker in tickers:
                    individual_data = self.get_stock_fundamentals(ticker, data_fields)
                    if individual_data:
                        results.append(individual_data)
                    else:
                        # 空の結果を追加
                        empty_result = {"ticker": ticker}
                        if data_fields:
                            for field in data_fields:
                                empty_result[field] = None
                        results.append(empty_result)
                return results

            logger.info(
                f"Successfully retrieved bulk data with {len(df)} rows and {len(df.columns)} columns"
            )

            # DataFrameの各行を処理してデータを抽出
            available_columns = df.columns.tolist()
            for idx, row in df.iterrows():
                try:
                    result = self._parse_fundamentals_row(row, available_columns)

                    # ティッカー情報を確実に含める
                    if "ticker" in result and result["ticker"]:
                        logger.info(f"Processed ticker: {result['ticker']}")
                    else:
                        # ティッカーがない場合は順番で推定
                        if idx < len(tickers):
                            result["ticker"] = tickers[idx]
                            logger.warning(
                                f"No ticker in data, using position-based ticker: {tickers[idx]}"
                            )
                        else:
                            logger.warning(f"No ticker information for row {idx}")
                            continue

                    # 52週高値・安値の絶対価格を price + relative % から復元
                    self._compute_absolute_52w_prices(result)

                    # 指定されたフィールドのみ返す
                    if data_fields:
                        filtered_result = self._filter_fundamental_fields(
                            result, data_fields, include_ticker=True
                        )
                        results.append(filtered_result)
                    else:
                        # すべての利用可能フィールドを返す
                        results.append(result)

                except Exception as e:
                    logger.warning(f"Error processing row {idx}: {e}")
                    # エラーの場合でも基本情報は返す
                    ticker = tickers[idx] if idx < len(tickers) else f"Unknown_{idx}"
                    error_result = {"ticker": ticker, "error": str(e)}
                    if data_fields:
                        for field in data_fields:
                            error_result[field] = None
                    results.append(error_result)
                    continue

            logger.info(
                f"Successfully processed {len(results)} stocks out of {len(tickers)} requested"
            )
            return results

        except FinvizAPIError:
            # 認証切れ・HTML応答などは個別取得でも必ず失敗する。
            # 全ティッカー分リトライして同じ失敗を繰り返さず、そのまま報告する。
            raise
        except Exception as e:
            logger.error(f"Error in bulk fundamentals retrieval: {e}")
            logger.info("Falling back to individual ticker fetching...")

            # エラーが発生した場合は個別取得にフォールバック
            for ticker in tickers:
                try:
                    individual_data = self.get_stock_fundamentals(ticker, data_fields)
                    if individual_data:
                        results.append(individual_data)
                    else:
                        # 空の結果を追加
                        empty_result = {"ticker": ticker}
                        if data_fields:
                            for field in data_fields:
                                empty_result[field] = None
                        results.append(empty_result)

                    # レート制限対応
                    time.sleep(0.2)

                except Exception as individual_error:
                    logger.warning(
                        f"Failed to get fundamentals for {ticker}: {individual_error}"
                    )
                    # エラーの場合でも基本情報は返す
                    error_result = {"ticker": ticker, "error": str(individual_error)}
                    if data_fields:
                        for field in data_fields:
                            error_result[field] = None
                    results.append(error_result)
                    continue

            return results
