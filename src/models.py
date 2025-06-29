from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class StockData:
    """株式データのメインモデル"""
    ticker: str
    company_name: str
    sector: str
    industry: str
    country: Optional[str] = None
    market_cap: Optional[str] = None
    price: Optional[float] = None
    volume: Optional[int] = None
    avg_volume: Optional[int] = None
    relative_volume: Optional[float] = None
    price_change: Optional[float] = None
    price_change_abs: Optional[float] = None
    gap: Optional[float] = None
    
    # 時間外取引データ
    premarket_price: Optional[float] = None
    premarket_change: Optional[float] = None
    premarket_change_percent: Optional[float] = None
    afterhours_price: Optional[float] = None
    afterhours_change: Optional[float] = None
    afterhours_change_percent: Optional[float] = None
    
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
    
    # テクニカル・パフォーマンス指標
    volatility: Optional[float] = None
    beta: Optional[float] = None
    performance_1w: Optional[float] = None
    performance_1m: Optional[float] = None
    performance_4w: Optional[float] = None
    performance_ytd: Optional[float] = None
    
    # 基本指標
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    rsi: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    above_sma_20: Optional[bool] = None
    above_sma_50: Optional[bool] = None
    above_sma_200: Optional[bool] = None
    sma_20_relative: Optional[float] = None
    sma_50_relative: Optional[float] = None
    sma_200_relative: Optional[float] = None
    target_price: Optional[float] = None
    analyst_recommendation: Optional[str] = None
    insider_ownership: Optional[float] = None
    institutional_ownership: Optional[float] = None
    short_interest: Optional[float] = None
    float_shares: Optional[int] = None
    outstanding_shares: Optional[int] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    
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

# Finvizのフィールドマッピング定数
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
    'float': 'Float',
    'outstanding': 'Outstanding',
    '52w_high': '52W High',
    '52w_low': '52W Low',
    
    # 決算関連
    'earnings_date': 'Earnings',
    'eps_surprise': 'EPS Surprise',
    'revenue_surprise': 'Sales Surprise'
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
    
    # 決算前分析スコア
    earnings_potential_score: Optional[float] = None
    risk_score: Optional[float] = None
    surprise_probability: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpcomingEarningsData':
        """辞書から作成"""
        return cls(**data)