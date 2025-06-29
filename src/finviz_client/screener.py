import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

from .base import FinvizClient
from ..models import StockData, ScreeningResult, UpcomingEarningsData, MARKET_CAP_FILTERS

logger = logging.getLogger(__name__)

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
            min_volume: 最低出来高
            sectors: 対象セクター
            premarket_price_change: 寄り付き前価格変動フィルタ
            afterhours_price_change: 時間外価格変動フィルタ
            
        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_earnings_filters(**kwargs)
        return self.screen_stocks(filters)
    
    def volume_surge_screener(self, **kwargs) -> List[StockData]:
        """
        出来高急増を伴う上昇銘柄のスクリーニング
        
        Args:
            market_cap: 時価総額フィルタ
            min_price: 最低株価
            min_avg_volume: 最低平均出来高
            min_relative_volume: 最低相対出来高倍率
            min_price_change: 最低価格変動率(%)
            sma_filter: 移動平均線フィルタ
            stocks_only: 株式のみ（ETF除外）
            max_results: 最大取得件数
            sort_by: ソート基準
            sectors: 対象セクター
            exclude_sectors: 除外セクター
            
        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_volume_surge_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        # 結果の制限とソート
        max_results = kwargs.get('max_results', 50)
        sort_by = kwargs.get('sort_by', 'price_change')
        
        # ソート
        if sort_by == 'price_change':
            results.sort(key=lambda x: x.price_change or 0, reverse=True)
        elif sort_by == 'relative_volume':
            results.sort(key=lambda x: x.relative_volume or 0, reverse=True)
        elif sort_by == 'volume':
            results.sort(key=lambda x: x.volume or 0, reverse=True)
        
        return results[:max_results]
    
    def uptrend_screener(self, **kwargs) -> List[StockData]:
        """
        上昇トレンド銘柄のスクリーニング
        
        Args:
            trend_type: トレンドタイプ
            sma_period: 移動平均期間
            relative_volume: 相対出来高最低値
            price_change: 価格変化率最低値
            max_results: 最大取得件数
            
        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_uptrend_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        # ソートと制限
        max_results = kwargs.get('max_results', 100)  # デフォルト100件に制限
        sort_by = kwargs.get('sort_by', 'eps_growth_yoy')
        sort_order = kwargs.get('sort_order', 'desc')
        
        # ソート処理（既にFinvizでソートされているが、念のため）
        if sort_by == 'eps_growth_yoy':
            results.sort(key=lambda x: x.eps_growth_this_y or 0, reverse=(sort_order == 'desc'))
        elif sort_by == 'price_change':
            results.sort(key=lambda x: x.price_change or 0, reverse=(sort_order == 'desc'))
        elif sort_by == 'market_cap':
            results.sort(key=lambda x: x.market_cap or 0, reverse=(sort_order == 'desc'))
        
        return results[:max_results]
    
    def dividend_growth_screener(self, **kwargs) -> List[StockData]:
        """
        配当成長銘柄のスクリーニング
        
        Args:
            min_dividend_yield: 最低配当利回り
            max_dividend_yield: 最高配当利回り
            min_dividend_growth: 最低配当成長率
            min_payout_ratio: 最低配当性向
            max_payout_ratio: 最高配当性向
            min_roe: 最低ROE
            max_debt_equity: 最高負債比率
            max_results: 最大取得件数
            
        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_dividend_growth_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        # 結果制限とソート
        max_results = kwargs.get('max_results', 100)
        sort_by = kwargs.get('sort_by', 'dividend_yield')
        sort_order = kwargs.get('sort_order', 'desc')
        
        # ソート処理
        if sort_by == 'dividend_yield':
            results.sort(key=lambda x: x.dividend_yield or 0, reverse=(sort_order == 'desc'))
        elif sort_by == 'market_cap':
            results.sort(key=lambda x: x.market_cap or 0, reverse=(sort_order == 'desc'))
        
        return results[:max_results]
    
    def etf_screener(self, **kwargs) -> List[StockData]:
        """
        ETF戦略用スクリーニング
        
        Args:
            strategy_type: 戦略タイプ
            asset_class: 資産クラス
            min_aum: 最低運用資産額
            max_expense_ratio: 最高経費率
            max_results: 最大取得件数
            
        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_etf_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        # 結果制限とソート
        max_results = kwargs.get('max_results', 50)
        sort_by = kwargs.get('sort_by', 'aum')
        sort_order = kwargs.get('sort_order', 'desc')
        
        # ソート処理
        if sort_by == 'aum':
            results.sort(key=lambda x: x.aum or 0, reverse=(sort_order == 'desc'))
        elif sort_by == 'expense_ratio':
            results.sort(key=lambda x: x.net_expense_ratio or 0, reverse=(sort_order == 'asc'))
        
        return results[:max_results]
    
    def earnings_premarket_screener(self, **kwargs) -> List[StockData]:
        """
        寄り付き前決算発表で上昇している銘柄のスクリーニング
        
        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_earnings_premarket_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        # ソートと制限
        max_results = kwargs.get('max_results', 60)
        sort_by = kwargs.get('sort_by', 'change_percent')
        sort_order = kwargs.get('sort_order', 'desc')
        
        if sort_by == 'change_percent':
            results.sort(key=lambda x: x.price_change or 0, reverse=(sort_order == 'desc'))
        elif sort_by == 'relative_volume':
            results.sort(key=lambda x: x.relative_volume or 0, reverse=(sort_order == 'desc'))
        
        return results[:max_results]
    
    def earnings_afterhours_screener(self, **kwargs) -> List[StockData]:
        """
        引け後決算発表で時間外取引上昇銘柄のスクリーニング
        
        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_earnings_afterhours_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        # ソートと制限
        max_results = kwargs.get('max_results', 60)
        sort_by = kwargs.get('sort_by', 'afterhours_change_percent')
        sort_order = kwargs.get('sort_order', 'desc')
        
        if sort_by == 'afterhours_change_percent':
            results.sort(key=lambda x: x.afterhours_change_percent or 0, reverse=(sort_order == 'desc'))
        
        return results[:max_results]
    
    def earnings_trading_screener(self, **kwargs) -> List[StockData]:
        """
        決算トレード対象銘柄のスクリーニング
        
        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_earnings_trading_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        # ソートと制限
        max_results = kwargs.get('max_results', 60)
        sort_by = kwargs.get('sort_by', 'eps_surprise')
        
        if sort_by == 'eps_surprise':
            results.sort(key=lambda x: x.eps_surprise or 0, reverse=True)
        elif sort_by == 'volatility':
            results.sort(key=lambda x: x.volatility or 0, reverse=True)
        
        return results[:max_results]
    
    def earnings_positive_surprise_screener(self, **kwargs) -> List[StockData]:
        """
        今週決算発表でポジティブサプライズがあって上昇している銘柄のスクリーニング
        
        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_earnings_positive_surprise_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        # ソートと制限
        max_results = kwargs.get('max_results', 50)
        sort_by = kwargs.get('sort_by', 'eps_qoq_growth')
        
        if sort_by == 'eps_qoq_growth':
            results.sort(key=lambda x: x.eps_growth_qtr or 0, reverse=True)
        elif sort_by == 'performance_1w':
            results.sort(key=lambda x: x.performance_1w or 0, reverse=True)
        
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
        
        # 結果制限とソート
        max_results = kwargs.get('max_results', 50)
        sort_by = kwargs.get('sort_by', 'rsi')
        sort_order = kwargs.get('sort_order', 'asc')  # RSIは低い順
        
        # ソート処理
        if sort_by == 'rsi':
            results.sort(key=lambda x: x.rsi or 0, reverse=(sort_order == 'desc'))
        elif sort_by == 'eps_growth_qoq':
            results.sort(key=lambda x: x.eps_growth_qtr or 0, reverse=(sort_order == 'desc'))
        
        return results[:max_results]
    
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
        results.sort(key=lambda x: x.relative_volume or 0, reverse=True)
        
        max_results = kwargs.get('max_results', 50)
        return results[:max_results]
    
    def technical_analysis_screener(self, **kwargs) -> List[StockData]:
        """
        テクニカル分析ベースのスクリーニング
        
        Args:
            rsi_min: RSI最低値
            rsi_max: RSI最高値
            price_vs_sma20: 20日移動平均との関係
            price_vs_sma50: 50日移動平均との関係
            price_vs_sma200: 200日移動平均との関係
            min_price: 最低株価
            min_volume: 最低出来高
            sectors: 対象セクター
            max_results: 最大取得件数
            
        Returns:
            StockData オブジェクトのリスト
        """
        filters = self._build_technical_analysis_filters(**kwargs)
        results = self.screen_stocks(filters)
        
        max_results = kwargs.get('max_results', 50)
        return results[:max_results]
    
    def _build_earnings_filters(self, **kwargs) -> Dict[str, Any]:
        """決算スクリーニング用フィルタを構築"""
        filters = {}
        
        # 決算発表日
        if 'earnings_date' in kwargs:
            filters['earnings_date'] = kwargs['earnings_date']
        
        # 時価総額
        if 'market_cap' in kwargs:
            filters['market_cap'] = kwargs['market_cap']
        
        # 価格範囲
        if 'min_price' in kwargs:
            filters['price_min'] = kwargs['min_price']
        if 'max_price' in kwargs:
            filters['price_max'] = kwargs['max_price']
        
        # 出来高
        if 'min_volume' in kwargs:
            filters['volume_min'] = kwargs['min_volume']
        
        # セクター
        if 'sectors' in kwargs and kwargs['sectors']:
            filters['sectors'] = kwargs['sectors']
        
        return filters
    
    def _build_volume_surge_filters(self, **kwargs) -> Dict[str, Any]:
        """
        出来高急増スクリーニング用フィルタを構築
        
        デフォルト条件：
        - 時価総額：スモール以上 (cap_smallover)
        - 株式のみ：ETF除外 (ind_stocksonly)
        - 平均出来高：100K以上 (sh_avgvol_o100)
        - 株価：10以上 (sh_price_o10)
        - 相対出来高：1.5倍以上 (sh_relvol_o1.5)
        - 価格変動：2%以上上昇 (ta_change_u2)
        - 200日移動平均線上 (ta_sma200_pa)
        - 価格変動降順ソート (o=-change)
        """
        filters = {}
        
        # デフォルト条件を設定
        # 時価総額：スモール以上
        filters['market_cap'] = kwargs.get('market_cap', 'smallover')
        
        # 株式のみ（ETF除外）
        filters['exclude_etfs'] = kwargs.get('stocks_only', True)
        
        # 平均出来高：100K以上
        filters['avg_volume_min'] = kwargs.get('min_avg_volume', 100000)
        
        # 株価：10以上
        filters['price_min'] = kwargs.get('min_price', 10.0)
        
        # 相対出来高：1.5倍以上
        filters['relative_volume_min'] = kwargs.get('min_relative_volume', 1.5)
        
        # 価格変動：2%以上上昇
        filters['price_change_min'] = kwargs.get('min_price_change', 2.0)
        
        # 200日移動平均線上
        sma_filter = kwargs.get('sma_filter', 'above_sma200')
        if sma_filter == 'above_sma200':
            filters['sma200_above'] = True
        elif sma_filter == 'above_sma50':
            filters['sma50_above'] = True
        elif sma_filter == 'above_sma20':
            filters['sma20_above'] = True
        else:
            # デフォルトは200日移動平均線上
            filters['sma200_above'] = True
        
        # ソート条件（価格変動降順）
        filters['sort_by'] = kwargs.get('sort_by', 'price_change')
        filters['sort_order'] = kwargs.get('sort_order', 'desc')
        
        # 追加条件があれば設定
        # セクターフィルタ
        if 'sectors' in kwargs and kwargs['sectors']:
            filters['sectors'] = kwargs['sectors']
        
        if 'exclude_sectors' in kwargs and kwargs['exclude_sectors']:
            filters['exclude_sectors'] = kwargs['exclude_sectors']
        
        return filters
    
    def _build_uptrend_filters(self, **kwargs) -> Dict[str, Any]:
        """
        上昇トレンドフィルタを構築
        
        デフォルト条件（Finvizの推奨設定）：
        - 時価総額：マイクロ以上 (cap_microover)
        - 平均出来高：100K以上 (sh_avgvol_o100)
        - 株価：10以上 (sh_price_o10)
        - 52週高値から30%以内 (ta_highlow52w_a30h)
        - 4週パフォーマンス上昇 (ta_perf2_4wup)
        - 20日移動平均線上 (ta_sma20_pa)
        - 200日移動平均線上 (ta_sma200_pa)
        - 50日移動平均線が200日移動平均線上 (ta_sma50_sa200)
        - EPS成長率（年次）降順ソート (o=-epsyoy1)
        """
        filters = {}
        
        # デフォルト条件を設定（Finviz推奨に合わせる）
        # 時価総額：マイクロ以上（修正）
        filters['market_cap'] = kwargs.get('market_cap', 'microover')
        
        # 平均出来高：100K以上（修正：100000 → 100）
        filters['avg_volume_min'] = kwargs.get('min_avg_volume', 100)  # 100K = 100 * 1000
        
        # 株価：10以上（小数点を除去）
        filters['price_min'] = kwargs.get('min_price', 10)
        
        # 52週高値から30%以内（小数点を除去）
        filters['near_52w_high'] = kwargs.get('near_52w_high', 30)
        
        # 4週パフォーマンス上昇（新規追加）
        filters['performance_4w_positive'] = kwargs.get('performance_4w_positive', True)
        
        # 移動平均線条件
        filters['sma20_above'] = kwargs.get('sma20_above', True)
        filters['sma200_above'] = kwargs.get('sma200_above', True)
        filters['sma50_above_sma200'] = kwargs.get('sma50_above_sma200', True)
        
        # ソート条件（EPS年次成長率降順に修正）
        filters['sort_by'] = kwargs.get('sort_by', 'eps_growth_yoy')
        filters['sort_order'] = kwargs.get('sort_order', 'desc')
        
        # trend_typeに基づく追加条件（デフォルトでは追加しない）
        trend_type = kwargs.get('trend_type', 'basic_uptrend')
        
        # 明示的に指定された場合のみ追加条件を適用
        if trend_type == 'strong_uptrend':
            # 強いトレンド用の追加条件
            if 'price_change' in kwargs:
                filters['price_change_min'] = kwargs['price_change']
            if 'relative_volume' in kwargs:
                filters['relative_volume_min'] = kwargs['relative_volume']
        elif trend_type == 'breakout':
            # ブレイクアウト用の追加条件
            if 'price_change' in kwargs:
                filters['price_change_min'] = kwargs['price_change']
        elif trend_type == 'momentum':
            # モメンタム用の追加条件
            if 'price_change' in kwargs:
                filters['price_change_min'] = kwargs['price_change']
            if 'relative_volume' in kwargs:
                filters['relative_volume_min'] = kwargs['relative_volume']
        
        # 移動平均期間の指定があれば設定
        sma_period = kwargs.get('sma_period')
        if sma_period:
            if sma_period == "20":
                filters['sma20_focus'] = True
            elif sma_period == "50":
                filters['sma50_focus'] = True
            elif sma_period == "200":
                filters['sma200_focus'] = True
        
        # 明示的に指定された場合のみ相対出来高・価格変動を追加
        if 'relative_volume' in kwargs:
            filters['relative_volume_min'] = kwargs['relative_volume']
        if 'price_change' in kwargs:
            filters['price_change_min'] = kwargs['price_change']
        
        # セクターフィルタ
        if 'sectors' in kwargs and kwargs['sectors']:
            filters['sectors'] = kwargs['sectors']
        
        if 'exclude_sectors' in kwargs and kwargs['exclude_sectors']:
            filters['exclude_sectors'] = kwargs['exclude_sectors']
        
        return filters
    
    def _build_dividend_growth_filters(self, **kwargs) -> Dict[str, Any]:
        """
        配当成長フィルタを構築
        
        デフォルト条件：
        - 時価総額：ミッド以上 (cap_midover)
        - 配当利回り：2%以上 (fa_div_o2)
        - EPS 5年成長率：プラス (fa_eps5years_pos)
        - EPS QoQ成長率：プラス (fa_epsqoq_pos)
        - EPS YoY成長率：プラス (fa_epsyoy_pos)
        - PBR：5以下 (fa_pb_u5)
        - PER：30以下 (fa_pe_u30)
        - 売上5年成長率：プラス (fa_sales5years_pos)
        - 売上QoQ成長率：プラス (fa_salesqoq_pos)
        - 地域：アメリカ (geo_usa)
        - 株式のみ (ft=4)
        - 200日移動平均でソート (o=sma200)
        """
        filters = {}
        
        # デフォルト条件を設定
        # 時価総額：ミッド以上
        filters['market_cap'] = kwargs.get('market_cap', 'midover')
        
        # 配当利回り：2%以上
        filters['dividend_yield_min'] = kwargs.get('min_dividend_yield', 2.0)
        
        # EPS成長率条件
        filters['eps_growth_5y_positive'] = kwargs.get('eps_growth_5y_positive', True)
        filters['eps_growth_qoq_positive'] = kwargs.get('eps_growth_qoq_positive', True)
        filters['eps_growth_yoy_positive'] = kwargs.get('eps_growth_yoy_positive', True)
        
        # バリュエーション条件
        filters['pb_ratio_max'] = kwargs.get('max_pb_ratio', 5.0)
        filters['pe_ratio_max'] = kwargs.get('max_pe_ratio', 30.0)
        
        # 売上成長率条件
        filters['sales_growth_5y_positive'] = kwargs.get('sales_growth_5y_positive', True)
        filters['sales_growth_qoq_positive'] = kwargs.get('sales_growth_qoq_positive', True)
        
        # 地域：アメリカ
        filters['country'] = kwargs.get('country', 'USA')
        
        # 株式のみ
        filters['stocks_only'] = kwargs.get('stocks_only', True)
        
        # ソート条件（200日移動平均）
        filters['sort_by'] = kwargs.get('sort_by', 'sma200')
        filters['sort_order'] = kwargs.get('sort_order', 'asc')
        
        # 追加条件があれば設定
        if 'max_dividend_yield' in kwargs:
            filters['dividend_yield_max'] = kwargs['max_dividend_yield']
        
        if 'min_dividend_growth' in kwargs:
            filters['dividend_growth_min'] = kwargs['min_dividend_growth']
        
        if 'min_payout_ratio' in kwargs:
            filters['payout_ratio_min'] = kwargs['min_payout_ratio']
        
        if 'max_payout_ratio' in kwargs:
            filters['payout_ratio_max'] = kwargs['max_payout_ratio']
        
        if 'min_roe' in kwargs:
            filters['roe_min'] = kwargs['min_roe']
        
        if 'max_debt_equity' in kwargs:
            filters['debt_equity_max'] = kwargs['max_debt_equity']
        
        return filters
    
    def _build_etf_filters(self, **kwargs) -> Dict[str, Any]:
        """ETFフィルタを構築"""
        filters = {}
        
        strategy_type = kwargs.get('strategy_type', 'long')
        asset_class = kwargs.get('asset_class', 'equity')
        
        filters['instrument_type'] = 'etf'
        
        if 'min_aum' in kwargs:
            filters['aum_min'] = kwargs['min_aum']
        if 'max_expense_ratio' in kwargs:
            filters['expense_ratio_max'] = kwargs['max_expense_ratio']
        
        return filters
    
    def _build_earnings_premarket_filters(self, **kwargs) -> Dict[str, Any]:
        """
        寄り付き前決算フィルタを構築
        
        デフォルト条件：
        - 時価総額：スモール以上 (cap_smallover)
        - 決算発表：今日の寄り付き前 (earningsdate_todaybefore)
        - 平均出来高：100K以上 (sh_avgvol_o100)
        - 株価：10以上 (sh_price_o10)
        - 価格変動：2%以上上昇 (ta_change_u2)
        - 株式のみ (ft=4)
        - 価格変動降順ソート (o=-change)
        - 最大結果件数：60件 (ar=60)
        """
        filters = {}
        
        # デフォルト条件を設定
        # 決算発表タイミング：今日の寄り付き前
        earnings_timing = kwargs.get('earnings_timing', 'today_before')
        if earnings_timing == 'today_before':
            filters['earnings_date'] = 'today_before'
        elif earnings_timing == 'yesterday_after':
            filters['earnings_date'] = 'yesterday_after'
        elif earnings_timing == 'this_week':
            filters['earnings_date'] = 'this_week'
        
        # 時価総額：スモール以上
        filters['market_cap'] = kwargs.get('market_cap', 'smallover')
        
        # 平均出来高：100K以上
        filters['avg_volume_min'] = kwargs.get('min_avg_volume', 100000)
        
        # 株価：10以上
        filters['price_min'] = kwargs.get('min_price', 10.0)
        
        # 価格変動：2%以上上昇
        filters['price_change_min'] = kwargs.get('min_price_change', 2.0)
        
        # 株式のみ
        filters['stocks_only'] = kwargs.get('stocks_only', True)
        
        # ソート条件（価格変動降順）
        filters['sort_by'] = kwargs.get('sort_by', 'price_change')
        filters['sort_order'] = kwargs.get('sort_order', 'desc')
        
        # 最大結果件数
        filters['max_results'] = kwargs.get('max_results', 60)
        
        # 追加条件があれば設定
        if 'max_price_change' in kwargs:
            filters['price_change_max'] = kwargs['max_price_change']
        
        if 'include_premarket_data' in kwargs:
            filters['include_premarket_data'] = kwargs['include_premarket_data']
        
        if 'sectors' in kwargs and kwargs['sectors']:
            filters['sectors'] = kwargs['sectors']
        
        if 'exclude_sectors' in kwargs and kwargs['exclude_sectors']:
            filters['exclude_sectors'] = kwargs['exclude_sectors']
        
        return filters
    
    def _build_earnings_afterhours_filters(self, **kwargs) -> Dict[str, Any]:
        """
        引け後決算・時間外取引フィルタを構築
        
        デフォルト条件：
        - 時間外取引変動：2%以上上昇 (ah_change_u2)
        - 時価総額：スモール以上 (cap_smallover)
        - 決算発表：今日の引け後 (earningsdate_todayafter)
        - 平均出来高：100K以上 (sh_avgvol_o100)
        - 株価：10以上 (sh_price_o10)
        - 株式のみ (ft=4)
        - 時間外変動降順ソート (o=-afterchange)
        - 最大結果件数：60件 (ar=60)
        """
        filters = {}
        
        # デフォルト条件を設定
        # 決算発表タイミング：今日の引け後
        earnings_timing = kwargs.get('earnings_timing', 'today_after')
        if earnings_timing == 'today_after':
            filters['earnings_date'] = 'today_after'
        elif earnings_timing == 'yesterday_after':
            filters['earnings_date'] = 'yesterday_after'
        elif earnings_timing == 'this_week':
            filters['earnings_date'] = 'this_week'
        
        # 時価総額：スモール以上
        filters['market_cap'] = kwargs.get('market_cap', 'smallover')
        
        # 平均出来高：100K以上
        filters['avg_volume_min'] = kwargs.get('min_avg_volume', 100000)
        
        # 株価：10以上
        filters['price_min'] = kwargs.get('min_price', 10.0)
        
        # 時間外取引変動：2%以上上昇
        filters['afterhours_change_min'] = kwargs.get('min_afterhours_change', 2.0)
        
        # 株式のみ
        filters['stocks_only'] = kwargs.get('stocks_only', True)
        
        # ソート条件（時間外変動降順）
        filters['sort_by'] = kwargs.get('sort_by', 'afterhours_change')
        filters['sort_order'] = kwargs.get('sort_order', 'desc')
        
        # 最大結果件数
        filters['max_results'] = kwargs.get('max_results', 60)
        
        # 追加条件があれば設定
        if 'max_afterhours_change' in kwargs:
            filters['afterhours_change_max'] = kwargs['max_afterhours_change']
        
        if 'include_afterhours_data' in kwargs:
            filters['include_afterhours_data'] = kwargs['include_afterhours_data']
        
        if 'sectors' in kwargs and kwargs['sectors']:
            filters['sectors'] = kwargs['sectors']
        
        if 'exclude_sectors' in kwargs and kwargs['exclude_sectors']:
            filters['exclude_sectors'] = kwargs['exclude_sectors']
        
        return filters
    
    def _build_earnings_trading_filters(self, **kwargs) -> Dict[str, Any]:
        """
        決算トレードフィルタを構築
        
        デフォルト条件：
        - 時価総額：スモール以上 (cap_smallover)
        - 決算発表：昨日の引け後または今日の寄り付き前 (earningsdate_yesterdayafter|todaybefore)
        - EPS予想：上方修正 (fa_epsrev_ep)
        - 平均出来高：200K以上 (sh_avgvol_o200)
        - 株価：10以上 (sh_price_o10)
        - 価格変動：上昇 (ta_change_u)
        - 4週パフォーマンス：0%から下落（下落後回復候補） (ta_perf_0to-4w)
        - ボラティリティ：1倍以上 (ta_volatility_1tox)
        - 株式のみ (ft=4)
        - EPSサプライズ降順ソート (o=-epssurprise)
        - 最大結果件数：60件 (ar=60)
        """
        filters = {}
        
        # デフォルト条件を設定
        # 決算発表期間：昨日の引け後または今日の寄り付き前
        earnings_window = kwargs.get('earnings_window', 'yesterday_after_today_before')
        if earnings_window == 'yesterday_after_today_before':
            filters['earnings_recent'] = True
        elif earnings_window == 'yesterday_after':
            filters['earnings_date'] = 'yesterday_after'
        elif earnings_window == 'today_before':
            filters['earnings_date'] = 'today_before'
        elif earnings_window == 'this_week':
            filters['earnings_date'] = 'this_week'
        
        # 時価総額：スモール以上
        filters['market_cap'] = kwargs.get('market_cap', 'smallover')
        
        # EPS予想：上方修正
        earnings_revision = kwargs.get('earnings_revision', 'eps_revenue_positive')
        if earnings_revision == 'eps_revenue_positive':
            filters['earnings_revision_positive'] = True
        
        # 平均出来高：200K以上
        filters['avg_volume_min'] = kwargs.get('min_avg_volume', 200000)
        
        # 株価：10以上
        filters['price_min'] = kwargs.get('min_price', 10.0)
        
        # 価格変動：上昇
        price_trend = kwargs.get('price_trend', 'positive_change')
        if price_trend == 'positive_change':
            filters['price_change_positive'] = True
        
        # 4週パフォーマンス：0%から下落（下落後回復候補）
        filters['performance_4w_range'] = kwargs.get('performance_4w_range', '0_to_negative_4w')
        
        # ボラティリティ：1倍以上
        filters['volatility_min'] = kwargs.get('min_volatility', 1.0)
        
        # 株式のみ
        filters['stocks_only'] = kwargs.get('stocks_only', True)
        
        # ソート条件（EPSサプライズ降順）
        filters['sort_by'] = kwargs.get('sort_by', 'eps_surprise')
        filters['sort_order'] = kwargs.get('sort_order', 'desc')
        
        # 最大結果件数
        filters['max_results'] = kwargs.get('max_results', 60)
        
        # 追加条件があれば設定
        if 'sectors' in kwargs and kwargs['sectors']:
            filters['sectors'] = kwargs['sectors']
        
        if 'exclude_sectors' in kwargs and kwargs['exclude_sectors']:
            filters['exclude_sectors'] = kwargs['exclude_sectors']
        
        return filters
    
    def _build_earnings_positive_surprise_filters(self, **kwargs) -> Dict[str, Any]:
        """決算ポジティブサプライズフィルタを構築"""
        filters = {}
        
        earnings_period = kwargs.get('earnings_period', 'this_week')
        filters['earnings_date'] = earnings_period
        
        market_cap = kwargs.get('market_cap', 'smallover')
        filters['market_cap'] = market_cap
        
        if 'min_price' in kwargs:
            filters['price_min'] = kwargs['min_price']
        
        # 成長性フィルタ
        growth_criteria = kwargs.get('growth_criteria', {})
        if growth_criteria.get('min_eps_qoq_growth'):
            filters['eps_growth_min'] = growth_criteria['min_eps_qoq_growth']
        
        # パフォーマンスフィルタ
        performance_criteria = kwargs.get('performance_criteria', {})
        if performance_criteria.get('above_sma200'):
            filters['sma200_above'] = True
        
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
            UpcomingEarningsData のリスト
        """
        try:
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
            sort_by = kwargs.get('sort_by', 'earnings_date')
            sort_order = kwargs.get('sort_order', 'asc')
            results = self._sort_upcoming_earnings_results(results, sort_by, sort_order)
            
            # 件数制限
            max_results = kwargs.get('max_results', 100)
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error in upcoming_earnings_screen: {e}")
            return []
    
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
            StockData オブジェクトのリスト
        """
        try:
            # フィルタを構築
            filters = self._build_earnings_winners_filters(**kwargs)
            
            # Finvizからデータを取得
            results = self.screen_stocks(filters)
            
            # ソート
            sort_by = kwargs.get('sort_by', 'performance_1w')
            sort_order = kwargs.get('sort_order', 'desc')
            
            if sort_by == 'performance_1w':
                results.sort(key=lambda x: x.performance_1w or -999, reverse=(sort_order == 'desc'))
            elif sort_by == 'eps_growth_qoq':
                results.sort(key=lambda x: x.eps_growth_qtr or -999, reverse=(sort_order == 'desc'))
            elif sort_by == 'price_change':
                results.sort(key=lambda x: x.price_change or -999, reverse=(sort_order == 'desc'))
            elif sort_by == 'volume':
                results.sort(key=lambda x: x.volume or 0, reverse=(sort_order == 'desc'))
            
            # 件数制限
            max_results = kwargs.get('max_results', 50)
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error in earnings_winners_screener: {e}")
            return []
    
    def _build_earnings_winners_filters(self, **kwargs) -> Dict[str, Any]:
        """決算後上昇銘柄スクリーニング用フィルタを構築"""
        filters = {}
        
        # 決算発表期間（直接指定されたearnings_dateが優先）
        if 'earnings_date' in kwargs:
            filters['earnings_date'] = kwargs['earnings_date']
        else:
            earnings_period = kwargs.get('earnings_period', 'this_week')
            if earnings_period == 'this_week':
                filters['earnings_date'] = 'thisweek'
            elif earnings_period == 'yesterday':
                filters['earnings_date'] = 'yesterday'
            elif earnings_period == 'today':
                filters['earnings_date'] = 'today'
            else:
                filters['earnings_date'] = 'thisweek'
        
        # 時価総額（デフォルト：small over）
        market_cap = kwargs.get('market_cap', 'smallover')
        if market_cap in MARKET_CAP_FILTERS:
            filters['market_cap'] = market_cap
        
        # 価格（デフォルト：10以上）
        min_price = kwargs.get('min_price', 10.0)
        if min_price:
            filters['price_min'] = min_price
        
        # 平均出来高（デフォルト：500K以上）
        min_avg_volume = kwargs.get('min_avg_volume', 'o500')
        if min_avg_volume:
            filters['avg_volume_min'] = min_avg_volume
        
        # EPS前四半期比成長率（デフォルト：10%以上）
        min_eps_growth_qoq = kwargs.get('min_eps_growth_qoq', 10.0)
        if min_eps_growth_qoq:
            filters['eps_growth_qoq_min'] = min_eps_growth_qoq
        
        # EPS予想改訂（デフォルト：5%以上）
        min_eps_revision = kwargs.get('min_eps_revision', 5.0)
        if min_eps_revision:
            filters['eps_revision_min'] = min_eps_revision
        
        # 売上前四半期比成長率（デフォルト：5%以上）
        min_sales_growth_qoq = kwargs.get('min_sales_growth_qoq', 5.0)
        if min_sales_growth_qoq:
            filters['sales_growth_qoq_min'] = min_sales_growth_qoq
        
        # 週次パフォーマンス（デフォルト：5日〜1週間）
        min_weekly_performance = kwargs.get('min_weekly_performance', '5to-1w')
        if min_weekly_performance:
            filters['weekly_performance'] = min_weekly_performance
        
        # 200日移動平均線上（デフォルト：True）
        sma200_filter = kwargs.get('sma200_filter', True)
        if sma200_filter:
            filters['sma200_above'] = True
        
        # セクター（デフォルト：主要セクター）
        target_sectors = kwargs.get('target_sectors', [
            'Technology', 'Industrials', 'Healthcare', 
            'Communication Services', 'Consumer Cyclical', 'Financial Services'
        ])
        if target_sectors:
            filters['sectors'] = target_sectors
        
        # 結果数制限
        max_results = kwargs.get('max_results', 50)
        if max_results:
            filters['max_results'] = max_results
        
        return filters
    
    def _build_upcoming_earnings_filters(self, **kwargs) -> Dict[str, Any]:
        """来週決算予定スクリーニング用フィルタを構築"""
        filters = {}
        
        # 決算発表期間（直接指定されたearnings_dateが優先）
        if 'earnings_date' in kwargs:
            # 直接指定されたearnings_dateパラメータを使用
            filters['earnings_date'] = kwargs['earnings_date']
        else:
            # earnings_periodからearnings_dateに変換
            earnings_period = kwargs.get('earnings_period', 'next_week')
            if earnings_period == 'next_week':
                filters['earnings_date'] = 'next_week'
            elif earnings_period == 'next_2_weeks':
                filters['earnings_date'] = 'within_2_weeks'
            elif earnings_period == 'next_month':
                filters['earnings_date'] = 'next_month'
        
        # 時価総額（デフォルト：small over）
        market_cap = kwargs.get('market_cap', 'smallover')
        if market_cap in MARKET_CAP_FILTERS:
            filters['market_cap'] = market_cap
        
        # 価格（デフォルト：10以上）
        min_price = kwargs.get('min_price', 10)
        if min_price:
            filters['price_min'] = min_price
        
        # 平均出来高（デフォルト：500）
        min_avg_volume = kwargs.get('min_avg_volume', 500)
        if min_avg_volume:
            filters['avg_volume_min'] = min_avg_volume
        
        # 結果数制限
        max_results = kwargs.get('max_results')
        if max_results:
            filters['max_results'] = max_results
        
        # セクター（デフォルト：主要セクター）
        target_sectors = kwargs.get('target_sectors', [
            'Technology', 'Industrials', 'Healthcare', 
            'Communication Services', 'Consumer Cyclical', 
            'Financial Services', 'Consumer Defensive', 'Basic Materials'
        ])
        if target_sectors:
            filters['sectors'] = target_sectors
        
        return filters
    
    def _convert_to_upcoming_earnings_data(self, stock: StockData, **kwargs) -> Optional[UpcomingEarningsData]:
        """StockDataをUpcomingEarningsDataに変換"""
        try:
            # 基本情報
            upcoming_data = UpcomingEarningsData(
                ticker=stock.ticker,
                company_name=stock.company_name or "",
                sector=stock.sector or "",
                industry=stock.industry or "",
                earnings_date=stock.earnings_date or "",
                earnings_timing="unknown"  # Finvizからは取得困難
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
                upcoming_data.target_price_upside = ((stock.target_price - stock.price) / stock.price) * 100
            
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
            logger.warning(f"Failed to convert stock data to upcoming earnings data: {e}")
            return None
    

    

    
    def _sort_upcoming_earnings_results(self, results: List[UpcomingEarningsData], 
                                      sort_by: str, sort_order: str) -> List[UpcomingEarningsData]:
        """来週決算予定結果をソート"""
        reverse = sort_order.lower() == 'desc'
        
        if sort_by == 'earnings_date':
            results.sort(key=lambda x: x.earnings_date or '', reverse=reverse)
        elif sort_by == 'market_cap':
            results.sort(key=lambda x: x.market_cap or 0, reverse=reverse)
        elif sort_by == 'target_price_upside':
            results.sort(key=lambda x: x.target_price_upside or 0, reverse=reverse)
        elif sort_by == 'volatility':
            results.sort(key=lambda x: x.volatility or 0, reverse=reverse)

        elif sort_by == 'ticker':
            results.sort(key=lambda x: x.ticker, reverse=reverse)
        
        return results
    
    def _build_trend_reversion_filters(self, **kwargs) -> Dict[str, Any]:
        """トレンド反転フィルタを構築"""
        filters = {}
        
        market_cap = kwargs.get('market_cap', 'mid_large')
        filters['market_cap'] = market_cap
        
        if 'eps_growth_qoq' in kwargs:
            filters['eps_growth_qoq_min'] = kwargs['eps_growth_qoq']
        
        if 'revenue_growth_qoq' in kwargs:
            filters['revenue_growth_qoq_min'] = kwargs['revenue_growth_qoq']
        
        if 'rsi_max' in kwargs:
            filters['rsi_max'] = kwargs['rsi_max']
        
        if 'sectors' in kwargs and kwargs['sectors']:
            filters['sectors'] = kwargs['sectors']
        
        if 'exclude_sectors' in kwargs and kwargs['exclude_sectors']:
            filters['exclude_sectors'] = kwargs['exclude_sectors']
        
        return filters
    
    def _build_relative_volume_filters(self, **kwargs) -> Dict[str, Any]:
        """相対出来高フィルタを構築"""
        filters = {}
        
        # 必須パラメータ
        filters['relative_volume_min'] = kwargs['min_relative_volume']
        
        if 'min_price' in kwargs:
            filters['price_min'] = kwargs['min_price']
        
        if 'sectors' in kwargs and kwargs['sectors']:
            filters['sectors'] = kwargs['sectors']
        
        return filters
    
    def _build_technical_analysis_filters(self, **kwargs) -> Dict[str, Any]:
        """テクニカル分析フィルタを構築"""
        filters = {}
        
        if 'rsi_min' in kwargs:
            filters['rsi_min'] = kwargs['rsi_min']
        
        if 'rsi_max' in kwargs:
            filters['rsi_max'] = kwargs['rsi_max']
        
        if 'price_vs_sma20' in kwargs:
            if kwargs['price_vs_sma20'] == 'above':
                filters['sma20_above'] = True
            elif kwargs['price_vs_sma20'] == 'below':
                filters['sma20_below'] = True
        
        if 'price_vs_sma50' in kwargs:
            if kwargs['price_vs_sma50'] == 'above':
                filters['sma50_above'] = True
            elif kwargs['price_vs_sma50'] == 'below':
                filters['sma50_below'] = True
        
        if 'price_vs_sma200' in kwargs:
            if kwargs['price_vs_sma200'] == 'above':
                filters['sma200_above'] = True
            elif kwargs['price_vs_sma200'] == 'below':
                filters['sma200_below'] = True
        
        if 'min_price' in kwargs:
            filters['price_min'] = kwargs['min_price']
        
        if 'min_volume' in kwargs:
            filters['volume_min'] = kwargs['min_volume']
        
        if 'sectors' in kwargs and kwargs['sectors']:
            filters['sectors'] = kwargs['sectors']
        
        return filters