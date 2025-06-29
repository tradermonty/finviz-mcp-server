import re
from typing import Optional, List, Any, Dict

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
    valid_caps = [
        'mega', 'large', 'mid', 'small', 'micro', 'nano',
        'smallover', 'midover'
    ]
    return market_cap in valid_caps

def validate_earnings_date(earnings_date: str) -> bool:
    """
    決算発表日フィルタの妥当性をチェック
    
    Args:
        earnings_date: 決算発表日フィルタ
        
    Returns:
        有効な決算発表日フィルタかどうか
    """
    valid_dates = [
        'today_after', 'tomorrow_before', 'this_week', 'within_2_weeks',
        'today_before', 'yesterday_after', 'this_week_after', 'this_week_before'
    ]
    return earnings_date in valid_dates

def validate_sector(sector: str) -> bool:
    """
    セクター名の妥当性をチェック
    
    Args:
        sector: セクター名
        
    Returns:
        有効なセクター名かどうか
    """
    valid_sectors = [
        'Basic Materials', 'Communication Services', 'Consumer Cyclical',
        'Consumer Defensive', 'Energy', 'Financial Services', 'Healthcare',
        'Industrials', 'Real Estate', 'Technology', 'Utilities'
    ]
    return sector in valid_sectors

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
    スクリーニングパラメータの妥当性をチェック
    
    Args:
        params: スクリーニングパラメータ
        
    Returns:
        エラーメッセージのリスト（空の場合は全て有効）
    """
    errors = []
    
    # 時価総額チェック
    if 'market_cap' in params and params['market_cap'] is not None:
        if not validate_market_cap(params['market_cap']):
            errors.append(f"Invalid market_cap: {params['market_cap']}")
    
    # 価格範囲チェック
    min_price = params.get('min_price')
    max_price = params.get('max_price')
    if not validate_price_range(min_price, max_price):
        errors.append("Invalid price range")
    
    # 出来高チェック
    if 'min_volume' in params and params['min_volume'] is not None:
        if not validate_volume(params['min_volume']):
            errors.append(f"Invalid min_volume: {params['min_volume']}")
    
    # 決算発表日チェック
    if 'earnings_date' in params and params['earnings_date'] is not None:
        if not validate_earnings_date(params['earnings_date']):
            errors.append(f"Invalid earnings_date: {params['earnings_date']}")
    
    # セクターチェック
    if 'sectors' in params and params['sectors']:
        for sector in params['sectors']:
            if not validate_sector(sector):
                errors.append(f"Invalid sector: {sector}")
    
    # 除外セクターチェック
    if 'exclude_sectors' in params and params['exclude_sectors']:
        for sector in params['exclude_sectors']:
            if not validate_sector(sector):
                errors.append(f"Invalid exclude_sector: {sector}")
    
    # 相対出来高チェック
    if 'min_relative_volume' in params and params['min_relative_volume'] is not None:
        rel_vol = params['min_relative_volume']
        if not isinstance(rel_vol, (int, float)) or rel_vol < 0:
            errors.append(f"Invalid min_relative_volume: {rel_vol}")
    
    # 価格変動率チェック
    if 'min_price_change' in params and params['min_price_change'] is not None:
        price_change = params['min_price_change']
        if not isinstance(price_change, (int, float)):
            errors.append(f"Invalid min_price_change: {price_change}")
    
    # SMAフィルタチェック
    if 'sma_filter' in params and params['sma_filter'] is not None:
        valid_sma_filters = ['above_sma20', 'above_sma50', 'above_sma200', 'none']
        if params['sma_filter'] not in valid_sma_filters:
            errors.append(f"Invalid sma_filter: {params['sma_filter']}")
    
    # ソート基準チェック
    if 'sort_by' in params and params['sort_by'] is not None:
        valid_sort_options = [
            'price_change', 'relative_volume', 'volume', 'price',
            'change_percent', 'afterhours_change_percent', 'eps_surprise',
            'volatility', 'market_cap'
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
        if not isinstance(max_results, int) or max_results <= 0 or max_results > 1000:
            errors.append(f"Invalid max_results: {max_results} (must be 1-1000)")
    
    return errors

def validate_data_fields(fields: List[str]) -> List[str]:
    """
    データフィールドの妥当性をチェック
    
    Args:
        fields: データフィールドのリスト
        
    Returns:
        無効なフィールドのリスト
    """
    valid_fields = [
        'ticker', 'company', 'sector', 'industry', 'country',
        'market_cap', 'pe_ratio', 'price', 'change', 'change_percent',
        'volume', 'avg_volume', 'relative_volume', 'float', 'outstanding',
        'insider_own', 'institutional_own', 'short_interest', 'target_price',
        '52w_high', '52w_low', 'rsi', 'gap', 'analyst_recom',
        'afterhours_change', 'afterhours_change_percent', 'afterhours_price',
        'eps_surprise', 'revenue_surprise', 'eps_estimate', 'revenue_estimate',
        'volatility', 'performance_4w', 'performance_1m', 'performance_1w',
        'beta', 'eps_qoq_growth', 'sales_qoq_growth', 'eps_revision',
        'earnings_date', 'forward_pe', 'peg', 'sma_200_relative'
    ]
    
    return [field for field in fields if field not in valid_fields]

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