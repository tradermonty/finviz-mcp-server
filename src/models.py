from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class StockData:
    """株式データのメインモデル（全Finvizフィールド対応）"""
    ticker: str
    company_name: str
    sector: str
    industry: str
    country: Optional[str] = None
    
    # 基本価格・出来高データ
    price: Optional[float] = None
    price_change: Optional[float] = None
    price_change_percent: Optional[float] = None
    volume: Optional[int] = None
    avg_volume: Optional[int] = None
    relative_volume: Optional[float] = None
    
    # 新規追加：詳細OHLC データ
    prev_close: Optional[float] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    change_from_open: Optional[float] = None
    trades_count: Optional[int] = None
    
    # 時間外取引データ
    premarket_price: Optional[float] = None
    premarket_change: Optional[float] = None
    premarket_change_percent: Optional[float] = None
    afterhours_price: Optional[float] = None
    afterhours_change: Optional[float] = None
    afterhours_change_percent: Optional[float] = None
    
    # 市場データ
    market_cap: Optional[float] = None
    income: Optional[float] = None
    sales: Optional[float] = None
    book_value_per_share: Optional[float] = None
    cash_per_share: Optional[float] = None
    dividend: Optional[float] = None
    dividend_yield: Optional[float] = None
    employees: Optional[int] = None
    
    # 新規追加：指数・分類情報
    index: Optional[str] = None  # 所属指数（S&P500等）
    optionable: Optional[bool] = None
    shortable: Optional[bool] = None
    ipo_date: Optional[str] = None
    
    # バリュエーション指標
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg: Optional[float] = None
    ps_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    price_to_cash: Optional[float] = None
    price_to_free_cash_flow: Optional[float] = None
    
    # 収益性指標
    eps: Optional[float] = None
    eps_this_y: Optional[float] = None
    eps_next_y: Optional[float] = None
    eps_past_5y: Optional[float] = None
    eps_next_5y: Optional[float] = None
    sales_past_5y: Optional[float] = None
    eps_growth_this_y: Optional[float] = None
    eps_growth_next_y: Optional[float] = None
    eps_growth_past_5y: Optional[float] = None
    eps_growth_next_5y: Optional[float] = None
    sales_growth_qtr: Optional[float] = None
    eps_growth_qtr: Optional[float] = None
    eps_next_q: Optional[float] = None  # 新規追加：次四半期EPS予想
    
    # 財務健全性指標
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    lt_debt_to_equity: Optional[float] = None
    
    # 収益性マージン
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    profit_margin: Optional[float] = None
    
    # ROE・ROA・ROI
    roe: Optional[float] = None
    roa: Optional[float] = None
    roi: Optional[float] = None
    roic: Optional[float] = None  # 新規追加：投下資本利益率
    
    # 配当関連
    payout_ratio: Optional[float] = None
    
    # 持株構造
    insider_ownership: Optional[float] = None
    insider_transactions: Optional[float] = None
    institutional_ownership: Optional[float] = None
    institutional_transactions: Optional[float] = None
    float_short: Optional[float] = None
    short_ratio: Optional[float] = None
    short_interest: Optional[float] = None
    
    # 株式数
    shares_outstanding: Optional[float] = None
    shares_float: Optional[float] = None
    float_percentage: Optional[float] = None  # 新規追加：Float %
    
    # テクニカル・パフォーマンス指標
    volatility: Optional[float] = None
    volatility_week: Optional[float] = None  # 新規追加：週次ボラティリティ
    volatility_month: Optional[float] = None  # 新規追加：月次ボラティリティ
    beta: Optional[float] = None
    atr: Optional[float] = None
    
    # 新規追加：短時間パフォーマンス
    performance_1min: Optional[float] = None
    performance_2min: Optional[float] = None
    performance_3min: Optional[float] = None
    performance_5min: Optional[float] = None
    performance_10min: Optional[float] = None
    performance_15min: Optional[float] = None
    performance_30min: Optional[float] = None
    performance_1h: Optional[float] = None
    performance_2h: Optional[float] = None
    performance_4h: Optional[float] = None
    
    # パフォーマンス
    performance_1w: Optional[float] = None
    performance_1m: Optional[float] = None
    performance_3m: Optional[float] = None
    performance_6m: Optional[float] = None
    performance_ytd: Optional[float] = None
    performance_1y: Optional[float] = None
    performance_2y: Optional[float] = None
    performance_3y: Optional[float] = None
    performance_5y: Optional[float] = None
    performance_10y: Optional[float] = None  # 新規追加：10年パフォーマンス
    performance_since_inception: Optional[float] = None  # 新規追加：設定来パフォーマンス
    
    # 移動平均線
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    above_sma_20: Optional[bool] = None
    above_sma_50: Optional[bool] = None
    above_sma_200: Optional[bool] = None
    sma_20_relative: Optional[float] = None
    sma_50_relative: Optional[float] = None
    sma_200_relative: Optional[float] = None
    
    # 高値・安値
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    high_52w_relative: Optional[float] = None
    low_52w_relative: Optional[float] = None
    
    # 新規追加：50日高値・安値
    day_50_high: Optional[float] = None
    day_50_low: Optional[float] = None
    all_time_high: Optional[float] = None
    all_time_low: Optional[float] = None
    
    # テクニカル指標
    rsi: Optional[float] = None
    rsi_14: Optional[float] = None
    rel_volume: Optional[float] = None
    avg_true_range: Optional[float] = None
    
    # 決算関連データ
    earnings_date: Optional[str] = None
    earnings_timing: Optional[str] = None
    eps_surprise: Optional[float] = None
    revenue_surprise: Optional[float] = None
    eps_estimate: Optional[float] = None
    revenue_estimate: Optional[float] = None
    eps_actual: Optional[float] = None
    revenue_actual: Optional[float] = None
    eps_qoq_growth: Optional[float] = None
    sales_qoq_growth: Optional[float] = None
    eps_revision: Optional[float] = None
    revenue_revision: Optional[float] = None
    
    # アナリスト推奨・目標価格
    target_price: Optional[float] = None
    analyst_recommendation: Optional[str] = None
    
    # オプション関連
    average_volume: Optional[int] = None
    
    # ETF専用フィールド（新規追加）
    single_category: Optional[str] = None
    asset_type: Optional[str] = None
    etf_type: Optional[str] = None
    sector_theme: Optional[str] = None
    region: Optional[str] = None
    active_passive: Optional[str] = None
    net_expense_ratio: Optional[float] = None
    total_holdings: Optional[int] = None
    aum: Optional[float] = None  # Assets Under Management
    nav: Optional[float] = None  # Net Asset Value
    nav_percent: Optional[float] = None
    
    # ETFフロー関連（新規追加）
    net_flows_1m: Optional[float] = None
    net_flows_1m_percent: Optional[float] = None
    net_flows_3m: Optional[float] = None
    net_flows_3m_percent: Optional[float] = None
    net_flows_ytd: Optional[float] = None
    net_flows_ytd_percent: Optional[float] = None
    net_flows_1y: Optional[float] = None
    net_flows_1y_percent: Optional[float] = None
    
    # その他のFinviz指標
    gap: Optional[float] = None
    tags: Optional[str] = None  # 新規追加：タグ情報
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StockData':
        """辞書から作成"""
        return cls(**data)

@dataclass
class NewsData:
    """ニュースデータモデル"""
    ticker: str
    title: str
    source: str
    date: datetime
    url: str
    category: str
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        # datetime を文字列に変換
        data['date'] = self.date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NewsData':
        """辞書から作成"""
        # 文字列の日付を datetime に変換
        if isinstance(data.get('date'), str):
            data['date'] = datetime.fromisoformat(data['date'])
        return cls(**data)

@dataclass
class SectorPerformance:
    """セクターパフォーマンスデータモデル"""
    sector: str
    performance_1d: float
    performance_1w: float
    performance_1m: float
    performance_3m: float
    performance_6m: float
    performance_1y: float
    stock_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SectorPerformance':
        """辞書から作成"""
        return cls(**data)

@dataclass
class EarningsData:
    """決算データモデル"""
    ticker: str
    company_name: str
    earnings_date: str
    earnings_timing: str  # "before" or "after"
    
    # 価格データ
    pre_earnings_price: Optional[float] = None
    post_earnings_price: Optional[float] = None
    premarket_price: Optional[float] = None
    afterhours_price: Optional[float] = None
    current_price: Optional[float] = None
    price_change_percent: Optional[float] = None
    gap_percent: Optional[float] = None
    
    # 出来高データ
    volume: Optional[int] = None
    avg_volume: Optional[int] = None
    relative_volume: Optional[float] = None
    
    # 決算結果・サプライズ
    eps_surprise: Optional[float] = None
    revenue_surprise: Optional[float] = None
    eps_estimate: Optional[float] = None
    eps_actual: Optional[float] = None
    revenue_estimate: Optional[float] = None
    revenue_actual: Optional[float] = None
    earnings_revision: Optional[str] = None
    
    # 市場反応・分析
    market_reaction: Optional[str] = None  # "positive", "negative", "neutral"
    volatility: Optional[float] = None
    beta: Optional[float] = None
    performance_4w: Optional[float] = None
    recovery_from_decline: Optional[bool] = None
    trading_opportunity_score: Optional[float] = None  # 1-10
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EarningsData':
        """辞書から作成"""
        return cls(**data)

@dataclass
class ScreeningResult:
    """スクリーニング結果のコンテナ"""
    query_parameters: Dict[str, Any]
    results: list
    total_count: int
    execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'query_parameters': self.query_parameters,
            'results': [stock.to_dict() for stock in self.results],
            'total_count': self.total_count,
            'execution_time': self.execution_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScreeningResult':
        """辞書から作成"""
        results = [StockData.from_dict(item) for item in data.get('results', [])]
        return cls(
            query_parameters=data.get('query_parameters', {}),
            results=results,
            total_count=data.get('total_count', 0),
            execution_time=data.get('execution_time')
        )

# 古いマッピング定数は削除され、constants.pyに統合されました

# Finvizのフィールドマッピング定数（既存のシンプル版も保持）
FINVIZ_FIELD_MAPPING = {
    # 基本情報
    'ticker': 'Ticker',
    'company': 'Company',
    'sector': 'Sector',
    'industry': 'Industry',
    'country': 'Country',
    
    # 価格・出来高
    'price': 'Price',
    'change': 'Change',
    'change_percent': 'Chg',
    'volume': 'Volume',
    'avg_volume': 'Avg Volume',
    'relative_volume': 'Rel Volume',
    
    # 市場データ
    'market_cap': 'Market Cap',
    'pe_ratio': 'P/E',
    'forward_pe': 'Forward P/E',
    'peg': 'PEG',
    'eps': 'EPS',
    'dividend_yield': 'Dividend %',
    
    # テクニカル指標
    'rsi': 'RSI',
    'beta': 'Beta',
    'volatility': 'Volatility',
    'performance_1w': 'Perf Week',
    'performance_1m': 'Perf Month',
    'performance_ytd': 'Perf YTD',
    
    # 移動平均
    'sma_20': 'SMA20',
    'sma_50': 'SMA50',
    'sma_200': 'SMA200',
    
    # その他
    'target_price': 'Target Price',
    'analyst_recom': 'Recom',
    'insider_own': 'Insider Own',
    'institutional_own': 'Inst Own',
    'short_interest': 'Short Interest',
    'week_52_high': '52W High',
    'week_52_low': '52W Low',
    'earnings_date': 'Earnings'
}

# セクター定数
SECTORS = [
    'Basic Materials',
    'Communication Services', 
    'Consumer Cyclical',
    'Consumer Defensive',
    'Energy',
    'Financial Services',
    'Healthcare',
    'Industrials',
    'Real Estate',
    'Technology',
    'Utilities'
]

# 時価総額フィルタ定数
MARKET_CAP_FILTERS = {
    'mega': 'Mega ($200bln and more)',
    'large': 'Large ($10bln to $200bln)',
    'mid': 'Mid ($2bln to $10bln)',
    'small': 'Small ($300mln to $2bln)',
    'micro': 'Micro ($50mln to $300mln)',
    'nano': 'Nano (under $50mln)',
    'smallover': 'Small+ ($300mln and more)',
    'midover': 'Mid+ ($2bln and more)'
}

@dataclass
class UpcomingEarningsData:
    """来週決算予定データモデル"""
    ticker: str
    company_name: str
    sector: str
    industry: str
    earnings_date: str
    earnings_timing: str  # "before" or "after"
    
    # 基本株価データ
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    avg_volume: Optional[int] = None
    
    # 決算予想データ
    eps_estimate: Optional[float] = None
    revenue_estimate: Optional[float] = None
    eps_estimate_revision: Optional[float] = None
    revenue_estimate_revision: Optional[float] = None
    analyst_count: Optional[int] = None
    estimate_trend: Optional[str] = None  # "improving", "declining", "stable"
    
    # 過去のサプライズ履歴
    historical_eps_surprise: Optional[list] = None
    historical_revenue_surprise: Optional[list] = None
    avg_eps_surprise: Optional[float] = None
    avg_revenue_surprise: Optional[float] = None
    
    # 評価・推奨データ
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg: Optional[float] = None
    target_price: Optional[float] = None
    target_price_upside: Optional[float] = None
    analyst_recommendation: Optional[str] = None
    recent_rating_changes: Optional[list] = None
    
    # リスク評価指標
    volatility: Optional[float] = None
    beta: Optional[float] = None
    short_interest: Optional[float] = None
    short_ratio: Optional[float] = None
    insider_ownership: Optional[float] = None
    institutional_ownership: Optional[float] = None
    
    # パフォーマンス・テクニカル指標
    performance_1w: Optional[float] = None
    performance_1m: Optional[float] = None
    performance_3m: Optional[float] = None
    sma_200_relative: Optional[float] = None
    rsi: Optional[float] = None
    
    # オプション活動（オプション）
    options_volume: Optional[int] = None
    put_call_ratio: Optional[float] = None
    implied_volatility: Optional[float] = None
    

    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpcomingEarningsData':
        """辞書から作成"""
        return cls(**data)