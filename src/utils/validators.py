import re
from typing import Optional, List, Any, Dict
from ..constants import ALL_PARAMETERS

def validate_ticker(ticker: str) -> bool:
    """
    ティッカーシンボルの妥当性をチェック
    
    Args:
        ticker: ティッカーシンボル
        
    Returns:
        有効なティッカーかどうか
    """
    if not ticker or not isinstance(ticker, str):
        return False
    
    # 基本的なパターンチェック（1-5文字のアルファベット）
    pattern = r'^[A-Z]{1,5}$'
    return bool(re.match(pattern, ticker.upper()))

def validate_price_range(min_price: Optional[float], max_price: Optional[float]) -> bool:
    """
    価格範囲の妥当性をチェック
    
    Args:
        min_price: 最低価格
        max_price: 最高価格
        
    Returns:
        有効な価格範囲かどうか
    """
    if min_price is not None and min_price < 0:
        return False
    
    if max_price is not None and max_price < 0:
        return False
    
    if min_price is not None and max_price is not None:
        return min_price <= max_price
    
    return True

def validate_market_cap(market_cap: str) -> bool:
    """
    時価総額フィルタの妥当性をチェック
    
    Args:
        market_cap: 時価総額フィルタ
        
    Returns:
        有効な時価総額フィルタかどうか
    """
    return market_cap in ALL_PARAMETERS['cap']

def validate_earnings_date(earnings_date: str) -> bool:
    """
    決算発表日フィルタの妥当性をチェック
    
    Args:
        earnings_date: 決算発表日フィルタ
        
    Returns:
        有効な決算発表日フィルタかどうか
    """
    # APIレベルの有効な決算日値を定義
    valid_api_values = {
        'today_after',
        'today_before', 
        'tomorrow_after',
        'tomorrow_before',
        'yesterday_after',
        'yesterday_before',
        'this_week',
        'next_week',
        'within_2_weeks',
        'thisweek',
        'nextweek',
        'nextdays5'
    }
    
    return earnings_date in valid_api_values

def validate_sector(sector: str) -> bool:
    """
    セクター名の妥当性をチェック
    
    Args:
        sector: セクター名
        
    Returns:
        有効なセクター名かどうか
    """
    # APIレベルの有効なセクター名を定義
    valid_api_sectors = {
        # ユーザーフレンドリーなセクター名
        'Basic Materials',
        'Communication Services', 
        'Consumer Cyclical',
        'Consumer Defensive',
        'Energy',
        'Financial',
        'Healthcare',
        'Industrials',
        'Real Estate',
        'Technology',
        'Utilities',
        # 内部パラメータ値も受け入れ
        'basicmaterials',
        'communicationservices',
        'consumercyclical', 
        'consumerdefensive',
        'energy',
        'financial',
        'healthcare',
        'industrials',
        'realestate',
        'technology',
        'utilities'
    }
    
    return sector in valid_api_sectors

def validate_percentage(value: float, min_val: float = -100, max_val: float = 1000) -> bool:
    """
    パーセンテージ値の妥当性をチェック
    
    Args:
        value: パーセンテージ値
        min_val: 最小値
        max_val: 最大値
        
    Returns:
        有効なパーセンテージ値かどうか
    """
    return min_val <= value <= max_val

def validate_volume(volume: int) -> bool:
    """
    出来高の妥当性をチェック
    
    Args:
        volume: 出来高
        
    Returns:
        有効な出来高かどうか
    """
    return volume >= 0

def validate_screening_params(params: Dict[str, Any]) -> List[str]:
    """
    スクリーニングパラメータの妥当性をチェック（完全版）
    
    Args:
        params: スクリーニングパラメータ
        
    Returns:
        エラーメッセージのリスト（空の場合は全て有効）
    """
    errors = []
    
    # 基本パラメータの検証
    basic_params = {
        'exchange': 'exch',
        'index': 'idx', 
        'sector': 'sec',
        'industry': 'ind',
        'country': 'geo',
        'market_cap': 'cap',
        'price': 'sh_price',
        'target_price': 'targetprice',
        'dividend_yield': 'fa_div',
        'short_float': 'sh_short',
        'analyst_recommendation': 'an_recom',
        'option_short': 'sh_opt',
        'earnings_date': 'earningsdate',
        'ipo_date': 'ipodate',
        'average_volume': 'sh_avgvol',
        'relative_volume': 'sh_relvol',
        'current_volume': 'sh_curvol',
        'trades': 'sh_trades',
        'shares_outstanding': 'sh_outstanding',
        'float': 'sh_float'
    }
    
    for param_name, param_key in basic_params.items():
        if param_name in params and params[param_name] is not None:
            if params[param_name] not in ALL_PARAMETERS[param_key]:
                errors.append(f"Invalid {param_name}: {params[param_name]}")
    
    # 価格範囲チェック
    min_price = params.get('min_price')
    max_price = params.get('max_price')
    if not validate_price_range(min_price, max_price):
        errors.append("Invalid price range")
    
    # 数値範囲チェック
    numeric_range_params = [
        'pe_min', 'pe_max', 'forward_pe_min', 'forward_pe_max',
        'peg_min', 'peg_max', 'ps_min', 'ps_max', 'pb_min', 'pb_max',
        'debt_equity_min', 'debt_equity_max', 'roe_min', 'roe_max',
        'roi_min', 'roi_max', 'roa_min', 'roa_max',
        'gross_margin_min', 'gross_margin_max',
        'operating_margin_min', 'operating_margin_max',
        'net_margin_min', 'net_margin_max',
        'rsi_min', 'rsi_max', 'beta_min', 'beta_max',
        'dividend_yield_min', 'dividend_yield_max',
        'volume_min', 'avg_volume_min', 'relative_volume_min',
        'price_change_min', 'price_change_max',
        'performance_week_min', 'performance_month_min',
        'performance_quarter_min', 'performance_halfyear_min',
        'performance_year_min', 'performance_ytd_min',
        'volatility_week_min', 'volatility_month_min',
        'week52_high_distance_min', 'week52_low_distance_min',
        'eps_growth_this_year_min', 'eps_growth_next_year_min',
        'eps_growth_past_5_years_min', 'eps_growth_next_5_years_min',
        'sales_growth_quarter_min', 'sales_growth_past_5_years_min',
        'insider_ownership_min', 'insider_ownership_max',
        'institutional_ownership_min', 'institutional_ownership_max'
    ]
    
    for param in numeric_range_params:
        if param in params and params[param] is not None:
            if not isinstance(params[param], (int, float)):
                errors.append(f"Invalid {param}: must be numeric")
    
    # 複数セクターチェック
    if 'sectors' in params and params['sectors']:
        for sector in params['sectors']:
            if not validate_sector(sector):
                errors.append(f"Invalid sector: {sector}")
    
    # 除外セクターチェック
    if 'exclude_sectors' in params and params['exclude_sectors']:
        for sector in params['exclude_sectors']:
            if not validate_sector(sector):
                errors.append(f"Invalid exclude_sector: {sector}")
    
    # SMAフィルタチェック
    if 'sma_filter' in params and params['sma_filter'] is not None:
        valid_sma_filters = ['above_sma20', 'above_sma50', 'above_sma200', 
                            'below_sma20', 'below_sma50', 'below_sma200', 'none']
        if params['sma_filter'] not in valid_sma_filters:
            errors.append(f"Invalid sma_filter: {params['sma_filter']}")
    
    # ソート基準チェック
    if 'sort_by' in params and params['sort_by'] is not None:
        valid_sort_options = [
            'ticker', 'company', 'sector', 'industry', 'country',
            'market_cap', 'pe', 'price', 'change', 'volume',
            'price_change', 'relative_volume', 'performance_week',
            'performance_month', 'performance_quarter', 'performance_year',
            'analyst_recom', 'avg_volume', 'dividend_yield',
            'eps', 'sales', 'float', 'insider_own', 'inst_own',
            'rsi', 'volatility', 'earnings_date', 'ipo_date'
        ]
        if params['sort_by'] not in valid_sort_options:
            errors.append(f"Invalid sort_by: {params['sort_by']}")
    
    # ソート順序チェック
    if 'sort_order' in params and params['sort_order'] is not None:
        if params['sort_order'] not in ['asc', 'desc']:
            errors.append(f"Invalid sort_order: {params['sort_order']}")
    
    # 最大結果数チェック
    if 'max_results' in params and params['max_results'] is not None:
        max_results = params['max_results']
        if not isinstance(max_results, int) or max_results <= 0 or max_results > 10000:
            errors.append(f"Invalid max_results: {max_results} (must be 1-10000)")
    
    # ビューチェック
    if 'view' in params and params['view'] is not None:
        valid_views = ['111', '121', '131', '141', '151', '161', '171']
        if params['view'] not in valid_views:
            errors.append(f"Invalid view: {params['view']}")
    
    return errors

def validate_data_fields(fields: List[str]) -> List[str]:
    """
    データフィールドの妥当性をチェック（完全版）
    
    Args:
        fields: データフィールドのリスト
        
    Returns:
        無効なフィールドのリスト
    """
    # constants.pyのFINVIZ_COMPREHENSIVE_FIELD_MAPPINGから動的に有効フィールドを取得
    try:
        from ..constants import FINVIZ_COMPREHENSIVE_FIELD_MAPPING
    except ImportError:
        # 直接実行時の場合
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from constants import FINVIZ_COMPREHENSIVE_FIELD_MAPPING
    
    valid_fields = set(FINVIZ_COMPREHENSIVE_FIELD_MAPPING.keys())
    
    # 追加の有効フィールド（後方互換性のため）
    additional_valid_fields = {
        # エラーで報告されたフィールド名の代替名
        'eps_growth_this_y', 'eps_growth_next_y', 'eps_growth_next_5y',
        'eps_growth_past_5y', 'sales_growth_qtr', 'eps_growth_qtr', 
        'sales_growth_qoq', 'performance_1w', 'performance_1m',
        'recommendation', 'analyst_recommendation',
        'insider_own', 'institutional_own', 'insider_ownership', 'institutional_ownership',
        
        # その他の代替フィールド名
        'profit_margin',  # profit_marginのエイリアス
        'all'  # 全フィールド取得用の特別キー
    }
    
    valid_fields.update(additional_valid_fields)
    
    return [field for field in fields if field not in valid_fields]

def validate_exchange(exchange: str) -> bool:
    """
    取引所フィルタの妥当性をチェック
    
    Args:
        exchange: 取引所コード
        
    Returns:
        有効な取引所コードかどうか
    """
    return exchange in ALL_PARAMETERS['exch']

def validate_index(index: str) -> bool:
    """
    指数フィルタの妥当性をチェック
    
    Args:
        index: 指数コード
        
    Returns:
        有効な指数コードかどうか
    """
    return index in ALL_PARAMETERS['idx']

def validate_industry(industry: str) -> bool:
    """
    業界フィルタの妥当性をチェック
    
    Args:
        industry: 業界コード
        
    Returns:
        有効な業界コードかどうか
    """
    return industry in ALL_PARAMETERS['ind']

def validate_country(country: str) -> bool:
    """
    国フィルタの妥当性をチェック
    
    Args:
        country: 国コード
        
    Returns:
        有効な国コードかどうか
    """
    return country in ALL_PARAMETERS['geo']

def validate_price_filter(price: str) -> bool:
    """
    価格フィルタの妥当性をチェック
    
    Args:
        price: 価格フィルタ
        
    Returns:
        有効な価格フィルタかどうか
    """
    return price in ALL_PARAMETERS['sh_price']

def validate_target_price(target_price: str) -> bool:
    """
    目標価格フィルタの妥当性をチェック
    
    Args:
        target_price: 目標価格フィルタ
        
    Returns:
        有効な目標価格フィルタかどうか
    """
    return target_price in ALL_PARAMETERS['targetprice']

def validate_dividend_yield_filter(dividend_yield: str) -> bool:
    """
    配当利回りフィルタの妥当性をチェック
    
    Args:
        dividend_yield: 配当利回りフィルタ
        
    Returns:
        有効な配当利回りフィルタかどうか
    """
    return dividend_yield in ALL_PARAMETERS['fa_div']

def validate_short_float(short_float: str) -> bool:
    """
    ショート比率フィルタの妥当性をチェック
    
    Args:
        short_float: ショート比率フィルタ
        
    Returns:
        有効なショート比率フィルタかどうか
    """
    return short_float in ALL_PARAMETERS['sh_short']

def validate_analyst_recommendation(analyst_rec: str) -> bool:
    """
    アナリスト推奨フィルタの妥当性をチェック
    
    Args:
        analyst_rec: アナリスト推奨フィルタ
        
    Returns:
        有効なアナリスト推奨フィルタかどうか
    """
    return analyst_rec in ALL_PARAMETERS['an_recom']

def validate_option_short(option_short: str) -> bool:
    """
    オプション/ショートフィルタの妥当性をチェック
    
    Args:
        option_short: オプション/ショートフィルタ
        
    Returns:
        有効なオプション/ショートフィルタかどうか
    """
    return option_short in ALL_PARAMETERS['sh_opt']

def validate_ipo_date(ipo_date: str) -> bool:
    """
    IPO日フィルタの妥当性をチェック
    
    Args:
        ipo_date: IPO日フィルタ
        
    Returns:
        有効なIPO日フィルタかどうか
    """
    return ipo_date in ALL_PARAMETERS['ipodate']

def validate_volume_filter(volume_type: str, volume_filter: str) -> bool:
    """
    出来高関連フィルタの妥当性をチェック
    
    Args:
        volume_type: 出来高タイプ ('sh_avgvol', 'sh_relvol', 'sh_curvol', 'sh_trades')
        volume_filter: 出来高フィルタ
        
    Returns:
        有効な出来高フィルタかどうか
    """
    if volume_type in ALL_PARAMETERS:
        return volume_filter in ALL_PARAMETERS[volume_type]
    return False

def validate_shares_filter(shares_type: str, shares_filter: str) -> bool:
    """
    株式数関連フィルタの妥当性をチェック
    
    Args:
        shares_type: 株式数タイプ ('sh_outstanding', 'sh_float')
        shares_filter: 株式数フィルタ
        
    Returns:
        有効な株式数フィルタかどうか
    """
    if shares_type in ALL_PARAMETERS:
        return shares_filter in ALL_PARAMETERS[shares_type]
    return False

def validate_custom_range(param_name: str, min_val: Optional[float], max_val: Optional[float]) -> bool:
    """
    カスタム範囲パラメータの妥当性をチェック
    
    Args:
        param_name: パラメータ名
        min_val: 最小値
        max_val: 最大値
        
    Returns:
        有効なカスタム範囲かどうか
    """
    # 数値パラメータの場合のみ検証
    numeric_params = {
        'price', 'market_cap', 'pe', 'forward_pe', 'peg', 'ps', 'pb',
        'debt_equity', 'roe', 'roi', 'roa', 'dividend_yield',
        'volume', 'avg_volume', 'relative_volume', 'rsi', 'beta'
    }
    
    if param_name not in numeric_params:
        return False
    
    if min_val is not None and max_val is not None:
        return min_val <= max_val
    
    return True

def get_all_valid_values() -> Dict[str, List[str]]:
    """
    すべての有効なパラメータ値を取得
    
    Returns:
        パラメータ名と有効値の辞書
    """
    return {param: list(values.keys()) for param, values in ALL_PARAMETERS.items()}

def validate_parameter_combination(params: Dict[str, Any]) -> List[str]:
    """
    パラメータの組み合わせの妥当性をチェック
    
    Args:
        params: パラメータ辞書
        
    Returns:
        組み合わせエラーのリスト
    """
    errors = []
    
    # ETFと株式の排他的な組み合わせチェック
    if params.get('exclude_etfs') and params.get('only_etfs'):
        errors.append("Cannot exclude and include ETFs simultaneously")
    
    # 価格範囲の組み合わせチェック
    price_filters = ['price', 'price_min', 'price_max']
    price_count = sum(1 for p in price_filters if p in params and params[p] is not None)
    if price_count > 1:
        errors.append("Use either price filter OR price_min/max, not both")
    
    # 出来高範囲の組み合わせチェック
    volume_filters = ['average_volume', 'avg_volume_min', 'volume_min']
    volume_count = sum(1 for v in volume_filters if v in params and params[v] is not None)
    if volume_count > 1:
        errors.append("Use either volume filter OR volume_min, not both")
    
    # 相対出来高範囲の組み合わせチェック
    rel_volume_filters = ['relative_volume', 'relative_volume_min']
    rel_volume_count = sum(1 for rv in rel_volume_filters if rv in params and params[rv] is not None)
    if rel_volume_count > 1:
        errors.append("Use either relative_volume filter OR relative_volume_min, not both")
    
    return errors

def sanitize_input(value: Any) -> Any:
    """
    入力値をサニタイズ
    
    Args:
        value: 入力値
        
    Returns:
        サニタイズされた値
    """
    if isinstance(value, str):
        # SQLインジェクションやXSS攻撃を防ぐための基本的なサニタイゼーション
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
        for char in dangerous_chars:
            value = value.replace(char, '')
        return value.strip()
    
    return value