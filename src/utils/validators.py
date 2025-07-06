import re
from typing import Optional, List, Any, Dict, Union
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

def validate_tickers(tickers: str) -> bool:
    """
    複数のティッカーシンボルの妥当性をチェック
    
    Args:
        tickers: カンマ区切りのティッカーシンボル文字列
        
    Returns:
        すべてのティッカーが有効かどうか
    """
    if not tickers or not isinstance(tickers, str):
        return False
    
    # カンマで分割して各ティッカーを検証
    ticker_list = [t.strip() for t in tickers.split(',') if t.strip()]
    
    if not ticker_list:
        return False
    
    # すべてのティッカーが有効かチェック
    return all(validate_ticker(ticker) for ticker in ticker_list)

def parse_tickers(tickers: str) -> List[str]:
    """
    カンマ区切りのティッカー文字列をリストに変換
    
    Args:
        tickers: カンマ区切りのティッカーシンボル文字列
        
    Returns:
        ティッカーシンボルのリスト
    """
    if not tickers or not isinstance(tickers, str):
        return []
    
    # カンマで分割して空白を除去し、大文字に変換
    return [t.strip().upper() for t in tickers.split(',') if t.strip()]

def validate_price_range(min_price: Optional[Union[int, float, str]], max_price: Optional[Union[int, float, str]]) -> bool:
    """
    価格範囲の妥当性をチェック
    
    Args:
        min_price: 最低価格（数値またはFinvizプリセット形式 'o5', 'u10'）
        max_price: 最高価格（数値またはFinvizプリセット形式 'o5', 'u10'）
        
    Returns:
        有効な価格範囲かどうか
    """
    def _convert_to_float(value):
        """価格値を数値に変換（Finviz形式も対応）"""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Finvizプリセット形式の場合（例: 'o5', 'u10'）
            if value.startswith(('o', 'u')):
                try:
                    return float(value[1:])
                except ValueError:
                    return None
            # 数値文字列の場合
            try:
                return float(value)
            except ValueError:
                return None
        return None
    
    min_val = _convert_to_float(min_price)
    max_val = _convert_to_float(max_price)
    
    if min_val is not None and min_val < 0:
        return False
    
    if max_val is not None and max_val < 0:
        return False
    
    if min_val is not None and max_val is not None:
        return min_val <= max_val
    
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

def validate_volume(volume: Union[int, float, str]) -> bool:
    """
    出来高の妥当性をチェック（数値とFinviz文字列形式の両方対応）
    
    Args:
        volume: 出来高（数値またはFinviz形式: o100, u500, 500to2000など）
        
    Returns:
        有効な出来高かどうか
    """
    if isinstance(volume, (int, float)):
        return volume >= 0
    
    if isinstance(volume, str):
        # 数値文字列のチェックを追加（整数と浮動小数点の両方）
        try:
            return float(volume) >= 0
        except ValueError:
            pass  # 数値でない場合は下のFinviz形式チェックに進む
            
        # Finviz平均出来高形式の検証
        
        # Under/Over patterns (固定値)
        fixed_patterns = {
            # Under patterns
            'u50', 'u100', 'u500', 'u750', 'u1000',
            # Over patterns  
            'o50', 'o100', 'o200', 'o300', 'o400', 'o500', 'o750', 'o1000', 'o2000',
            # 既存の範囲パターン（下位互換性）
            '100to500', '100to1000', '500to1000', '500to10000',
            # Custom
            'frange'
        }
        
        if volume in fixed_patterns:
            return True
        
        # カスタム範囲パターン（数値to数値）の検証
        # 例: 500to2000, 100to500, 1000to5000
        import re
        range_pattern = r'^\d+to\d*$'
        if re.match(range_pattern, volume):
            return True
        
        return False
    
    return False

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
        
        # エラーで報告された無効フィールド名の正しい代替名
        'roi',  # roic (Return on Invested Capital) の代替名
        'debt_equity',  # debt_to_equity の代替名
        'book_value',  # book_value_per_share の代替名
        'performance_week',  # performance_1w の代替名
        'performance_month',  # performance_1m の代替名
        'short_float',  # float_short の代替名
        
        # その他の代替フィールド名
        'profit_margin',  # profit_marginのエイリアス
        'all',  # 全フィールド取得用の特別キー
        
        # 実際に取得されているFinvizフィールド名（104フィールド）
        '200_day_simple_moving_average', '20_day_simple_moving_average', '50_day_high', 
        '50_day_low', '50_day_simple_moving_average', '52_week_high', '52_week_low', 
        'after_hours_change', 'after_hours_close', 'all_time_high', 'all_time_low', 
        'analyst_recom', 'average_true_range', 'average_volume', 'beta', 'book_sh', 
        'cash_sh', 'change', 'change_from_open', 'company', 'country', 'current_ratio', 
        'dividend', 'dividend_yield', 'earnings_date', 'employees', 'eps_growth_next_5_years', 
        'eps_growth_next_year', 'eps_growth_past_5_years', 'eps_growth_quarter_over_quarter', 
        'eps_growth_this_year', 'eps_next_q', 'eps_surprise', 'eps_ttm', 'float_percent', 
        'forward_p_e', 'gap', 'gross_margin', 'high', 'income', 'index', 'industry', 
        'insider_ownership', 'insider_transactions', 'institutional_ownership', 
        'institutional_transactions', 'ipo_date', 'low', 'lt_debt_equity', 'market_cap', 
        'no', 'open', 'operating_margin', 'optionable', 'p_b', 'p_cash', 'p_e', 
        'p_free_cash_flow', 'p_s', 'payout_ratio', 'peg', 'performance_10_minutes', 
        'performance_15_minutes', 'performance_1_hour', 'performance_1_minute', 
        'performance_2_hours', 'performance_2_minutes', 'performance_30_minutes', 
        'performance_3_minutes', 'performance_4_hours', 'performance_5_minutes', 
        'performance_half_year', 'performance_month', 'performance_quarter', 
        'performance_week', 'performance_year', 'performance_ytd', 'prev_close', 
        'price', 'profit_margin', 'quick_ratio', 'relative_strength_index_14', 
        'relative_volume', 'return_on_assets', 'return_on_equity', 'return_on_invested_capital', 
        'revenue_surprise', 'sales', 'sales_growth_past_5_years', 'sales_growth_quarter_over_quarter', 
        'sector', 'shares_float', 'shares_outstanding', 'short_float', 'short_interest', 
        'short_ratio', 'shortable', 'target_price', 'ticker', 'total_debt_equity', 
        'trades', 'volatility_month', 'volatility_week', 'volume'
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