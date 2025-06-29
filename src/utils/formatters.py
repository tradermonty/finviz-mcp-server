from typing import List, Dict, Any, Optional
from ..models import StockData, SectorPerformance, NewsData

def format_stock_data_table(stocks: List[StockData], fields: Optional[List[str]] = None) -> str:
    """
    株式データをテーブル形式でフォーマット
    
    Args:
        stocks: 株式データのリスト
        fields: 表示するフィールドのリスト
        
    Returns:
        フォーマットされたテーブル文字列
    """
    if not stocks:
        return "No stocks found."
    
    # デフォルトフィールド
    if fields is None:
        fields = ['ticker', 'company_name', 'sector', 'price', 'price_change', 
                 'volume', 'market_cap']
    
    # ヘッダー行
    header_mapping = {
        'ticker': 'Ticker',
        'company_name': 'Company',
        'sector': 'Sector',
        'industry': 'Industry',
        'price': 'Price',
        'price_change': 'Change%',
        'volume': 'Volume',
        'market_cap': 'Market Cap',
        'pe_ratio': 'P/E',
        'relative_volume': 'Rel Vol',
        'target_price': 'Target',
        'analyst_recommendation': 'Recom'
    }
    
    headers = [header_mapping.get(field, field.title()) for field in fields]
    
    # データ行
    rows = []
    for stock in stocks:
        row = []
        for field in fields:
            value = getattr(stock, field, None)
            formatted_value = format_field_value(field, value)
            row.append(formatted_value)
        rows.append(row)
    
    # テーブル作成
    return create_ascii_table(headers, rows)

def format_large_number(num: float) -> str:
    """
    大きな数値を読みやすい形式でフォーマット
    
    Args:
        num: 数値
        
    Returns:
        フォーマットされた文字列
    """
    if num >= 1e9:
        return f"{num/1e9:.2f}B"
    elif num >= 1e6:
        return f"{num/1e6:.2f}M"
    elif num >= 1e3:
        return f"{num/1e3:.2f}K"
    else:
        return f"{num:.0f}"

def format_field_value(field: str, value: Any) -> str:
    """
    フィールド値をフォーマット
    
    Args:
        field: フィールド名
        value: 値
        
    Returns:
        フォーマットされた文字列
    """
    if value is None:
        return "N/A"
    
    # 価格フィールド
    if field in ['price', 'target_price', 'week_52_high', 'week_52_low']:
        return f"${value:.2f}" if isinstance(value, (int, float)) else str(value)
    
    # パーセンテージフィールド
    if field in ['price_change', 'dividend_yield', 'performance_1w', 'performance_1m', 
                'eps_surprise', 'revenue_surprise']:
        return f"{value:.2f}%" if isinstance(value, (int, float)) else str(value)
    
    # 出来高フィールド
    if field in ['volume', 'avg_volume']:
        return format_large_number(value) if isinstance(value, (int, float)) else str(value)
    
    # 倍率フィールド
    if field in ['relative_volume', 'pe_ratio', 'beta']:
        return f"{value:.2f}x" if isinstance(value, (int, float)) else str(value)
    
    # そのまま表示
    return str(value)

def create_ascii_table(headers: List[str], rows: List[List[str]]) -> str:
    """
    ASCII テーブルを作成
    
    Args:
        headers: ヘッダーのリスト
        rows: データ行のリスト
        
    Returns:
        ASCII テーブル文字列
    """
    if not headers or not rows:
        return ""
    
    # 各列の最大幅を計算
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(header)
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(str(row[i])))
        col_widths.append(min(max_width, 20))  # 最大20文字に制限
    
    # ヘッダー行
    header_line = "| " + " | ".join(header.ljust(col_widths[i]) for i, header in enumerate(headers)) + " |"
    separator_line = "+" + "+".join("-" * (col_widths[i] + 2) for i in range(len(headers))) + "+"
    
    # データ行
    data_lines = []
    for row in rows:
        padded_row = []
        for i, cell in enumerate(row):
            if i < len(col_widths):
                cell_str = str(cell)[:col_widths[i]]  # 幅制限
                padded_row.append(cell_str.ljust(col_widths[i]))
        data_line = "| " + " | ".join(padded_row) + " |"
        data_lines.append(data_line)
    
    # テーブル組み立て
    table_lines = [
        separator_line,
        header_line,
        separator_line
    ]
    table_lines.extend(data_lines)
    table_lines.append(separator_line)
    
    return "\n".join(table_lines)

def format_earnings_summary(stocks: List[StockData]) -> str:
    """
    決算銘柄のサマリーをフォーマット
    
    Args:
        stocks: 株式データのリスト
        
    Returns:
        フォーマットされたサマリー
    """
    if not stocks:
        return "No earnings data found."
    
    summary_lines = [
        f"Earnings Summary ({len(stocks)} stocks):",
        "=" * 50,
        ""
    ]
    
    # セクター別集計
    sector_counts = {}
    positive_surprises = 0
    negative_surprises = 0
    
    for stock in stocks:
        # セクター集計
        sector = stock.sector or "Unknown"
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        
        # サプライズ集計
        if stock.eps_surprise:
            if stock.eps_surprise > 0:
                positive_surprises += 1
            else:
                negative_surprises += 1
    
    # セクター別結果
    summary_lines.append("Sector Breakdown:")
    for sector, count in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True):
        summary_lines.append(f"  {sector}: {count} stocks")
    
    summary_lines.extend([
        "",
        "Earnings Surprises:",
        f"  Positive: {positive_surprises} stocks",
        f"  Negative: {negative_surprises} stocks",
        ""
    ])
    
    return "\n".join(summary_lines)

def format_sector_performance(sectors: List[SectorPerformance]) -> str:
    """
    セクターパフォーマンスをフォーマット
    
    Args:
        sectors: セクターパフォーマンスのリスト
        
    Returns:
        フォーマットされた文字列
    """
    if not sectors:
        return "No sector performance data found."
    
    headers = ['Sector', '1D', '1W', '1M', '3M', '6M', '1Y', 'Stocks']
    rows = []
    
    for sector in sectors:
        row = [
            sector.sector,
            f"{sector.performance_1d:.2f}%",
            f"{sector.performance_1w:.2f}%",
            f"{sector.performance_1m:.2f}%",
            f"{sector.performance_3m:.2f}%",
            f"{sector.performance_6m:.2f}%",
            f"{sector.performance_1y:.2f}%",
            str(sector.stock_count)
        ]
        rows.append(row)
    
    return create_ascii_table(headers, rows)

def format_news_summary(news_list: List[NewsData]) -> str:
    """
    ニュースデータをフォーマット
    
    Args:
        news_list: ニュースデータのリスト
        
    Returns:
        フォーマットされた文字列
    """
    if not news_list:
        return "No news found."
    
    summary_lines = [
        f"News Summary ({len(news_list)} articles):",
        "=" * 50,
        ""
    ]
    
    for news in news_list[:10]:  # 最新10件のみ表示
        summary_lines.extend([
            f"[{news.category}] {news.title}",
            f"Source: {news.source} | Date: {news.date.strftime('%Y-%m-%d %H:%M')}",
            f"URL: {news.url}",
            "-" * 40,
            ""
        ])
    
    return "\n".join(summary_lines)

def format_screening_result_summary(stocks: List[StockData], params: Dict[str, Any]) -> str:
    """
    スクリーニング結果のサマリーをフォーマット
    
    Args:
        stocks: 株式データのリスト
        params: スクリーニングパラメータ
        
    Returns:
        フォーマットされたサマリー
    """
    summary_lines = [
        f"Screening Results Summary:",
        "=" * 40,
        f"Total stocks found: {len(stocks)}",
        ""
    ]
    
    # パラメータ表示
    summary_lines.append("Search Criteria:")
    for key, value in params.items():
        if value is not None:
            summary_lines.append(f"  {key}: {value}")
    
    summary_lines.append("")
    
    if stocks:
        # 統計情報
        prices = [s.price for s in stocks if s.price is not None]
        changes = [s.price_change for s in stocks if s.price_change is not None]
        volumes = [s.volume for s in stocks if s.volume is not None]
        
        if prices:
            summary_lines.extend([
                "Statistics:",
                f"  Price range: ${min(prices):.2f} - ${max(prices):.2f}",
                f"  Average price: ${sum(prices)/len(prices):.2f}"
            ])
        
        if changes:
            summary_lines.extend([
                f"  Change range: {min(changes):.2f}% - {max(changes):.2f}%",
                f"  Average change: {sum(changes)/len(changes):.2f}%"
            ])
        
        if volumes:
            summary_lines.append(f"  Average volume: {format_large_number(sum(volumes)/len(volumes))}")
        
        summary_lines.append("")
    
    return "\n".join(summary_lines)