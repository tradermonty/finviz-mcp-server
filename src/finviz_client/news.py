import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional, Union
from zoneinfo import ZoneInfo

import pandas as pd

from ..models import NewsData
from .base import FinvizClient

logger = logging.getLogger(__name__)

# Finviz news_export.ashx timestamps are US/Eastern wall-clock with no offset
# (GROUND_TRUTH.md). Everything below keeps them tz-aware in that zone so the
# ``days_back`` window is correct no matter where the server runs, and so a
# naive-vs-aware comparison can never raise.
EASTERN = ZoneInfo("America/New_York")


def _now_et() -> datetime:
    """Current time in US/Eastern (patch point for tests)."""
    return datetime.now(EASTERN)


def _as_et(dt: datetime) -> datetime:
    """Return ``dt`` in US/Eastern; a naive value is *assumed* Eastern."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=EASTERN)
    return dt.astimezone(EASTERN)


def _cell(row: Any, key: str) -> str:
    """Read a CSV cell as a clean string.

    Missing columns and NaN cells become ``""`` — never the literal ``"nan"``
    that ``str(float('nan'))`` produces.
    """
    try:
        value = row.get(key)
    except AttributeError:  # not a Series/mapping
        return ""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):  # arrays / odd types
        pass
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


class FinvizNewsClient(FinvizClient):
    """Finvizニュース機能専用クライアント

    Endpoint reality (verified, see GROUND_TRUTH.md):

    * ``news_export.ashx?v=1`` — market/general news.
      Columns ``Title,Source,Date,Url,Category``; ``Category`` is ``Market``
      or ``Blog``. No ``Ticker`` column.
    * ``news_export.ashx?v=3`` — per-stock headlines. Adds a ``Ticker``
      column (comma-joined when an item covers several names) and
      ``Category`` is always ``Stock``. ``t=A,B`` restricts to those tickers.
    * ``sec=`` and ``filter=`` are **ignored** by the endpoint, so neither a
      sector feed nor a news-type feed exists server-side.
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)

    # ------------------------------------------------------------------
    # Stock news (v=3)
    # ------------------------------------------------------------------
    def get_stock_news(
        self, tickers: Union[str, List[str]], days_back: int = 7
    ) -> List[NewsData]:
        """
        指定銘柄のニュースを取得（news_export v=3）

        Args:
            tickers: 銘柄ティッカー（単一、カンマ区切り文字列、またはリスト）
            days_back: 過去何日分のニュース（US/Eastern基準）

        Returns:
            NewsData オブジェクトのリスト（該当なしの場合は空リスト）。
            各アイテムの ``ticker`` はCSVの ``Ticker`` 列の実値。

        Raises:
            ValueError: ティッカーが不正な場合
            FinvizAPIError: リクエスト自体が失敗した場合（「ニュース無し」にしない）

        Note:
            There is no news-type filter: Finviz ignores ``filter=`` and every
            v=3 row carries ``Category=Stock``, so nothing can be filtered on
            honestly. See C3 in AUDIT_FINDINGS.md.

            ``days_back`` の境界は**含む**: ちょうど ``days_back`` 日前の
            アイテムは残る（``date < cutoff`` のみ落とす）。
            日付が空/``-``/解釈不能な行は落とすが、件数をWARNINGで1回まとめて
            記録する（フィード書式変更が「ニュース無し」に化けないため）。
        """
        from ..utils.validators import parse_tickers, validate_tickers

        # ティッカーの妥当性チェック
        if not validate_tickers(tickers):
            raise ValueError(f"Invalid tickers: {tickers}")

        # ティッカーを正規化されたリストに変換
        ticker_list = parse_tickers(tickers)

        params = {
            "v": "3",
            "t": ",".join(ticker_list),
        }

        df = self._fetch_csv_from_url(self.NEWS_EXPORT_URL, params)

        if df.empty:
            logger.info(f"Finviz returned no news rows for {ticker_list}")
            return []

        fallback = ticker_list[0] if len(ticker_list) == 1 else None
        news_list = self._rows_to_news(
            df,
            cutoff_date=self._cutoff(days_back),
            fallback_ticker=fallback,
        )

        logger.info(f"Retrieved {len(news_list)} news items for {ticker_list}")
        return news_list

    # ------------------------------------------------------------------
    # Market news (v=1)
    # ------------------------------------------------------------------
    #: ``Category`` values observed on the v=1 feed (probe 2026-07-31).
    MARKET_NEWS_CATEGORIES = ("Market", "Blog")

    def get_market_news(
        self,
        days_back: int = 3,
        max_items: int = 50,
        category: Optional[str] = None,
    ) -> List[NewsData]:
        """
        市場全体のニュースを取得（news_export v=1）

        Args:
            days_back: 過去何日分のニュース（US/Eastern基準）
            max_items: 最大取得件数
            category: CSVの ``Category`` 列に対する**クライアント側**フィルタ。
                ``MARKET_NEWS_CATEGORIES`` のいずれか（大文字小文字は不問）。
                None なら全件。

        Returns:
            NewsData オブジェクトのリスト（``ticker`` は None: v=1 に
            ``Ticker`` 列は存在しない）

        Note:
            ``days_back`` の境界は**含む**: ちょうど ``days_back`` 日前の
            アイテムは残る（``date < cutoff`` のみ落とす）。
            日付が空/``-``/解釈不能な行は落とすが、件数をWARNINGで1回まとめて
            記録する（フィード書式変更が「ニュース無し」に化けないため）。

        Raises:
            ValueError: 未知の ``category`` を渡した場合（黙って0件にしない）
            FinvizAPIError: リクエスト自体が失敗した場合（「ニュース無し」にしない）
        """
        # 存在しないカテゴリを黙って「0件」にしない（house rule 2）
        if category is not None:
            if category.strip().lower() not in {
                c.lower() for c in self.MARKET_NEWS_CATEGORIES
            }:
                raise ValueError(
                    f"Unknown market news category: {category!r}. "
                    f"The v=1 feed only carries "
                    f"{', '.join(self.MARKET_NEWS_CATEGORIES)}."
                )

        params = {"v": "1"}

        df = self._fetch_csv_from_url(self.NEWS_EXPORT_URL, params)

        if df.empty:
            logger.info("Finviz returned no market news rows")
            return []

        news_list = self._rows_to_news(
            df,
            cutoff_date=self._cutoff(days_back),
            fallback_ticker=None,
            max_items=max_items,
            category=category,
        )

        logger.info(f"Retrieved {len(news_list)} market news items")
        return news_list

    # ------------------------------------------------------------------
    # Sector news (constituents -> v=3)
    # ------------------------------------------------------------------
    #: How many constituents (largest by market cap) a sector query covers.
    SECTOR_TICKER_LIMIT = 40

    def get_sector_news(
        self, sector: str, days_back: int = 5, max_items: int = 30
    ) -> List[NewsData]:
        """
        特定セクターのニュースを取得（構成銘柄経由、リクエストは2回）

        Finviz has no sector news feed (``sec=`` is ignored), so this resolves
        the sector to its largest constituents with one screener export and
        then asks the v=3 news feed for exactly those tickers. Every returned
        item carries the real ``Ticker`` of the article.

        Args:
            sector: セクター名またはFinvizコード
            days_back: 過去何日分のニュース（US/Eastern基準）
            max_items: 最大取得件数

        Returns:
            NewsData オブジェクトのリスト

        Note:
            ``days_back`` の境界は**含む**: ちょうど ``days_back`` 日前の
            アイテムは残る（``date < cutoff`` のみ落とす）。
            日付が空/``-``/解釈不能な行は落とすが、件数をWARNINGで1回まとめて
            記録する（フィード書式変更が「ニュース無し」に化けないため）。

        Raises:
            ValueError: セクター名が未知、または構成銘柄が0件の場合
            FinvizAPIError: リクエスト自体が失敗した場合
        """
        # 1回目: セクター構成銘柄（時価総額降順）
        tickers = self.get_sector_constituent_tickers(
            sector, limit=self.SECTOR_TICKER_LIMIT
        )

        # 2回目: その銘柄群のニュース
        df = self._fetch_csv_from_url(
            self.NEWS_EXPORT_URL, {"v": "3", "t": ",".join(tickers)}
        )

        if df.empty:
            logger.info(f"Finviz returned no news rows for {sector} constituents")
            return []

        news_list = self._rows_to_news(
            df,
            cutoff_date=self._cutoff(days_back),
            fallback_ticker=None,
            max_items=max_items,
        )

        logger.info(
            f"Retrieved {len(news_list)} news items for {len(tickers)} "
            f"{sector} constituents"
        )
        return news_list

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _cutoff(days_back: int, now: Optional[datetime] = None) -> datetime:
        """Eastern-time cutoff for a ``days_back`` window.

        The boundary is **inclusive**: only ``date < cutoff`` is dropped, so an
        item timestamped exactly ``days_back`` days ago is kept.
        """
        reference = _as_et(now) if now is not None else _now_et()
        return reference - timedelta(days=days_back)

    def _rows_to_news(
        self,
        df: "pd.DataFrame",
        cutoff_date: datetime,
        fallback_ticker: Optional[str] = None,
        max_items: Optional[int] = None,
        category: Optional[str] = None,
    ) -> List[NewsData]:
        """Convert CSV rows to NewsData, newest-first order preserved.

        Rows we cannot use are dropped, but never silently: the counts are
        summarised in one WARNING per call so a changed feed format shows up
        as "N rows had an unparseable Date" instead of masquerading as
        "no news".
        """
        wanted_category = category.strip().lower() if category else None
        news_list: List[NewsData] = []
        undated_rows = 0
        untitled_rows = 0

        for _, row in df.iterrows():
            # 日付が読めない行は使えない（期間判定ができない）ので数えて捨てる
            if self._parse_news_date_from_csv(_cell(row, "Date")) is None:
                undated_rows += 1
                continue
            if not _cell(row, "Title"):
                untitled_rows += 1
                continue

            # 行単位のパースエラーは1件だけ捨てる
            try:
                news_data = self._parse_news_from_csv(
                    row, cutoff_date, fallback_ticker=fallback_ticker
                )
            except Exception as e:
                logger.warning(f"Failed to parse news data from CSV: {e}")
                continue

            if not news_data:
                continue
            if (
                wanted_category
                and (news_data.category or "").lower() != wanted_category
            ):
                continue

            news_list.append(news_data)
            if max_items is not None and len(news_list) >= max_items:
                break

        if undated_rows or untitled_rows:
            logger.warning(
                "Dropped %d of %d news rows: %d with an empty/unparseable Date, "
                "%d with no Title (check the feed format if this is unexpected)",
                undated_rows + untitled_rows,
                len(df),
                undated_rows,
                untitled_rows,
            )

        return news_list

    def _parse_news_from_csv(
        self,
        row: "pd.Series",
        cutoff_date: datetime,
        fallback_ticker: Optional[str] = None,
    ) -> Optional[NewsData]:
        """
        CSV行からNewsDataオブジェクトを作成

        Args:
            row: pandasのSeries（CSV行データ）
            cutoff_date: カットオフ日時（naiveならUS/Easternとみなす）
            fallback_ticker: ``Ticker`` 列が無い/空のときに使う値（任意）

        Returns:
            NewsData オブジェクトまたはNone（期間外・必須項目欠落）
        """
        try:
            # 必須フィールド。NaNセルは "nan" ではなく空文字になる。
            title = _cell(row, "Title")
            if not title:
                logger.debug("Skipping news row without a Title")
                return None

            source = _cell(row, "Source")
            # CSVのカラム名は "Url"（"URL" ではない）— GROUND_TRUTH.md参照
            url = _cell(row, "Url")

            # 日時の解析（US/Eastern）
            news_date = self._parse_news_date_from_csv(_cell(row, "Date"))
            if not news_date or news_date < _as_et(cutoff_date):
                return None

            # カテゴリはCSVの実値（v=1: Market/Blog, v=3: Stock）。推測しない。
            category = _cell(row, "Category")

            # 記事に紐づく実際のティッカー（v=3のみ。複数はカンマ連結）
            ticker = _cell(row, "Ticker") or (fallback_ticker or "")

            return NewsData(
                ticker=ticker or None,
                title=title,
                source=source,
                date=news_date,
                url=url,
                category=category,
            )

        except Exception as e:
            logger.warning(f"Failed to parse news data from CSV row: {e}")
            return None

    def _parse_news_date_from_csv(self, date_str: str) -> Optional[datetime]:
        """
        CSV日時文字列をUS/Eastern awareなdatetimeに変換

        Args:
            date_str: 日時文字列（例 ``2026-07-31 04:07:58``）

        Returns:
            tz-aware datetime（US/Eastern）またはNone
        """
        if not date_str or date_str == "-":
            return None

        try:
            # ISO形式（オフセット付きのことがある）
            if "T" in date_str:
                parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return _as_et(parsed)

            # Finvizのエクスポート形式
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]:
                try:
                    return datetime.strptime(date_str, fmt).replace(tzinfo=EASTERN)
                except ValueError:
                    continue

            logger.warning(f"Could not parse date string: {date_str}")
            return None

        except Exception as e:
            logger.warning(f"Error parsing date '{date_str}': {e}")
            return None
