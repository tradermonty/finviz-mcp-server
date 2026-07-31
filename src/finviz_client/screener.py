import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..models import (
    MARKET_CAP_FILTERS,
    StockData,
    UpcomingEarningsData,
    resolve_market_cap_code,
)
from .base import (
    EARNINGS_DATE_TOKENS,
    EARNINGS_DATE_WINDOW_DAYS,
    FinvizClient,
    finviz_date_range,
    parse_earnings_datetime,
    resolve_sector_code,
)
from .base import sorted_none_last as _sorted_none_last

# ``parse_earnings_datetime`` / ``sorted_none_last`` live in base.py because
# ``screen_stocks_raw`` needs them too and base must not import from here.
__all__ = ["FinvizScreener", "parse_earnings_datetime"]

logger = logging.getLogger(__name__)

# Asset-class request -> substring of the export's ``Asset Type`` column.
# The real vocabulary (probed): "Equities (Stocks)", "Bonds", "CryptoCurrency",
# "Multi-Asset - Tactical / Active", "Commodities & Metals", "Preferred Stock".
ASSET_CLASS_MATCHES = {
    "equity": "equit",
    "equities": "equit",
    "stock": "equit",
    "stocks": "equit",
    "bond": "bond",
    "bonds": "bond",
    "fixed income": "bond",
    "commodity": "commodit",
    "commodities": "commodit",
    "metal": "metal",
    "metals": "metal",
    "crypto": "crypto",
    "cryptocurrency": "crypto",
    "multi-asset": "multi-asset",
    "multi_asset": "multi-asset",
    "preferred": "preferred",
}


class FinvizScreener(FinvizClient):
    """Finvizスクリーニング機能専用クライアント"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)

    def earnings_screener(self, **kwargs) -> List[StockData]:
        """
        決算発表予定銘柄のスクリーニング

        Args:
            earnings_date: 決算発表日の指定
            market_cap: 時価総額フィルタ
            min_price: 最低株価
            max_price: 最高株価
            min_volume: 最低出来高（当日出来高 sh_curvol_*）
            sectors: 対象セクター

        Returns:
            StockData オブジェクトのリスト

        Note:
            寄り付き前／時間外の価格変動での絞り込みは受け付けない。Finvizの
            スクリーナーにpre-market変動のフィルタトークンは無く、``ah_change``
            も表示専用である（audit B13）。時間外の値動きで絞りたい場合は
            ``earnings_afterhours_screener`` を使う。
        """
        filters = self._build_earnings_filters(**kwargs)
        return self.screen_stocks(filters)

    def volume_surge_screener(self) -> List[StockData]:
        """
        出来高急増を伴う上昇銘柄のスクリーニング（固定条件）

        固定フィルタ条件（変更不可）：
        f=cap_smallover,ind_stocksonly,sh_avgvol_o100,sh_price_o10,sh_relvol_o1.5,ta_change_u2,ta_sma200_pa&ft=4&o=-change&ar=10

        - 時価総額：スモール以上 ($300M+)
        - 株式のみ：ETF除外
        - 平均出来高：100,000以上
        - 株価：$10以上
        - 相対出来高：1.5倍以上
        - 価格変動：2%以上上昇
        - 200日移動平均線上
        - 価格変動降順ソート
        - 最大結果件数：10件

        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_volume_surge_filters()
        results = self.screen_stocks(filters)

        # 固定ソート（価格変動率降順）
        results = _sorted_none_last(results, key=lambda x: x.price_change, reverse=True)

        # 全件返す（制限なし）
        return results

    def uptrend_screener(self) -> List[StockData]:
        """
        上昇トレンド銘柄のスクリーニング（固定条件）

        固定フィルタ条件（変更不可）：
        f=cap_microover,sh_avgvol_o100,sh_price_o10,ta_highlow52w_a30h,ta_perf2_4wup,ta_sma20_pa,ta_sma200_pa,ta_sma50_sa200&ft=4&o=-epsyoy1

        - 時価総額：マイクロ以上（$50M+）
        - 平均出来高：100K以上
        - 株価：$10以上
        - 52週高値から30%以内
        - 4週パフォーマンス上昇
        - 20日移動平均線上
        - 200日移動平均線上
        - 50日移動平均線が200日移動平均線上
        - 株式のみ
        - EPS成長率（年次）降順ソート

        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_uptrend_filters()
        results = self.screen_stocks(filters)

        # Finvizで既にソートされているので、そのまま返す
        return results

    def dividend_growth_screener(self, **kwargs) -> List[StockData]:
        """
        配当成長銘柄のスクリーニング

        Args:
            min_dividend_yield: 最低配当利回り
            max_dividend_yield: 最高配当利回り
            min_payout_ratio: 最低配当性向
            max_payout_ratio: 最高配当性向
            min_roe: 最低ROE
            max_debt_equity: 最高負債比率
            max_results: 最大取得件数

        Returns:
            StockData オブジェクトのリスト（ソート後に max_results で切る）
        """
        filters = self._build_dividend_growth_filters(**kwargs)
        results = self.screen_stocks(filters)

        # 結果制限とソート
        max_results = kwargs.get("max_results", 100)
        sort_by = kwargs.get("sort_by", "dividend_yield")
        reverse = kwargs.get("sort_order", "desc") == "desc"

        # ソートしてから切る（逆順ティッカー順の先頭N件を後からソートすると
        # 「配当利回り上位」が「ZZ〜から数えてN件を並べ替えたもの」になる:
        # audit B7）。
        sort_keys = {
            "dividend_yield": lambda x: x.dividend_yield,
            "market_cap": lambda x: x.market_cap,
            "sma200": lambda x: x.sma_200,
            "pe_ratio": lambda x: x.pe_ratio,
        }
        if sort_by in sort_keys:
            results = _sorted_none_last(
                results, key=sort_keys[sort_by], reverse=reverse
            )
        else:
            raise ValueError(
                f"Unsupported sort_by for dividend_growth_screener: {sort_by!r}. "
                f"Valid values: {', '.join(sorted(sort_keys))}"
            )

        return results[:max_results] if max_results else results

    def etf_screener(self, **kwargs) -> List[StockData]:
        """
        ETF戦略用スクリーニング

        Args:
            asset_class: 資産クラス（Asset Type 列でクライアント側フィルタ）
            min_aum: 最低運用資産額（USD、クライアント側フィルタ）
            max_expense_ratio: 最高経費率（%、クライアント側フィルタ）
            max_results: 最大取得件数

        Returns:
            StockData オブジェクトのリスト（ソート後に max_results で切る）

        Note:
            サーバー側で絞れるのはETF universe（``ind_exchangetradedfund``）
            まで。AUM・経費率・資産クラスのFinvizトークンは存在が確認できな
            かったため、CSVに含まれる実データでクライアント側に適用する
            （audit B3）。件数の絞り込みはソート後。
        """
        filters = self._build_etf_filters(**kwargs)
        results = self.screen_stocks(filters)
        results = self._apply_etf_client_filters(results, **kwargs)

        # 結果制限とソート
        max_results = kwargs.get("max_results", 50)
        sort_by = kwargs.get("sort_by", "aum")
        reverse = kwargs.get("sort_order", "desc") == "desc"

        sort_keys = {
            "aum": lambda x: x.aum,
            "expense_ratio": lambda x: x.net_expense_ratio,
            "price": lambda x: x.price,
            "volume": lambda x: x.volume,
            "ticker": lambda x: x.ticker,
        }
        if sort_by not in sort_keys:
            raise ValueError(
                f"Unsupported sort_by for etf_screener: {sort_by!r}. "
                f"Valid values: {', '.join(sorted(sort_keys))}"
            )
        results = _sorted_none_last(results, key=sort_keys[sort_by], reverse=reverse)

        return results[:max_results] if max_results else results

    @staticmethod
    def _apply_etf_client_filters(
        results: List[StockData], **kwargs
    ) -> List[StockData]:
        """Apply the ETF criteria Finviz has no filter token for.

        Rows missing the datum are dropped rather than kept: "AUM >= $1B"
        must not silently include ETFs whose AUM we do not know.
        """
        min_aum = kwargs.get("min_aum")
        max_expense_ratio = kwargs.get("max_expense_ratio")
        asset_class = kwargs.get("asset_class")

        if min_aum is not None:
            results = [s for s in results if s.aum is not None and s.aum >= min_aum]
        if max_expense_ratio is not None:
            results = [
                s
                for s in results
                if s.net_expense_ratio is not None
                and s.net_expense_ratio <= max_expense_ratio
            ]
        if asset_class:
            needle = ASSET_CLASS_MATCHES.get(
                str(asset_class).strip().lower(), str(asset_class).strip().lower()
            )
            results = [
                s for s in results if s.asset_type and needle in s.asset_type.lower()
            ]
        return results

    def earnings_premarket_screener(self) -> List[StockData]:
        """
        寄り付き前決算発表で上昇している銘柄のスクリーニング（固定条件）

        固定フィルタ条件（変更不可）：
        f=cap_largeover,earningsdate_todaybefore,sh_avgvol_o100,sh_price_o30,ta_change_u2&ft=4&o=-change

        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_earnings_premarket_filters()
        results = self.screen_stocks(filters)

        # 固定ソート（価格変動率降順）→ そのあとで60件に切る
        results = _sorted_none_last(results, key=lambda x: x.price_change, reverse=True)

        return results[: filters.get("max_results", 60)]

    def earnings_afterhours_screener(self) -> List[StockData]:
        """
        引け後決算発表で時間外取引上昇銘柄のスクリーニング（固定条件）

        固定フィルタ条件（変更不可）：
        f=ah_change_u2,cap_largeover,earningsdate_todayafter,sh_avgvol_o100,sh_price_o30&ft=4&o=-afterchange&ar=60

        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_earnings_afterhours_filters()
        results = self.screen_stocks(filters)

        # 固定ソート（時間外変動率降順）
        results = _sorted_none_last(
            results, key=lambda x: x.afterhours_change_percent, reverse=True
        )

        # 固定結果件数（60件）
        return results[:60]

    def earnings_trading_screener(self) -> List[StockData]:
        """
        決算トレード対象銘柄のスクリーニング（固定条件）

        固定フィルタ: f=cap_largeover,earningsdate_yesterdayafter|todaybefore,fa_epsrev_ep,fa_netmargin_3to,sh_avgvol_o200,sh_price_o30,ta_change_u,ta_perf_0to-4w&ft=4&o=-epssurprise&ar=60

        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_earnings_trading_filters()
        results = self.screen_stocks(filters)

        # EPSサプライズ降順ソート（固定）
        results = _sorted_none_last(results, key=lambda x: x.eps_surprise, reverse=True)

        # 最大60件（固定）
        return results[:60]

    def earnings_positive_surprise_screener(self, **kwargs) -> List[StockData]:
        """
        今週決算発表でポジティブサプライズがあって上昇している銘柄のスクリーニング

        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_earnings_positive_surprise_filters(**kwargs)
        results = self.screen_stocks(filters)

        # ソートと制限
        max_results = kwargs.get("max_results", 50)
        sort_by = kwargs.get("sort_by", "eps_qoq_growth")

        if sort_by == "eps_qoq_growth":
            results = _sorted_none_last(
                results, key=lambda x: x.eps_growth_qtr, reverse=True
            )
        elif sort_by == "performance_1w":
            results = _sorted_none_last(
                results, key=lambda x: x.performance_1w, reverse=True
            )

        return results[:max_results]

    def trend_reversion_screener(self, **kwargs) -> List[StockData]:
        """
        トレンド反転候補銘柄のスクリーニング

        Args:
            market_cap: 時価総額フィルタ
            eps_growth_qoq: EPS成長率(QoQ) 最低値
            revenue_growth_qoq: 売上成長率(QoQ) 最低値
            rsi_max: RSI上限値
            sectors: 対象セクター
            exclude_sectors: 除外セクター
            max_results: 最大取得件数

        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_trend_reversion_filters(**kwargs)
        results = self.screen_stocks(filters)

        # 除外セクターはクライアント側で適用（Finvizに否定構文は無い）
        exclude_sectors = kwargs.get("exclude_sectors") or []
        if exclude_sectors:
            excluded_codes = set()
            for sector in exclude_sectors:
                code = resolve_sector_code(sector)
                if not code:
                    raise ValueError(f"Unknown sector in exclude_sectors: {sector!r}")
                excluded_codes.add(code)
            results = [
                stock
                for stock in results
                if resolve_sector_code(stock.sector or "") not in excluded_codes
            ]

        # 結果制限とソート
        max_results = kwargs.get("max_results", 50)
        sort_by = kwargs.get("sort_by", "rsi")
        reverse = kwargs.get("sort_order", "asc") == "desc"  # RSIは低い順

        sort_keys = {
            "rsi": lambda x: x.rsi,
            "eps_growth_qoq": lambda x: x.eps_growth_qtr,
            "market_cap": lambda x: x.market_cap,
            "price_change": lambda x: x.price_change,
        }
        if sort_by not in sort_keys:
            raise ValueError(
                f"Unsupported sort_by for trend_reversion_screener: {sort_by!r}. "
                f"Valid values: {', '.join(sorted(sort_keys))}"
            )
        results = _sorted_none_last(results, key=sort_keys[sort_by], reverse=reverse)

        return results[:max_results] if max_results else results

    def get_relative_volume_stocks(self, **kwargs) -> List[StockData]:
        """
        相対出来高異常銘柄の検出

        Args:
            min_relative_volume: 最低相対出来高
            min_price: 最低株価
            sectors: 対象セクター
            max_results: 最大取得件数

        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_relative_volume_filters(**kwargs)
        results = self.screen_stocks(filters)

        # 相対出来高でソート
        results = _sorted_none_last(
            results, key=lambda x: x.relative_volume, reverse=True
        )

        max_results = kwargs.get("max_results", 50)
        return results[:max_results]

    def technical_analysis_screener(self, **kwargs) -> Tuple[List[StockData], int]:
        """
        テクニカル分析ベースのスクリーニング

        Args:
            rsi_min: RSI最低値
            rsi_max: RSI最高値
            price_vs_sma20: 20日移動平均との関係 (above / below)
            price_vs_sma50: 50日移動平均との関係 (above / below)
            price_vs_sma200: 200日移動平均との関係 (above / below)
            min_price: 最低株価
            min_volume: 最低出来高（当日出来高）
            sectors: 対象セクター
            max_results: 最大取得件数

        Returns:
            ``(結果リスト, 条件に一致した総数)``。返すのはティッカー昇順の
            先頭 ``max_results`` 件。以前は「Finvizが返した順（逆ティッカー順）の
            先頭50件」を暗黙に返していた（audit B7/B28）。
        """
        filters = self._build_technical_analysis_filters(**kwargs)
        results = self.screen_stocks(filters)

        # 決まった順序で切る: ソート基準の無いスクリーナーなので、
        # 「アルファベット順の先頭N件」であることを呼び出し側が説明できる
        # 形にする。
        results.sort(key=lambda stock: stock.ticker or "")
        total_matches = len(results)

        max_results = kwargs.get("max_results") or 50
        return results[:max_results], total_matches

    def _build_earnings_filters(self, **kwargs) -> Dict[str, Any]:
        """決算スクリーニング用フィルタを構築"""
        filters = {}

        # 決算発表日。固定トークンの無い期間（"within_2_weeks" など）は
        # ここで実際の日付レンジに解決しておく。以前は nextdays5（5営業日）
        # に化けており、フィルタ辞書には要求ラベルだけが残るので、条件表示
        # が「2週間で絞った」と嘘をついていた（レビュー指摘 #4 / audit B15）。
        if "earnings_date" in kwargs:
            filters["earnings_date"] = self.resolve_earnings_date(
                kwargs["earnings_date"]
            )

        # 時価総額
        if "market_cap" in kwargs:
            filters["market_cap"] = kwargs["market_cap"]

        # 価格範囲
        if "min_price" in kwargs:
            filters["price_min"] = kwargs["min_price"]
        if "max_price" in kwargs:
            filters["price_max"] = kwargs["max_price"]

        # 出来高
        if "min_volume" in kwargs:
            filters["volume_min"] = kwargs["min_volume"]

        # セクター
        if "sectors" in kwargs and kwargs["sectors"]:
            filters["sectors"] = kwargs["sectors"]

        return filters

    def _build_volume_surge_filters(self) -> Dict[str, Any]:
        """
        出来高急増スクリーニング用フィルタを構築（固定条件）

        固定フィルタ条件（変更不可）：
        f=cap_smallover,ind_stocksonly,sh_avgvol_o100,sh_price_o10,sh_relvol_o1.5,ta_change_u2,ta_sma200_pa&ft=4&o=-change

        - 時価総額：スモール以上 ($300M+)
        - 株式のみ
        - 平均出来高：100,000以上
        - 株価：$10以上
        - 相対出来高：1.5倍以上
        - 価格変動：2%以上上昇
        - 200日移動平均線上
        - 価格変動降順ソート
        - 全件取得（制限なし）
        """
        filters = {}

        # 固定条件を設定
        # 時価総額：スモール以上
        filters["market_cap"] = "smallover"

        # 平均出来高：100,000以上
        filters["avg_volume_min"] = 100000

        # 株価：$10以上
        filters["price_min"] = 10.0

        # 相対出来高：1.5倍以上
        filters["relative_volume_min"] = 1.5

        # 価格変動：2%以上上昇
        filters["price_change_min"] = 2.0

        # 200日移動平均線上
        filters["sma200_above"] = True

        # ソート条件（価格変動降順）
        filters["sort_by"] = "price_change"
        filters["sort_order"] = "desc"

        # 株式のみ（ETFなどを除外）
        filters["stocks_only"] = True

        # 全件取得（制限なし）
        # filters['max_results'] = 削除

        return filters

    def _build_uptrend_filters(self) -> Dict[str, Any]:
        """
        上昇トレンドフィルタを構築（固定条件）

        固定フィルタ条件（変更不可）：
        f=cap_microover,sh_avgvol_o100,sh_price_o10,ta_highlow52w_a30h,ta_perf2_4wup,ta_sma20_pa,ta_sma200_pa,ta_sma50_sa200&ft=4&o=-epsyoy1

        - 時価総額：マイクロ以上（$50M+）
        - 平均出来高：100K以上
        - 株価：$10以上
        - 52週高値から30%以内
        - 4週パフォーマンス上昇
        - 20日移動平均線上
        - 200日移動平均線上
        - 50日移動平均線が200日移動平均線上
        - 株式のみ
        - EPS成長率（年次）降順ソート
        """
        filters = {}

        # デフォルト条件を設定（Finviz推奨に合わせる）
        # 時価総額：マイクロ以上（修正）
        filters["market_cap"] = "microover"

        # 平均出来高：100K以上（修正：100000 → 100）
        filters["avg_volume_min"] = 100

        # 株価：10以上（小数点を除去）
        filters["price_min"] = 10

        # 52週高値から30%以内（小数点を除去）
        filters["near_52w_high"] = 30

        # 4週パフォーマンス上昇（新規追加）
        filters["performance_4w_positive"] = True

        # 移動平均線条件
        filters["sma20_above"] = True
        filters["sma200_above"] = True
        filters["sma50_above_sma200"] = True

        # ソート条件（EPS年次成長率降順に修正）
        filters["sort_by"] = "eps_growth_yoy"
        filters["sort_order"] = "desc"

        # 株式のみ（ETFなどを除外）
        filters["stocks_only"] = True

        return filters

    def _build_dividend_growth_filters(self, **kwargs) -> Dict[str, Any]:
        """
        配当成長フィルタを構築

        すべてライブプローブで検証済みのトークンに落ちる（GROUND_TRUTH.md）：
        - 時価総額：ミッド以上 (cap_midover)
        - 配当利回り：2%以上 (fa_div_2to)
        - EPS 5年成長率：プラス (fa_eps5years_pos)
        - EPS QoQ成長率：プラス (fa_epsqoq_pos)
        - EPS YoY成長率：プラス (fa_epsyoy_pos)
        - PBR：5以下 (fa_pb_u5)
        - PER：30以下 (fa_pe_u30)
        - 売上5年成長率：プラス (fa_sales5years_pos)
        - 売上QoQ成長率：プラス (fa_salesqoq_pos)
        - 地域：アメリカ (geo_usa)
        - 株式のみ (ind_stocksonly)
        - ソートはクライアント側（sma200 に対応する o= トークンは無い）

        Note:
            ``min_dividend_growth`` は受け付けない。配当成長率のフィルタ
            トークンはFinvizに存在せず（プローブ: ``fa_divgrowth1_o5`` は
            無視され、-58.97%の銘柄まで残った）、StockDataにも該当フィールドが
            無いためクライアント側でも判定できない（audit B2）。
        """
        filters = {}

        # デフォルト条件を設定
        # 時価総額：ミッド以上
        filters["market_cap"] = kwargs.get("market_cap", "midover")

        # 配当利回り：2%以上
        filters["dividend_yield_min"] = kwargs.get("min_dividend_yield", 2.0)

        # EPS成長率条件
        filters["eps_growth_5y_positive"] = kwargs.get("eps_growth_5y_positive", True)
        filters["eps_growth_qoq_positive"] = kwargs.get("eps_growth_qoq_positive", True)
        filters["eps_growth_yoy_positive"] = kwargs.get("eps_growth_yoy_positive", True)

        # バリュエーション条件
        filters["pb_ratio_max"] = kwargs.get("max_pb_ratio", 5.0)
        filters["pe_ratio_max"] = kwargs.get("max_pe_ratio", 30.0)

        # 売上成長率条件
        filters["sales_growth_5y_positive"] = kwargs.get(
            "sales_growth_5y_positive", True
        )
        filters["sales_growth_qoq_positive"] = kwargs.get(
            "sales_growth_qoq_positive", True
        )

        # 地域：アメリカ
        if kwargs.get("country") is not None:
            filters["country"] = kwargs["country"]
        elif "country" not in kwargs:
            filters["country"] = "USA"

        # 株式のみ（ind_stocksonly）。``stocks_only`` は ft=4 用の別キーなので
        # 実トークンを出す instrument_type を使う。
        if kwargs.get("stocks_only", True):
            filters["instrument_type"] = "stock"

        # ソートはクライアント側で行うため、o= には渡さない
        # （sma200 に対応する検証済みの o= トークンが無い: audit B2）。

        # 追加条件があれば設定
        if "max_dividend_yield" in kwargs and kwargs["max_dividend_yield"] is not None:
            filters["dividend_yield_max"] = kwargs["max_dividend_yield"]

        optional = {
            "payout_ratio_min": kwargs.get("min_payout_ratio"),
            "payout_ratio_max": kwargs.get("max_payout_ratio"),
            "roe_min": kwargs.get("min_roe"),
            "debt_equity_max": kwargs.get("max_debt_equity"),
        }
        for key, value in optional.items():
            if value is not None:
                filters[key] = value

        # None を渡された条件はフィルタから消す（"適用した" と表示しないため）
        return {key: value for key, value in filters.items() if value is not None}

    def _build_etf_filters(self, **kwargs) -> Dict[str, Any]:
        """ETFフィルタを構築（サーバー側はETF universe、残りはクライアント側）

        Finvizで検証できたETF向けトークンは ``ind_exchangetradedfund``
        （5,580行 = ETFのみ）だけ。``etf_netexpense_u0.2`` と
        ``etf_aum_o10000`` はどちらも黙って無視された（経費率0.95%やAUM
        $81,491のETFが残った）ので、AUM・経費率・資産クラスは取得済みの
        列（Assets Under Management / Net Expense Ratio / Asset Type）を
        使ってクライアント側で適用する（audit B3）。
        """
        filters: Dict[str, Any] = {"instrument_type": "etf"}

        # サーバー側で効かせられる汎用フィルタはここで通す
        for kwarg, filter_key in (
            ("min_price", "price_min"),
            ("max_price", "price_max"),
            ("min_avg_volume", "avg_volume_min"),
        ):
            if kwargs.get(kwarg) is not None:
                filters[filter_key] = kwargs[kwarg]

        return filters

    def _build_earnings_premarket_filters(self) -> Dict[str, Any]:
        """
        寄り付き前決算フィルタを構築

        デフォルト条件：
        - 時価総額：ラージ以上 (cap_largeover)
        - 決算発表：今日の寄り付き前 (earningsdate_todaybefore)
        - 平均出来高：100K以上 (sh_avgvol_o100)
        - 株価：30以上 (sh_price_o30)
        - 価格変動：2%以上上昇 (ta_change_u2)
        - 株式のみ (ft=4)
        - 価格変動降順ソート (o=-change)
        - 最大結果件数：60件 (ar=60)
        """
        filters = {}

        # デフォルト条件を設定
        # 決算発表タイミング：今日の寄り付き前
        filters["earnings_date"] = "today_before"

        # 時価総額：ラージ以上
        filters["market_cap"] = "largeover"

        # 平均出来高：100K以上
        filters["avg_volume_min"] = 100000

        # 株価：30以上
        filters["price_min"] = 30.0

        # 価格変動：2%以上上昇
        filters["price_change_min"] = 2.0

        # 株式のみ
        filters["stocks_only"] = True

        # ソート条件（価格変動降順）
        filters["sort_by"] = "price_change"
        filters["sort_order"] = "desc"

        # 最大結果件数
        filters["max_results"] = 60

        return filters

    def _build_earnings_afterhours_filters(self) -> Dict[str, Any]:
        """
        引け後決算・時間外取引フィルタを構築

        デフォルト条件：
        - 時間外取引変動：2%以上上昇 (ah_change_u2)
        - 時価総額：ラージ以上 (cap_largeover)
        - 決算発表：今日の引け後 (earningsdate_todayafter)
        - 平均出来高：100K以上 (sh_avgvol_o100)
        - 株価：30以上 (sh_price_o30)
        - 株式のみ (ft=4)
        - 時間外変動降順ソート (o=-afterchange)
        - 最大結果件数：60件 (ar=60)
        """
        filters = {}

        # デフォルト条件を設定
        # 決算発表タイミング：今日の引け後
        filters["earnings_date"] = "today_after"

        # 時価総額：ラージ以上
        filters["market_cap"] = "largeover"

        # 平均出来高：100K以上
        filters["avg_volume_min"] = 100000

        # 株価：30以上
        filters["price_min"] = 30.0

        # 時間外取引変動：2%以上上昇
        filters["afterhours_change_min"] = 2.0

        # 株式のみ
        filters["stocks_only"] = True

        # ソート条件（時間外変動降順）
        filters["sort_by"] = "afterhours_change"
        filters["sort_order"] = "desc"

        # 最大結果件数
        filters["max_results"] = 60

        return filters

    def _build_earnings_trading_filters(self) -> Dict[str, Any]:
        """
        決算トレードフィルタを構築（固定条件）

        固定フィルタ: f=cap_largeover,earningsdate_yesterdayafter|todaybefore,fa_epsrev_ep,fa_netmargin_3to,sh_avgvol_o200,sh_price_o30,ta_change_u,ta_perf_0to-4w&ft=4&o=-epssurprise&ar=60

        固定条件：
        - 時価総額：ラージ以上 (cap_largeover)
        - 決算発表：昨日の引け後または今日の寄り付き前 (earningsdate_yesterdayafter|todaybefore)
        - EPS予想：上方修正 (fa_epsrev_ep)
        - ネットマージン：3%以上 (fa_netmargin_3to)
        - 平均出来高：200K以上 (sh_avgvol_o200)
        - 株価：$30以上 (sh_price_o30)
        - 価格変動：上昇 (ta_change_u)
        - 4週パフォーマンス：0%以上 (ta_perf_0to-4w)
        - 株式のみ (ft=4)
        - EPSサプライズ降順ソート (o=-epssurprise)
        - 最大結果件数：60件 (ar=60)
        """
        # 固定条件を設定
        filters = {
            # 決算発表期間：昨日の引け後または今日の寄り付き前
            "earnings_recent": True,
            # 時価総額：ラージ以上
            "market_cap": "largeover",
            # EPS予想：上方修正
            "earnings_revision_positive": True,
            # ネットマージン：3%以上
            "net_margin_min": 3.0,
            # 平均出来高：200K以上
            "avg_volume_min": 200000,
            # 株価：$30以上
            "price_min": 30.0,
            # 価格変動：上昇
            "price_change_positive": True,
            # 4週パフォーマンス：0%以上（`0to-4w` = 4週騰落率 >= 0%）
            "performance_4w_range": "0_to_negative_4w",
            # 株式のみ
            "stocks_only": True,
            # ソート条件（EPSサプライズ降順）
            "sort_by": "eps_surprise",
            "sort_order": "desc",
            # 最大結果件数
            "max_results": 60,
            # earnings_trading_screener専用の識別子
            "screener_type": "earnings_trading",
        }

        return filters

    def _build_earnings_positive_surprise_filters(self, **kwargs) -> Dict[str, Any]:
        """決算ポジティブサプライズフィルタを構築"""
        filters = {}

        filters["earnings_date"] = "this_week"

        filters["market_cap"] = "smallover"

        if "min_price" in kwargs:
            filters["price_min"] = kwargs["min_price"]

        # 成長性フィルタ
        growth_criteria = kwargs.get("growth_criteria", {})
        if growth_criteria.get("min_eps_qoq_growth"):
            filters["eps_growth_min"] = growth_criteria["min_eps_qoq_growth"]

        # パフォーマンスフィルタ
        performance_criteria = kwargs.get("performance_criteria", {})
        if performance_criteria.get("above_sma200"):
            filters["sma200_above"] = True

        return filters

    def upcoming_earnings_screener(self, **kwargs) -> List[UpcomingEarningsData]:
        """
        来週決算予定銘柄のスクリーニング

        Args:
            earnings_period: 決算発表期間 ('next_week', 'next_2_weeks', 'next_month')
            market_cap: 時価総額フィルタ
            min_price: 最低株価
            min_avg_volume: 最低平均出来高
            target_sectors: 対象セクター
            max_results: 最大取得件数
            sort_by: ソート基準
            sort_order: ソート順序

        Returns:
            UpcomingEarningsData のリスト（該当なしの場合は空リスト）

        Raises:
            FinvizAPIError: リクエスト自体が失敗した場合（「該当なし」にしない）
        """
        # フィルタを構築
        filters = self._build_upcoming_earnings_filters(**kwargs)

        # Finvizからデータを取得
        raw_results = self.screen_stocks(filters)

        # UpcomingEarningsDataに変換
        results = []
        for stock in raw_results:
            upcoming_data = self._convert_to_upcoming_earnings_data(stock, **kwargs)
            if upcoming_data:
                results.append(upcoming_data)

        # ソート
        sort_by = kwargs.get("sort_by", "earnings_date")
        sort_order = kwargs.get("sort_order", "asc")
        results = self._sort_upcoming_earnings_results(results, sort_by, sort_order)

        # 件数制限
        max_results = kwargs.get("max_results", 100)
        return results[:max_results]

    def earnings_winners_screener(self, **kwargs) -> List[StockData]:
        """
        決算後上昇銘柄のスクリーニング（決算勝ち組）

        Args:
            earnings_period: 決算発表期間
            market_cap: 時価総額フィルタ
            min_price: 最低株価
            min_avg_volume: 最低平均出来高
            min_eps_growth_qoq: 最低EPS前四半期比成長率
            min_eps_revision: 最低EPS予想改訂率
            min_sales_growth_qoq: 最低売上前四半期比成長率
            min_weekly_performance: 週次パフォーマンスフィルタ
            sma200_filter: 200日移動平均線上のフィルタ
            target_sectors: 対象セクター
            max_results: 最大取得件数
            sort_by: ソート基準
            sort_order: ソート順序

        Returns:
            StockData オブジェクトのリスト（該当なしの場合は空リスト）

        Raises:
            FinvizAPIError: リクエスト自体が失敗した場合（「該当なし」にしない）
        """
        # フィルタを構築
        filters = self._build_earnings_winners_filters(**kwargs)

        # Finvizからデータを取得
        results = self.screen_stocks(filters)

        # ソートしてから件数を切る（順序が先、切り取りは後: audit B7）
        sort_by = kwargs.get("sort_by", "performance_1w")
        reverse = kwargs.get("sort_order", "desc") == "desc"

        sort_keys = {
            "performance_1w": lambda x: x.performance_1w,
            "eps_growth_qoq": lambda x: x.eps_growth_qtr,
            # 宣伝だけされて実装が無かった（結果は逆ティッカー順のまま:
            # audit B18）。EPS Surprise 列は取得済みなのでここで並べ替える。
            "eps_surprise": lambda x: x.eps_surprise,
            "price_change": lambda x: x.price_change,
            "volume": lambda x: x.volume,
        }
        if sort_by not in sort_keys:
            raise ValueError(
                f"Unsupported sort_by for earnings_winners_screener: {sort_by!r}. "
                f"Valid values: {', '.join(sorted(sort_keys))}"
            )
        results = _sorted_none_last(results, key=sort_keys[sort_by], reverse=reverse)

        # 件数制限
        max_results = kwargs.get("max_results", 50)
        return results[:max_results] if max_results else results

    def _build_earnings_winners_filters(self, **kwargs) -> Dict[str, Any]:
        """決算後上昇銘柄スクリーニング用フィルタを構築"""
        filters = {}

        # 決算発表期間（直接指定されたearnings_dateが優先）
        if "earnings_date" in kwargs:
            filters["earnings_date"] = kwargs["earnings_date"]
        else:
            earnings_period = kwargs.get("earnings_period", "this_week")
            if earnings_period == "this_week":
                filters["earnings_date"] = "thisweek"
            elif earnings_period == "yesterday":
                filters["earnings_date"] = "yesterday"
            elif earnings_period == "today":
                filters["earnings_date"] = "today"
            else:
                filters["earnings_date"] = "thisweek"

        # 時価総額（デフォルト：small over）
        filters["market_cap"] = self._resolved_market_cap(
            kwargs.get("market_cap", "smallover")
        )

        # 価格（デフォルト：10以上）
        min_price = kwargs.get("min_price", 10.0)
        if min_price:
            filters["price_min"] = min_price

        # 平均出来高（デフォルト：500K以上）
        min_avg_volume = self._requested_avg_volume(kwargs, default=500000)
        if min_avg_volume is not None:
            # 数値と文字列の両方をサポート
            finviz_volume = self._convert_volume_to_finviz_format(min_avg_volume)
            filters["avg_volume_min"] = finviz_volume

        # EPS前四半期比成長率（デフォルト：10%以上）
        min_eps_growth_qoq = kwargs.get("min_eps_growth_qoq", 10.0)
        if min_eps_growth_qoq:
            filters["eps_growth_qoq_min"] = min_eps_growth_qoq

        # EPS予想改訂（デフォルト：5%以上）
        min_eps_revision = kwargs.get("min_eps_revision", 5.0)
        if min_eps_revision:
            filters["eps_revision_min"] = min_eps_revision

        # 売上前四半期比成長率（デフォルト：5%以上）
        min_sales_growth_qoq = kwargs.get("min_sales_growth_qoq", 5.0)
        if min_sales_growth_qoq:
            filters["sales_growth_qoq_min"] = min_sales_growth_qoq

        # 週次パフォーマンス（デフォルト：5日〜1週間）
        min_weekly_performance = kwargs.get("min_weekly_performance", "5to-1w")
        if min_weekly_performance:
            filters["weekly_performance"] = min_weekly_performance

        # 200日移動平均線上（デフォルト：True）
        sma200_filter = kwargs.get("sma200_filter", True)
        if sma200_filter:
            filters["sma200_above"] = True

        # セクター（デフォルト：主要セクター）
        target_sectors = kwargs.get(
            "target_sectors",
            [
                "Technology",
                "Industrials",
                "Healthcare",
                "Communication Services",
                "Consumer Cyclical",
                "Financial Services",
            ],
        )
        if target_sectors:
            filters["sectors"] = target_sectors

        # 結果数制限はここでは渡さない: フィルタに max_results を入れると
        # Finvizが返した順（逆ティッカー順）のままCSVが切り詰められ、その後の
        # ソートが「任意のN件を並べ替えたもの」になる（audit B7）。
        # 切り取りはソート後にスクリーナー側で行う。

        return filters

    # Advertised earnings periods -> what actually runs. Only tokens/grammars
    # verified against the live API are used (GROUND_TRUTH.md):
    # ``earningsdate_nextmonth`` and ``earningsdate_nextdays10`` DO NOT EXIST
    # (both returned the full 11,532-row universe), while the date-range form
    # ``earningsdate_MM-DD-YYYYxMM-DD-YYYY`` does (1,607 rows, all inside the
    # window). ``next_2_weeks``/``next_month`` therefore run as explicit date
    # ranges instead of the wrong fixed tokens they used to send: nextdays5
    # (5 business days) and thismonth (the *current* month) - audit B15.
    EARNINGS_PERIOD_DAYS = {
        "next_2_weeks": 14,
        "next_month": 30,
    }
    EARNINGS_PERIOD_TOKENS = {
        "next_week": "nextweek",
        "next_5_days": "nextdays5",
        "this_week": "thisweek",
        "this_month": "thismonth",
    }

    @staticmethod
    def resolve_earnings_date(earnings_date: Any) -> Any:
        """Resolve an ``earnings_date`` value to what will actually be sent.

        Values whose window has no Finviz token (``within_2_weeks``) become an
        explicit ``MM-DD-YYYYxMM-DD-YYYY`` range (US/Eastern) so the filter
        dict - and therefore the printed criteria - hold the real query.
        """
        if (
            isinstance(earnings_date, str)
            and earnings_date in EARNINGS_DATE_TOKENS
            and EARNINGS_DATE_TOKENS[earnings_date] is None
        ):
            resolved = finviz_date_range(EARNINGS_DATE_WINDOW_DAYS[earnings_date])
            logger.info(
                "earnings_date=%s has no Finviz token; running it as the "
                "explicit window %s",
                earnings_date,
                resolved,
            )
            return resolved
        return earnings_date

    @classmethod
    def earnings_period_to_finviz(cls, earnings_period: Optional[str]) -> Any:
        """Resolve an advertised ``earnings_period`` to a real Finviz value."""
        period = earnings_period or "next_week"
        if period in cls.EARNINGS_PERIOD_TOKENS:
            return cls.EARNINGS_PERIOD_TOKENS[period]
        if period in cls.EARNINGS_PERIOD_DAYS:
            # US/Eastern, not the server's local zone: Finviz's calendar is a
            # US market calendar, so "the next 14 days" must start from the
            # Eastern date (a Tokyo box would otherwise ask for tomorrow's
            # window, an LA box for yesterday's after 21:00 local).
            return finviz_date_range(cls.EARNINGS_PERIOD_DAYS[period])
        raise ValueError(
            f"Unsupported earnings_period: {earnings_period!r}. Valid values: "
            f"{', '.join(sorted(cls.EARNINGS_PERIOD_TOKENS) + sorted(cls.EARNINGS_PERIOD_DAYS))}"
        )

    @classmethod
    def describe_earnings_period(cls, earnings_period: Optional[str]) -> str:
        """Human label that matches what the period actually filters on."""
        period = earnings_period or "next_week"
        labels = {
            "next_week": "next week (earningsdate_nextweek)",
            "next_5_days": "next 5 business days (earningsdate_nextdays5)",
            "this_week": "this week (earningsdate_thisweek)",
            "this_month": "the current month (earningsdate_thismonth)",
        }
        if period in labels:
            return labels[period]
        days = cls.EARNINGS_PERIOD_DAYS.get(period)
        if days:
            return f"the next {days} calendar days (explicit earningsdate range)"
        return str(period)

    @staticmethod
    def _resolved_market_cap(market_cap: Any) -> Optional[str]:
        """Validate a market-cap request, raising instead of dropping it.

        ``market_cap in MARKET_CAP_FILTERS`` used to gate this, and the table
        was missing ``largeover``/``microover`` - so those requests were
        silently discarded and the screen ran over every cap tier (audit B22).
        """
        if not market_cap:
            return None
        code = resolve_market_cap_code(market_cap)
        if not code:
            raise ValueError(
                f"Unknown market_cap: {market_cap!r}. Valid values: "
                f"{', '.join(sorted(MARKET_CAP_FILTERS))}"
            )
        return code

    @staticmethod
    def _requested_avg_volume(kwargs: Dict[str, Any], default: Any = None) -> Any:
        """Read the average-volume minimum under any of its spellings.

        The MCP tools stored it as ``avg_volume_min``/``average_volume`` while
        this builder only ever read ``min_avg_volume``, so a caller-supplied
        threshold was dropped and the 500K default silently applied instead
        (audit B4).
        """
        for key in ("min_avg_volume", "avg_volume_min", "average_volume"):
            if kwargs.get(key) is not None:
                return kwargs[key]
        return default

    def _build_upcoming_earnings_filters(self, **kwargs) -> Dict[str, Any]:
        """来週決算予定スクリーニング用フィルタを構築"""
        filters = {}

        # 決算発表期間（直接指定されたearnings_dateが優先）
        if kwargs.get("earnings_date"):
            # 直接指定されたearnings_dateパラメータを使用
            filters["earnings_date"] = kwargs["earnings_date"]
        else:
            filters["earnings_date"] = self.earnings_period_to_finviz(
                kwargs.get("earnings_period", "next_week")
            )

        # 時価総額（デフォルト：small over）
        filters["market_cap"] = self._resolved_market_cap(
            kwargs.get("market_cap", "smallover")
        )

        # 価格（デフォルト：10以上）
        min_price = kwargs.get("min_price", 10)
        if min_price:
            filters["price_min"] = min_price

        # 平均出来高（デフォルト：500K = o500）
        min_avg_volume = self._requested_avg_volume(kwargs, default=500000)
        if min_avg_volume is not None:
            # 数値と文字列の両方をサポート
            finviz_volume = self._convert_volume_to_finviz_format(min_avg_volume)
            filters["avg_volume_min"] = finviz_volume

        # 件数制限はソート後にクライアント側で適用する（audit B7）

        # セクター（デフォルト：主要セクター）
        target_sectors = kwargs.get(
            "target_sectors",
            [
                "Technology",
                "Industrials",
                "Healthcare",
                "Communication Services",
                "Consumer Cyclical",
                "Financial Services",
                "Consumer Defensive",
                "Basic Materials",
            ],
        )
        if target_sectors:
            filters["sectors"] = target_sectors

        return filters

    def _convert_to_upcoming_earnings_data(
        self, stock: StockData, **kwargs
    ) -> Optional[UpcomingEarningsData]:
        """StockDataをUpcomingEarningsDataに変換"""
        try:
            # 基本情報
            upcoming_data = UpcomingEarningsData(
                ticker=stock.ticker,
                company_name=stock.company_name or "",
                sector=stock.sector or "",
                industry=stock.industry or "",
                earnings_date=stock.earnings_date or "",
                earnings_timing="unknown",  # Finvizからは取得困難
            )

            # 基本株価データ
            upcoming_data.current_price = stock.price
            upcoming_data.market_cap = stock.market_cap
            upcoming_data.avg_volume = stock.avg_volume

            # 評価・推奨データ
            upcoming_data.pe_ratio = stock.pe_ratio
            upcoming_data.target_price = stock.target_price
            upcoming_data.analyst_recommendation = stock.analyst_recommendation

            # 目標価格までのアップサイド計算
            if stock.target_price and stock.price and stock.price > 0:
                upcoming_data.target_price_upside = (
                    (stock.target_price - stock.price) / stock.price
                ) * 100

            # リスク評価指標
            upcoming_data.volatility = stock.volatility
            upcoming_data.beta = stock.beta
            upcoming_data.short_interest = stock.short_interest
            upcoming_data.insider_ownership = stock.insider_ownership
            upcoming_data.institutional_ownership = stock.institutional_ownership

            # パフォーマンス・テクニカル指標
            upcoming_data.performance_1w = stock.performance_1w
            upcoming_data.performance_1m = stock.performance_1m
            upcoming_data.rsi = stock.rsi

            return upcoming_data

        except Exception as e:
            logger.warning(
                f"Failed to convert stock data to upcoming earnings data: {e}"
            )
            return None

    def _sort_upcoming_earnings_results(
        self, results: List[UpcomingEarningsData], sort_by: str, sort_order: str
    ) -> List[UpcomingEarningsData]:
        """来週決算予定結果をソート

        ``earnings_date`` は文字列ではなく datetime に直してから並べる:
        "M/D/YYYY h:mm" を辞書順で比べると 5/13 が 5/2 の前に来る（audit B16）。
        """
        reverse = (sort_order or "asc").lower() == "desc"

        sort_keys = {
            "earnings_date": lambda x: parse_earnings_datetime(x.earnings_date),
            "market_cap": lambda x: x.market_cap,
            "target_price_upside": lambda x: x.target_price_upside,
            "volatility": lambda x: x.volatility,
            "ticker": lambda x: x.ticker,
        }
        if sort_by not in sort_keys:
            raise ValueError(
                f"Unsupported sort_by for upcoming_earnings_screener: {sort_by!r}. "
                f"Valid values: {', '.join(sorted(sort_keys))}"
            )
        return _sorted_none_last(results, key=sort_keys[sort_by], reverse=reverse)

    def _build_trend_reversion_filters(self, **kwargs) -> Dict[str, Any]:
        """トレンド反転フィルタを構築

        Note:
            ``market_cap="mid_large"`` は ``cap_mid_large`` という存在しない
            トークンになっていた（＝時価総額フィルタ無しで全銘柄）。実在する
            ``cap_midover``（$2B以上）に解決する（audit B5）。
            ``exclude_sectors`` はここには入れない: Finvizに除外構文が無く、
            スクリーナー側でクライアント適用する。
        """
        filters = {}

        market_cap = kwargs.get("market_cap") or "midover"
        filters["market_cap"] = market_cap

        if kwargs.get("eps_growth_qoq") is not None:
            filters["eps_growth_qoq_min"] = kwargs["eps_growth_qoq"]

        if kwargs.get("revenue_growth_qoq") is not None:
            # fa_salesqoq_o<N>（売上QoQ）に落ちる
            filters["sales_growth_qoq_min"] = kwargs["revenue_growth_qoq"]

        if kwargs.get("rsi_max") is not None:
            filters["rsi_max"] = kwargs["rsi_max"]

        if kwargs.get("sectors"):
            filters["sectors"] = kwargs["sectors"]

        return filters

    def _build_relative_volume_filters(self, **kwargs) -> Dict[str, Any]:
        """相対出来高フィルタを構築"""
        filters = {}

        # 必須パラメータ
        filters["relative_volume_min"] = kwargs["min_relative_volume"]

        if "min_price" in kwargs:
            filters["price_min"] = kwargs["min_price"]

        if "sectors" in kwargs and kwargs["sectors"]:
            filters["sectors"] = kwargs["sectors"]

        return filters

    def _build_technical_analysis_filters(self, **kwargs) -> Dict[str, Any]:
        """テクニカル分析フィルタを構築"""
        filters = {}

        if "rsi_min" in kwargs:
            filters["rsi_min"] = kwargs["rsi_min"]

        if "rsi_max" in kwargs:
            filters["rsi_max"] = kwargs["rsi_max"]

        if "price_vs_sma20" in kwargs:
            if kwargs["price_vs_sma20"] == "above":
                filters["sma20_above"] = True
            elif kwargs["price_vs_sma20"] == "below":
                filters["sma20_below"] = True

        if "price_vs_sma50" in kwargs:
            if kwargs["price_vs_sma50"] == "above":
                filters["sma50_above"] = True
            elif kwargs["price_vs_sma50"] == "below":
                filters["sma50_below"] = True

        if "price_vs_sma200" in kwargs:
            if kwargs["price_vs_sma200"] == "above":
                filters["sma200_above"] = True
            elif kwargs["price_vs_sma200"] == "below":
                filters["sma200_below"] = True

        if "min_price" in kwargs:
            filters["price_min"] = kwargs["min_price"]

        if "min_volume" in kwargs:
            filters["volume_min"] = kwargs["min_volume"]

        if "sectors" in kwargs and kwargs["sectors"]:
            filters["sectors"] = kwargs["sectors"]

        return filters
