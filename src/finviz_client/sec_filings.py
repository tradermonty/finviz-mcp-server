import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from ..models import SECFilingData
from ..utils.exceptions import FinvizAPIError
from ..utils.validators import normalize_ticker
from .base import FinvizClient

logger = logging.getLogger(__name__)

# Finviz の latest-filings エクスポートが返す日付表記。GROUND_TRUTH.md で
# 実測済み: ``M/D/YYYY``（例 ``7/30/2026``。ゼロ埋めなし。``%m/%d/%Y`` は
# 1桁の月日も受理する）。残り2つは将来のフォーマット変更に対する保険。
_DATE_FORMATS = ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y")

# ``o=`` に渡せると実測できた値だけを許可する（2026-07-31 プローブ:
# ``o=-reportDate`` は Report Date 降順、``o=-form`` は Form 名降順で
# 実際に並び替わった）。未知の値は黙って無効なパラメータを送るのではなく
# ValueError で拒否する。
SORT_FIELD_MAP = {
    "filing_date": "filingDate",
    "filingdate": "filingDate",
    "report_date": "reportDate",
    "reportdate": "reportDate",
    "form": "form",
}


def normalize_form_name(form: str) -> str:
    """フォーム名の表記ゆれを吸収する。

    Finviz の latest-filings は保有報告書の綴りを途中で変えている。実測
    (``sec_latest_filings_aapl.csv``): 2024年以前は ``SC 13G`` / ``SC 13G/A``、
    2025年7月以降は ``SCHEDULE 13G`` / ``SCHEDULE 13G/A``。どちらも同じ
    フォームなので ``SCHEDULE 13x`` を ``SC 13x`` に寄せて比較する
    （フォーム一覧を長くするより表記非依存の比較の方が壊れにくい）。
    """
    normalized = " ".join(str(form or "").strip().upper().split())
    return re.sub(r"^SCHEDULE\s+13", "SC 13", normalized)


def form_matches(form: str, wanted: str) -> bool:
    """フォーム名が要求フォーム（およびその訂正版）に一致するか。

    ``10-K`` は ``10-K`` と ``10-K/A`` に一致し、``4`` は ``4`` と ``4/A`` に
    一致するが ``424B2``/``497`` には一致しない（単純な ``startswith`` だと
    Form 4 の要求が 424B2 を拾ってしまう）。一致条件は「完全一致」または
    「要求フォーム + ``/`` で始まる」（＝ EDGAR の訂正版表記）。
    綴りは :func:`normalize_form_name` で正規化してから比較する。
    """
    form_u = normalize_form_name(form)
    wanted_u = normalize_form_name(wanted)
    if not form_u or not wanted_u:
        return False
    return form_u == wanted_u or form_u.startswith(f"{wanted_u}/")


def matches_any_form(form: str, wanted_forms: List[str]) -> bool:
    return any(form_matches(form, wanted) for wanted in wanted_forms)


class FinvizSECFilingsClient(FinvizClient):
    """Finviz SECファイリングデータクライアント"""

    SEC_FILINGS_EXPORT_URL = f"{FinvizClient.BASE_URL}/export/latest-filings"

    # 主要フォーム。訂正版（``10-K/A`` 等）と綴り違い（``SCHEDULE 13G`` =
    # ``SC 13G``）は form_matches が吸収する。
    # 外国民間発行体向けの ``6-K``/``20-F`` を含む。
    MAJOR_FORMS = [
        "10-K",
        "10-Q",
        "8-K",
        "20-F",
        "6-K",
        "DEF 14A",
        "SC 13G",
        "SC 13D",
    ]

    # インサイダー関連フォーム: Section 16 の 3/4/5 と Rule 144 通知。
    # 訂正版（``4/A`` 等）は form_matches が拾う。
    INSIDER_FORMS = ["3", "4", "5", "144"]

    def get_sec_filings(
        self,
        ticker: str,
        form_types: Optional[List[str]] = None,
        days_back: int = 30,
        max_results: int = 50,
        sort_by: str = "filing_date",
        sort_order: str = "desc",
    ) -> List[SECFilingData]:
        """
        指定銘柄のSECファイリングデータを取得

        Args:
            ticker: 銘柄ティッカー
            form_types: フォームタイプフィルタ (例: ["10-K", "10-Q", "8-K"])。
                訂正版（``10-K/A`` 等）も一致する。
            days_back: 過去何日分のファイリング
            max_results: 最大取得件数（0 以下なら無制限）
            sort_by: ソート基準 ("filing_date", "report_date", "form")
            sort_order: ソート順序 ("asc", "desc")

        Returns:
            SECFilingData オブジェクトのリスト（該当なしの場合は空リスト）

        Raises:
            ValueError: sort_by がエンドポイントの実測サポート外の場合。
            FinvizAPIError: APIキー欠如・通信失敗・HTML応答など、リクエスト自体の
                失敗。「ファイリング無し」には変換しない（GROUND_TRUTH house rule 3）。
        """
        # パラメータの構築
        # Finviz の ``o=`` はキャメルケース。実測で通る値のみ許可する。
        finviz_sort_param = SORT_FIELD_MAP.get(str(sort_by).strip().lower())
        if finviz_sort_param is None:
            raise ValueError(
                f"Unsupported sort_by for SEC filings: {sort_by!r}. "
                f"Supported: filing_date, report_date, form."
            )
        # Finviz もクラス株はハイフン表記（``BRK-B``）。``BRK.B`` を受け取ったら
        # ここで正規化する。
        ticker = normalize_ticker(ticker) or ticker
        params = {
            "t": ticker,
            "o": (
                f"-{finviz_sort_param}" if sort_order == "desc" else finviz_sort_param
            ),
            # APIキーが無ければ FinvizAPIError を送出（従来はこの失敗自体が
            # 同じメソッド内の except に飲み込まれ「No SEC filings found」になっていた）
            "auth": self._require_api_key(),
        }

        # CSVデータを取得
        response = self._make_request(self.SEC_FILINGS_EXPORT_URL, params)

        # HTML（ログインページ等）・空ボディはここで失敗させる
        text = response.text
        self._require_csv_body(text, self.SEC_FILINGS_EXPORT_URL)

        # CSVデータをパース
        filings_data = self._parse_sec_filings_csv(text, ticker)

        # フィルタリング（訂正版フォームも含めて一致させる）
        if form_types:
            filings_data = [
                f for f in filings_data if matches_any_form(f.form, form_types)
            ]

        # 日付フィルタリング
        filings_data = self.filter_by_days_back(filings_data, days_back)

        # 最大件数制限（0 以下 = 無制限）
        if max_results and max_results > 0:
            filings_data = filings_data[:max_results]

        logger.info(f"Retrieved {len(filings_data)} SEC filings for {ticker}")
        return filings_data

    def get_recent_filings_by_form(
        self, ticker: str, form_type: str, limit: int = 10
    ) -> List[SECFilingData]:
        """
        特定のフォームタイプの最新ファイリングを取得

        Args:
            ticker: 銘柄ティッカー
            form_type: フォームタイプ (例: "10-K", "10-Q", "8-K")
            limit: 最大取得件数

        Returns:
            SECFilingData オブジェクトのリスト
        """
        return self.get_sec_filings(
            ticker=ticker,
            form_types=[form_type],
            days_back=365,  # 1年分
            max_results=limit,
            sort_by="filing_date",
            sort_order="desc",
        )

    def get_major_filings(
        self, ticker: str, days_back: int = 90
    ) -> List[SECFilingData]:
        """
        主要フォームのファイリングを取得

        対象は 10-K / 10-Q / 8-K / 20-F / 6-K / DEF 14A / SC 13G / SC 13D と
        それぞれの訂正版（``10-K/A``, ``SC 13G/A`` …）。20-F・6-K は外国民間
        発行体の年次・臨時報告に相当するため含める。

        Args:
            ticker: 銘柄ティッカー
            days_back: 過去何日分

        Returns:
            SECFilingData オブジェクトのリスト
        """
        return self.get_sec_filings(
            ticker=ticker,
            form_types=list(self.MAJOR_FORMS),
            days_back=days_back,
            max_results=50,
            sort_by="filing_date",
            sort_order="desc",
        )

    def get_insider_filings(
        self, ticker: str, days_back: int = 30
    ) -> List[SECFilingData]:
        """
        インサイダー取引関連のファイリング（フォーム4等）を取得

        対象は Section 16 の Form 3 / 4 / 5、Rule 144 売却通知（Form 144）、
        およびそれぞれの訂正版（``4/A`` 等）。

        以前含めていた **11-K は除外**した: 11-K は従業員給付制度（401(k) 等）の
        年次報告であり、インサイダー個人の売買を示すものではない。

        Args:
            ticker: 銘柄ティッカー
            days_back: 過去何日分

        Returns:
            SECFilingData オブジェクトのリスト
        """
        return self.get_sec_filings(
            ticker=ticker,
            form_types=list(self.INSIDER_FORMS),
            days_back=days_back,
            max_results=30,
            sort_by="filing_date",
            sort_order="desc",
        )

    def _parse_sec_filings_csv(self, csv_text: str, ticker: str) -> List[SECFilingData]:
        """
        CSV形式のSECファイリングデータをパースしてSECFilingDataオブジェクトのリストに変換

        Args:
            csv_text: CSV形式のテキスト
            ticker: 銘柄ティッカー

        Returns:
            SECFilingData オブジェクトのリスト
        """
        try:
            # CSVテキストをDataFrameに変換（エラー処理を強化）
            from io import StringIO

            # CSVパラメータを調整してエラーを回避
            df = pd.read_csv(
                StringIO(csv_text),
                on_bad_lines="skip",  # 不正な行をスキップ
                dtype=str,  # 全てを文字列として読み込み
                na_filter=False,  # NAフィルタを無効化
            )

            logger.info(f"Successfully parsed CSV with {len(df)} rows")

            filings = []
            for idx, row in df.iterrows():
                try:
                    # 安全にデータを取得（デフォルト値を設定）
                    filing_date = str(row.get("Filing Date", "")).strip()
                    report_date = str(row.get("Report Date", "")).strip()
                    form = str(row.get("Form", "")).strip()
                    description = str(row.get("Description", "")).strip()
                    filing_url = str(row.get("Filing", "")).strip()
                    document_url = str(row.get("Document", "")).strip()

                    # 必須フィールドの検証
                    if not filing_date or not form:
                        logger.warning(f"Skipping row {idx}: missing required fields")
                        continue

                    filing = SECFilingData(
                        ticker=ticker,
                        filing_date=filing_date,
                        report_date=report_date if report_date else filing_date,
                        form=form,
                        description=description if description else f"{form} filing",
                        filing_url=filing_url,
                        document_url=document_url,
                    )
                    filings.append(filing)

                except Exception as e:
                    logger.warning(f"Failed to parse filing row {idx}: {e}")
                    continue

            logger.info(f"Successfully parsed {len(filings)} filings for {ticker}")
            return filings

        except Exception as e:
            # レスポンス全体が読めないのは失敗であって「ファイリング0件」ではない
            csv_preview = csv_text[:500] if csv_text else "Empty CSV"
            logger.error(f"Error parsing SEC filings CSV: {e}")
            logger.debug(f"CSV preview: {csv_preview}")
            raise FinvizAPIError(
                f"Could not parse the Finviz SEC filings response for {ticker} "
                f"as CSV: {e}"
            ) from e

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        日付文字列をdatetimeオブジェクトに変換

        パースできない場合は **None** を返す（旧実装は ``datetime.now()`` を
        返しており、日付が読めない＝常に「今日」＝ days_back フィルタを
        素通りしていた）。行ごとの warning も出さない。呼び出し側
        (:meth:`filter_by_days_back`) が 1 コールにつき 1 回だけ件数付きで
        ログする。

        Args:
            date_str: 日付文字列（Finviz は ``M/D/YYYY``）

        Returns:
            datetime オブジェクト、またはパース不能なら None
        """
        if not date_str:
            return None
        text = str(date_str).strip()
        if not text:
            return None
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None

    def filter_by_days_back(
        self,
        filings: List[SECFilingData],
        days_back: int,
        now: Optional[datetime] = None,
    ) -> List[SECFilingData]:
        """``filing_date`` が直近 ``days_back`` 日以内のファイリングだけを返す。

        日付をパースできなかったファイリングは **除外**する（期間指定の結果に
        素性の分からない行を混ぜない）。除外件数は 1 コールにつき 1 行だけ
        warning に集約する（news ツールと同じ方式）。

        Args:
            filings: フィルタ対象
            days_back: 0 以下なら日付フィルタを行わない
            now: 基準時刻（テスト用。省略時は ``datetime.now()``）
        """
        if not filings or days_back is None or days_back <= 0:
            return list(filings)

        reference = now or datetime.now()
        cutoff_date = reference - timedelta(days=days_back)

        kept: List[SECFilingData] = []
        unparseable = 0
        for filing in filings:
            parsed = self._parse_date(filing.filing_date)
            if parsed is None:
                unparseable += 1
                continue
            if parsed >= cutoff_date:
                kept.append(filing)

        if unparseable:
            logger.warning(
                "Dropped %d SEC filing(s) with an unparseable filing date "
                "while applying the %d-day window",
                unparseable,
                days_back,
            )

        return kept

    def get_filing_summary(self, ticker: str, days_back: int = 90) -> Dict[str, Any]:
        """
        指定期間のファイリング概要を取得

        件数・内訳は **期間内の全ファイリング** に対して数える（旧実装は
        100 件で打ち切ったうえで "Total Filings: 100" と表示し、比率もその
        上限に対する値になっていた）。

        Args:
            ticker: 銘柄ティッカー
            days_back: 過去何日分

        Returns:
            ファイリング概要の辞書
        """
        try:
            filings = self.get_sec_filings(
                ticker,
                days_back=days_back,
                max_results=0,  # 0 = 無制限。集計は期間内の全件に対して行う
                sort_by="filing_date",
                sort_order="desc",
            )

            if not filings:
                return {"ticker": ticker, "total_filings": 0, "forms": {}}

            # フォームタイプ別集計
            form_counts = {}
            for filing in filings:
                form_type = filing.form
                if form_type not in form_counts:
                    form_counts[form_type] = 0
                form_counts[form_type] += 1

            # 最新ファイリング日（パース不能な日付は最古扱いにして落とす）
            latest_filing = max(
                filings,
                key=lambda x: self._parse_date(x.filing_date) or datetime.min,
            )

            summary = {
                "ticker": ticker,
                "total_filings": len(filings),
                "forms": form_counts,
                "latest_filing_date": latest_filing.filing_date,
                "latest_filing_form": latest_filing.form,
                "period_days": days_back,
            }

            return summary

        except FinvizAPIError:
            # リクエスト失敗は「0件のサマリー」に変換しない
            raise
        except Exception as e:
            logger.error(f"Error generating filing summary for {ticker}: {e}")
            return {"ticker": ticker, "error": str(e)}
