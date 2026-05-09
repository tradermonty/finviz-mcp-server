# Review Findings Tracking

レビュー指摘事項の対応状況を記録するトラッキング表。

## Status Legend

- 🔴 Open: 未着手
- 🟡 In Progress: Issue / PR 作成済み、レビュー待ち
- 🟢 Done: マージ済み
- 🔵 Approved (waiting merge): リポジトリレビュー で Approve 済み、マージ待ち
- ⚪ Deferred: 別途対応 / スコープ外
- ⛔ Blocked: 他者 PR で要対応 / Request changes

## Findings

| # | Source | Priority | Finding | Issue | PR | Status | Notes |
|---|--------|----------|---------|-------|----|----|-------|
| 1 | pr-6-review-2026-05-07.md | Medium | `price_change_min` preset guard が `_safe_numeric_conversion` 後の値を見ており機能しない | (PR #6 内対応) | [#6](https://github.com/tradermonty/finviz-mcp-server/pull/6) | 🟢 Done | コミット 3c19d95 で修正、main にマージ済み (9a18400)。重複ハンドラ削除 + 上流ブロックに一元化。回帰テスト5件追加。 |
| 2 | code-review-2026-05-07.md | High | `pyproject.toml` に `mcp` / `sec-edgar-api` が未登録。クリーン環境で import 失敗 | [#7](https://github.com/tradermonty/finviz-mcp-server/issues/7) | [#8](https://github.com/tradermonty/finviz-mcp-server/pull/8) | 🟢 Done | main にマージ済み。 |
| 3 | code-review-2026-05-07.md | Medium | `run_tests.py` がサブプロセスで `python` / `pip` を直接呼び出すため、別 interpreter / 不在環境で失敗 | [#9](https://github.com/tradermonty/finviz-mcp-server/issues/9) | [#10](https://github.com/tradermonty/finviz-mcp-server/pull/10) | 🟢 Done | main にマージ済み。 |
| 4 | code-review-2026-05-07.md | Medium | `get_relative_volume_stocks` の inline conditional で `0` 値が `N/A` になる + 表示崩れ | [#11](https://github.com/tradermonty/finviz-mcp-server/issues/11) | [#12](https://github.com/tradermonty/finviz-mcp-server/pull/12) | 🟢 Done | main にマージ済み。`volume=0` の明示的 assertion フォローアップ含む。 |
| 5 | code-review-2026-05-07.md | Low | pytest 9 で `tests/test_basic.py` の test 関数が値を返しており `PytestReturnNotNoneWarning` | [#13](https://github.com/tradermonty/finviz-mcp-server/issues/13) | [#14](https://github.com/tradermonty/finviz-mcp-server/pull/14) | 🟢 Done | main にマージ済み。 |
| 6 | repository-prs-review-2026-05-07.md | **P1** | PR #3: HTTP transport で DNS rebinding 保護がデフォルト無効化、`MCP_HOST=0.0.0.0` 公開でセキュリティ後退 | (PR #3 author 対応待ち) | [#3](https://github.com/tradermonty/finviz-mcp-server/pull/3) | ⛔ Blocked | **Security regression**。`src/server.py:2080-2107`, `Dockerfile:25`。DNS rebinding protection をデフォルト enabled に。 |
| 7 | repository-prs-review-2026-05-07.md | **P1** | PR #3: 実行可能 Python ファイル先頭に UTF-8 BOM (`ef bb bf`) が混入、shebang 無効化 | (PR #3 author 対応待ち) | [#3](https://github.com/tradermonty/finviz-mcp-server/pull/3) | ⛔ Blocked | `run_server.py:1`, `run_release_tests.py:1`, `src/server.py:1` 他。pre-commit に encoding チェック追加推奨。 |
| 8 | repository-prs-review-2026-05-07.md | P2 | PR #3: タイトルと無関係なテキスト churn (`Unit testsrun`, `Environment checkrunning...`, `detectstocks` 等) でレポート出力が破損 | (PR #3 author 対応待ち) | [#3](https://github.com/tradermonty/finviz-mcp-server/pull/3) | ⛔ Blocked | PR を transport / security 専用に分割推奨。無関係な書き換えを revert。 |
| 9 | P2-2 派生 (parser/CSV view) | High | `week_52_high` と `high_52w_relative` が同じ `52-Week High` カラムにマップ。v=151 では絶対価格でなく percent が返る | [#17](https://github.com/tradermonty/finviz-mcp-server/issues/17) | [#22](https://github.com/tradermonty/finviz-mcp-server/pull/22) (旧 #20) | 🟢 Done | main にマージ済み。 |
| 10 | P2-2 派生 (parser/CSV view) | High | `above_sma_*` 未populate、`sma_*` に percent が誤格納 (v=151 に SMA20/50/200 カラムなし、SMA カラムは relative %) | [#18](https://github.com/tradermonty/finviz-mcp-server/issues/18) | [#23](https://github.com/tradermonty/finviz-mcp-server/pull/23) (旧 #21) | 🟢 Done | main にマージ済み。E2E invariant の SMA 系も有効化、`E2E_TESTING.md` 更新済み。 |
| 11 | P2-2 派生 (parser/CSV view) | Medium | `eps_revision` が earnings_trading で常に None (v=151 の CSV columns に `EPS Revision` が含まれない) | [#19](https://github.com/tradermonty/finviz-mcp-server/issues/19) | [#28](https://github.com/tradermonty/finviz-mcp-server/pull/28) | 🟢 Done | 複数 view (v=151/152/120/130/141/161/170) を probe して `EPS Revision` カラム不在を確定 → option C (仕様化) を採用。`models.py` / `base.py` に limitation コメント、E2E に reference 化、parser unit tests 2件追加（None 維持 + 将来 Finviz が追加した時の forward-compat 双方向 pin）。 |
| 12 | pr-20-21-parser-followups-review-2026-05-07.md | P2 | PR #22 と PR #23 は `src/finviz_client/base.py` の同じ post-processing 挿入位置で conflict | (両 PR に conflict resolution 注記) | [#22](https://github.com/tradermonty/finviz-mcp-server/pull/22) / [#23](https://github.com/tradermonty/finviz-mcp-server/pull/23) | 🟢 Done | PR #22 先行 merge → PR #23 を rebase して conflict 解消（両 helper 呼び出しと本体を保持）→ merge 完了。 |
| 13 | pr-22-23-parser-followups-rereview-2026-05-07.md | P2 | `sma_50_above_sma_200()` の `field_getter` が `s.sma_50` のみを返すため、`sma_50` present + `sma_200` 欠損の行で false-positive violation を出す | [#25](https://github.com/tradermonty/finviz-mcp-server/issues/25) | [#26](https://github.com/tradermonty/finviz-mcp-server/pull/26) | 🟢 Done | main にマージ済み。`field_getter` を pair return 化、unit test 4件で partial / UNVERIFIABLE / 正規違反を保証。Re-review 指摘の assertion 厳密化フォローアップも反映 (4214275)。 |
| 14 | E2E suite full run 2026-05-09 | Medium | E2E suite (`pytest --run-e2e -m e2e`) で 12 件 fail。すべてテスト側の API drift（result-shape / tool signature / error model） | [#34](https://github.com/tradermonty/finviz-mcp-server/issues/34) | [#35](https://github.com/tradermonty/finviz-mcp-server/pull/35) | 🟢 Done | server.py 不変。3 カテゴリすべてテスト側で対応: (A) FastMCP `convert_result()` の `(unstructured, structured)` tuple 返却に合わせ `result[0][0].text` へ更新 / (B) `get_stock_news` の `ticker` → `tickers` パラメータ訂正 / (C) FastMCP wrap → `McpToolError` で受ける / catch 済み tool は error TextContent assert に書き換え。結果: **75 passed / 3 skipped (legitimate 市場閉場)** に到達。 |
| 15 | pr-35-e2e-suite-api-drift-postmerge-review-2026-05-09.md | P1+P2 | `tests/test_e2e_screeners.py` で **P1** mock target drift × 2（`get_relative_volume_stocks` / `technical_analysis_screener` が `screen_stocks()` ではなく専用メソッドを patch）+ **P1** stale args × 9 + **P2** fixed-criteria tools への引数渡し × 3。FastMCP が unknown args を silently drop するため false-positive coverage。 | [#38](https://github.com/tradermonty/finviz-mcp-server/issues/38) | [#39](https://github.com/tradermonty/finviz-mcp-server/pull/39) | 🟢 Done | server.py 不変。`screen_stocks` を patch するように変更し flat signature 化、stale args (`limit` / `category` / `timeframe` / `sort_by` / `time_range` / `expected_move` / `technical_criteria` / 不要 `market_cap`) を全削除、fixed-criteria 3 tools は `{}` 呼び出し + `assert_called_once_with()`、各 test に `mock.call_count == len(test_cases)` の strict assertion 追加。news mock を `NewsData` object 化。**39 passed in 19.42s**（旧: 同一 2 tests で 32.08s）。out-of-scope: `validate_tickers` がリスト拒絶する docstring 不一致は別 issue。 |
| 16 | project-quality-rescore-2026-05-09.md (PR B) | High | Default `pytest -q` が **13 failed**。MCP tool の top-level `except Exception` が catch して error TextContent を返すため、テストが期待する `pytest.raises(McpToolError)` が成立しない。 | [#43](https://github.com/tradermonty/finviz-mcp-server/issues/43) | [#44](https://github.com/tradermonty/finviz-mcp-server/pull/44) | 🟢 Done | 全 34 ハンドラを `raise` に統一して FastMCP に boundary wrap させる。test_e2e_screeners / test_comprehensive_e2e_real_calls の 4 テストは旧 catch 前提から `pytest.raises(McpToolError)` に書き換え。副作用で 6 ファイルにまたがる 65 skip marker（64 test-level + `test_financial_parameters.py` module-level 1 件、実効 79 tests）の quasi-integration false-positive coverage が露出 → `@pytest.mark.skip(... tracked as #42)` で一時無効化（再 enable は #42）。**0 failed** 達成（190 passed / 145 skipped）。 |
| 17 | project-quality-rescore-2026-05-09.md (PR C) | Medium | CI test job が 7-file allowlist (48 tests) に制限されており、品質を gate していない。Deferred Risk **R2** (marker separation) も未解消。 | (PR 内対応) | [#45](https://github.com/tradermonty/finviz-mcp-server/pull/45) | 🟢 Done | `pytest -m "not e2e"` に切替（254 collected → 187 passed / 67 skipped / 76 deselected）。tests/test_edgar_api.py は collection 時に sec_edgar_api / pyrate-limiter API mismatch で import 失敗するため `--ignore=` で除外（PR E で正式対応）。R2 解消。 |
| 18 | project-quality-rescore-2026-05-09.md (PR D1) | Medium | `black` reformat 対象 48 files、`flake8` 2,512 findings の 81% (W293 系) が残存。 | (PR 内対応) | [#46](https://github.com/tradermonty/finviz-mcp-server/pull/46) | 🟢 Done | `black` + `isort` を一括適用。**機械整形のみ**（semantic 変更なし）。`black --check` / `isort --check-only` 共に 0。flake8 は 2,512 → 111 に圧縮。 |
| 19 | project-quality-rescore-2026-05-09.md (PR D2) | Medium | flake8 残 violation 111 件 + lint job が `continue-on-error` で gate 化されていない。 | (PR 内対応) | [#47](https://github.com/tradermonty/finviz-mcp-server/pull/47) | 🟢 Done | autoflake で F401/F811 除去、F541 は AST col-based に leading `f` を除去、E712 は `is True/False` 化、E303/E304/W391 は黒残処理、E402 / F841 は構造的に必要な箇所に `# noqa` (理由コメント付き) を貼った。**flake8 0 findings** 達成。lint job を hard gate 昇格、pyproject dev extras に `isort`/`pre-commit`/`autoflake` 追加。typecheck は引き続き informational（mypy strict 化は 85 到達後）。 |
| 20 | project-quality-rescore-2026-05-09.md (PR E) | High | `EdgarClientStub` が disabled-error を固定で返し、登録済み 5 EDGAR API tools が機能していない。`EDGAR_USER_AGENT` 必須化も未実装。 | (PR 内対応) | [#48](https://github.com/tradermonty/finviz-mcp-server/pull/48) | 🟢 Done | stub 削除、`_get_edgar_client()` の lazy init 追加（`EDGAR_USER_AGENT` 未設定なら `ValueError`、PR B 後の error model で boundary wrap）。**5 EDGAR API tools のみ** 切替（`get_edgar_filing_content` / `..._multiple_..._contents` / `..._company_filings` / `..._company_facts` / `..._company_concept`）。**Finviz SEC tools 4 本は touch せず**（`get_sec_filings` / `..._major_...` / `..._insider_...` / `..._summary` は `FinvizSECFilingsClient` 経由で USER_AGENT 不要）。`tests/test_edgar_lazy_init.py` 3 件追加（`monkeypatch.setattr(server_module, "_edgar_client", None)` の autouse fixture でテスト順依存を防止）。 |
| 21 | project-quality-rescore-2026-05-09.md (PR F) | High | HTTP/SSE bind が `MCP_HOST` default `0.0.0.0` で全 NIC 公開（host 直接実行時）。 | (PR 内対応) | [#49](https://github.com/tradermonty/finviz-mcp-server/pull/49) | 🟢 Done | 直接実行時の default を **`127.0.0.1`** に変更。`MCP_HOST=0.0.0.0` を明示設定したときは安全な代替策（host port 制限 `-p 127.0.0.1:8000:8000`）と DNS rebinding (Finding #6) を案内する warning を出力。**Dockerfile はそのまま**（コンテナ内 loopback bind を強制すると port publishing が壊れるため）。README に Docker 利用パターンと security note 追記。 |

## Remaining Risks (Deferred)

| # | Risk | Status | Notes |
|---|------|--------|-------|
| R1 | `tests/test_mcp_integration.py` が現行の `mcp` API とずれており複数失敗 | ⚪ Deferred | `FastMCP.list_tools()` の同期/非同期扱いが異なる。別途 issue 化を検討。 |
| ~~R2~~ | ~~ネットワーク / API キー前提テストが unit テストと混在~~ | 🟢 Resolved | PR #45 (PR C) で CI test job を `pytest -m "not e2e"` に切替し、`tests/conftest.py` の `LIVE_TEST_FILENAME_PATTERNS` auto-mark を活用。 |
| R3 | `src/server.py` が肥大（MCPツール層・validation・formatting・client が密結合） | ⚪ Deferred | ツール毎の formatter / validation の分割をリファクタリング issue として整理。85+ phase で対応予定。 |

## Quality Infrastructure

| ファイル | 状態 | PR | 備考 |
|---|---|---|---|
| `.flake8` | 🟢 Done | [#30](https://github.com/tradermonty/finviz-mcp-server/pull/30) | Linter 設定 |
| `.pre-commit-config.yaml` | 🟢 Done | [#30](https://github.com/tradermonty/finviz-mcp-server/pull/30) | pre-commit hooks |
| `.github/workflows/ci.yml` | 🟢 Done | [#30](https://github.com/tradermonty/finviz-mcp-server/pull/30) | GitHub Actions CI（lint/typecheck は informational、test は explicit allowlist） |
| `tests/conftest.py` | 🟢 Done | [#16](https://github.com/tradermonty/finviz-mcp-server/pull/16) | テスト共通 fixture (e2e auto-marker / auto-skip) |
| `tests/test_e2e_screener_invariants.py` | 🟢 Done | [#16](https://github.com/tradermonty/finviz-mcp-server/pull/16) | E2E スクリーナー不変式テスト |
| `scripts/run_e2e_invariants.py` | 🟢 Done | [#16](https://github.com/tradermonty/finviz-mcp-server/pull/16) | E2E 実行スクリプト |
| `tests/E2E_TESTING.md` | 🟢 Done | [#16](https://github.com/tradermonty/finviz-mcp-server/pull/16) | E2E テスト手順書 |

PR #30 のフォローアップ完了状況:
1. ~~Codebase format PR~~ → **PR #46 / #47 で完了**（black/isort + 残 flake8 全件修正、lint hard gate 化）
2. ~~Marker separation (Deferred Risk R2)~~ → **PR #45 で完了**（`pytest -m "not e2e"` を CI test gate に）
3. **mypy strictness 調整** → 残課題（85+ phase で対応）

## Snapshot (2026-05-09)

| 観点 | 値 |
|---|---|
| Findings | 21（🟢 Done 18 / ⛔ Blocked 3） |
| Open PRs | 0 |
| Open Issues | 1（[#42](https://github.com/tradermonty/finviz-mcp-server/issues/42) — final batch で quarantine 解消済み。PR merge 後に close 可能） |
| Quality Infrastructure | 7/7 main 取り込み済み + lint hard gate 化済み |
| `pytest -q` (default) | **261 passed / 79 skipped / 0 failed**（旧: 13 failed） |
| `pytest --run-e2e -m e2e tests/test_e2e_screeners.py` | **39 passed / 0 failed**（live-data/time-dependent duration 変動あり） |
| `black --check` / `isort --check-only` / `flake8` | 全て **0 findings** |
| CI test job scope | `pytest -m "not e2e"`（旧: 7-file allowlist） |
| EDGAR tools | 5 EDGAR API tools が `EDGAR_USER_AGENT` lazy init で稼働可能（Finviz SEC tools 4 本は不変） |
| HTTP/SSE bind default (host 直接実行) | `127.0.0.1` + 0.0.0.0 設定時の warning |
| Score | 74 → **85+ 想定**（再評価依頼予定） |

⛔ Blocked 3 件（#6 / #7 / #8）はすべて外部 author の PR #3 への要対応で、本リポジトリ側からの追加対応は不要。Open Issue #42 は PR B 副作用で表面化した false-positive coverage の本格修正。現在の #42 quarantine は 0 marker occurrences / 実効 0 tests。

### Issue #42 Quarantine Inventory

| File | Marker count | Effective skipped tests | Next action |
|---|---:|---:|---|
| `tests/test_error_handling.py` | 0 | 0 | Restored with shared `tests.factories`, explicit FastMCP `ToolError` expectations, and current validation/delegation contracts. |
| `tests/test_mcp_integration.py` | 0 | 0 | Restored with shared `tests.factories` model-shaped mocks and current FastMCP tuple return handling. |
| `tests/test_parameter_combinations.py` | 0 | 0 | Restored with shared `tests.factories`, current tool signatures, and correct `screen_stocks` delegation patches. |
| `tests/test_comprehensive_parameters.py` | 0 | 0 | Restored with model-shaped mocks, `custom_screener` raw filter forwarding, and current `technical_analysis_screener` `screen_stocks` delegation. |
| `tests/test_e2e_screeners.py` | 0 | 0 | Restored mocked E2E screener paths with model-shaped responses and current fixed-criteria tool signatures. |
| `tests/test_financial_parameters.py` | 0 | 0 | Restored with model-shaped mocks and `custom_screener` raw financial filter forwarding. |
| **Total** | **0** | **0** | Track under [#42](https://github.com/tradermonty/finviz-mcp-server/issues/42). |

## Update History

- 2026-05-07: 初版作成。PR #6 のレビュー指摘1件は対応済み。
- 2026-05-07: code-review-2026-05-07.md の High 1件・Medium 2件・Low 1件について Issue (#7, #9, #11, #13) と PR (#8, #10, #12, #14) を作成。
- 2026-05-07: repository-prs-review-2026-05-07.md の結果を反映。PR #8/#10/#12/#14/#15 が Approved 判定。PR #12 にはフォローアップ assertion を追加。PR #3 に P1×2 / P2×1 の blocker 判定（コメント投稿はユーザー判断で見送り、ローカル tracker のみに記録）。
- 2026-05-07: P2-2 派生 parser/CSV view 問題 3件を確認 → Issue #17 / #18 / #19、PR #20 / #21 を作成。PR #21 にレビュー対応で E2E invariant 有効化フォローアップを追加。
- 2026-05-07: PR #8/#10/#12/#14/#15/#16 が main にマージ。Status を 🟢 Done に更新。
- 2026-05-07: リポジトリ全体の commit author を `tradermonty <205491838+tradermonty@users.noreply.github.com>` に統一する rewrite を実施（`git filter-repo --mailmap`、97 commits）。プレースホルダ email と旧 author entries を全置換。全ブランチを force-push。副作用として PR #20 / #21 が auto-close されたため、同一内容で **PR #22 / #23** として再オープン。
- 2026-05-07: PR #22 を main にマージ。PR #23 を rebase して conflict 解消（`_compute_sma_fields` と `_compute_absolute_52w_extremes` の両 helper を共存）→ merge 完了。Status #9 / #10 / #12 を 🟢 Done に更新。
- 2026-05-07: pr-22-23-parser-followups-rereview-2026-05-07.md の P2 finding (sma_50_above_sma_200 field_getter) を反映 → Issue #25 / PR #26 を作成。Finding #13 として追加。
- 2026-05-07: pr-26-27-sma-pair-rereview-2026-05-07.md で PR #26 / #27 とも Approve。non-blocking で UNVERIFIABLE assertion の厳密化指摘を受けて 4214275 で対応 → PR #26 を main にマージ。Finding #13 を 🟢 Done に更新。
- 2026-05-08: Issue #19 (`eps_revision` 不在) について、複数 Finviz Elite view (v=151/152/120/130/141/161/170) を probe して "EPS Revision" カラムがどの view にも存在しないことを確定 → Option C (仕様化) を採用した PR #28 を作成・マージ。`models.py` / `base.py` に limitation コメント追加、forward-compat の双方向 parser unit test 2件 (`tests/test_parser_unit_contracts.py::TestEpsRevisionUnfetchable`) で pin。Finding #11 を 🟢 Done に更新。bonus として `ta_highlow52w_a30h` の Finviz semantic 不整合を実データ (17/725 stocks beyond -30%) で確認、E2E コメントを更新。
- 2026-05-08: Quality Infrastructure (`.flake8` / `.pre-commit-config.yaml` / `.github/workflows/ci.yml`) を PR #30 で取り込み開始。CI は existing codebase の状態を考慮し、lint/typecheck は informational、test は explicit allowlist (今日の offline regression tests 7ファイル / 48 tests) で起動。フォローアップとして codebase format PR、marker separation (R2)、mypy strictness 調整を予定。
- 2026-05-09: E2E suite full run で 12 件 fail を確認。原因 3 カテゴリ（FastMCP `convert_result()` の tuple 返却、`get_stock_news` のパラメータ名 drift、`McpToolError` wrap / catch+error TextContent の error model 二系統）すべてテスト側修正で解消した PR #35 を作成・マージ → Issue #34 close。**75 passed / 3 skipped (legitimate 市場閉場) / 0 failed** で E2E suite green 化。Finding #14 として追加。server.py / src/finviz_client/* は不変。
- 2026-05-09: Quality Infrastructure 3 ファイル（`.flake8` / `.pre-commit-config.yaml` / `.github/workflows/ci.yml`）の Status を 🟡 In Progress → 🟢 Done に修正（PR #30 は既に 04:13 にマージ済みだったが tracker 反映が漏れていた）。Obsolete な "Recommended Merge Order" section を削除し、Snapshot セクションで現在のリポジトリ状態を集約表示。これにより全 14 findings のうち 11 件解決・3 件 ⛔ Blocked（外部 PR #3 待ち）の最終形に整理。
- 2026-05-09: PR #35 の post-merge review (`reviews/pr-35-e2e-suite-api-drift-postmerge-review-2026-05-09.md`) で `tests/test_e2e_screeners.py` の false-positive coverage を指摘 → Issue #38 / PR #39 として対応・マージ。**P1** mock target drift 2件（`get_relative_volume_stocks` / `technical_analysis_screener` を `screen_stocks()` patch に修正）+ **P1** stale args 9件 + **P2** fixed-criteria 3件 を解消。`mock.call_count == len(test_cases)` / `assert_called_once_with()` の strict assertion を全テストに追加し、news mock を `NewsData` object 化。verification: `pytest --run-e2e -m e2e tests/test_e2e_screeners.py` 39 passed in 19.42s（旧: 2 tests で 32.08s = live retry 経路に落ちていた証跡）/ full suite 75 passed / offline 48 passed。Finding #15 として追加。server.py 不変。out-of-scope として `validate_tickers` がリスト拒絶する docstring 不一致を別 issue 候補として記録。
- 2026-05-09: `reviews/project-quality-rescore-2026-05-09.md` で品質スコア 74/100 を提示。85 までの優先度（Default red 解消 / CI 拡大 / lint baseline / EDGAR / HTTP bind）に沿って **6 PR を順次 merge**:
  - **Finding #16 / PR #44 (PR B)**: server.py の全 top-level `except Exception` を `raise` に統一 → FastMCP boundary で `ToolError` wrap。default pytest **13 failed → 0 failed**。副作用で 6 ファイル / 65 skip marker（実効 79 tests）の quasi-integration false-positive coverage が露出 → Issue #42 で追跡し本 PR 内では `@pytest.mark.skip` 化。
  - **Finding #17 / PR #45 (PR C)**: CI test job を `pytest -m "not e2e"` に拡張（254 collected 規模に。tests/conftest.py の auto-mark で e2e は自動 skip）。Deferred Risk **R2** 解消。
  - **Finding #18 / PR #46 (PR D1)**: `black src/ tests/` + `isort src/ tests/` 機械整形のみ。48 files reformat、semantic 変更なし。flake8 2,512 → 111。
  - **Finding #19 / PR #47 (PR D2)**: 残 flake8 violation 111 件すべて修正（autoflake / AST f-string / `is True` 化 / 構造的に必要な箇所への `# noqa: F841|E402`）。lint job を hard gate 昇格（`continue-on-error` 削除）。`pyproject.toml` dev extras に `isort` / `pre-commit` / `autoflake` 追加。
  - **Finding #20 / PR #48 (PR E)**: `EdgarClientStub` 撤去 → `_get_edgar_client()` lazy init + `EDGAR_USER_AGENT` 必須化。**5 EDGAR API tools のみ** 切替、Finviz SEC 4 tools は不変（USER_AGENT 不要）。`tests/test_edgar_lazy_init.py` で autouse fixture により singleton リセットしテスト順依存を防止。
  - **Finding #21 / PR #49 (PR F)**: 直接実行時の `MCP_HOST` default を `127.0.0.1` に変更、0.0.0.0 設定時に warning 出力。Dockerfile はそのまま、README で Docker 利用時の `-p 127.0.0.1:8000:8000` パターンを案内。
  これにより default pytest red、CI 制限、lint debt、EDGAR stub、public bind の 5 blocker をすべて解消。スコア 74 → 85+ に到達した想定で再評価依頼を準備。85 到達には不要として Out of scope に保留したのは server.py / base.py 分割（Finding #6 系）のみ。
- 2026-05-09: Issue #42 の first batch として `tests/test_mcp_integration.py` の 10 skip を復帰。`tests.factories` の model-shaped mocks、FastMCP tuple return helper、current tool signatures / patch targets (`screen_stocks`) に揃え、`pytest tests/test_mcp_integration.py -q` は **18 passed / 1 skipped / 0 failed**。default pytest は **205 passed / 135 skipped / 0 failed** まで改善。#42 quarantine は **55 marker occurrences / 実効 69 tests** に減少。
- 2026-05-09: Issue #42 second batch として `tests/test_error_handling.py` の 11 skip を復帰。dict-shaped screener responses を `tests.factories` の model-shaped list に置換し、malformed data は `McpToolError`、empty data は normal no-result response、relative-volume は `screen_stocks` delegation として明示的に pin。`pytest tests/test_error_handling.py -q` は **24 passed / 0 skipped / 0 failed**。default pytest は **216 passed / 124 skipped / 0 failed** まで改善。#42 quarantine は **44 marker occurrences / 実効 58 tests** に減少。
- 2026-05-09: Issue #42 third batch として `tests/test_parameter_combinations.py` の 12 skip を復帰。parameter matrix の旧 dict responses を `tests.factories` の model-shaped list に置換し、news は `NewsData`、sector/industry/country は server formatter が読む dict keys に同期。`get_relative_volume_stocks` / `technical_analysis_screener` は `screen_stocks` patch、`upcoming_earnings_screener` は dynamic `current_price` / `target_price_upside` を持つ factory object で pin。`pytest tests/test_parameter_combinations.py -q` は **15 passed / 0 skipped / 0 failed**。default pytest は **228 passed / 112 skipped / 0 failed** まで改善。#42 quarantine は **32 marker occurrences / 実効 46 tests** に減少。
- 2026-05-09: Issue #42 fourth batch として `tests/test_e2e_screeners.py` の 13 skip を復帰。旧 dict-shaped screener responses を `tests.factories` の model-shaped list に置換し、fixed-criteria screeners (`volume_surge_screener` / `uptrend_screener` / earnings timing screeners) は stale args を渡さず `{}` 呼び出しに統一。`dividend_growth_screener` / `etf_screener` は current signatures に同期。`pytest --run-e2e -m e2e tests/test_e2e_screeners.py -q` は **39 passed / 0 failed**。#42 quarantine は **19 marker occurrences / 実効 33 tests** に減少。
- 2026-05-09: Issue #42 fifth batch として `tests/test_comprehensive_parameters.py` の 18 skip を復帰。存在しない high-level wrapper 引数は `custom_screener` の raw Finviz filter forwarding に移し、`screen_stocks_raw` に渡る filter string を strict assertion。既存 technical tests も `technical_analysis_screener` の現行 flat signature / `screen_stocks` delegation に同期し、live API leak を防止。`pytest tests/test_comprehensive_parameters.py -q` は **22 passed / 0 skipped / 0 failed**、default pytest は **246 passed / 94 skipped / 0 failed**。#42 quarantine は **1 marker occurrence / 実効 15 tests** に減少。
- 2026-05-09: Issue #42 final batch として `tests/test_financial_parameters.py` の module-level skip（実効 15 tests）を復帰。P/E・PEG・P/B・Debt/Equity・ROE/ROA・margin・ownership・short/option・target price の各 financial filter coverage を `custom_screener` + `screen_stocks_raw` forwarding の strict assertion に置換し、旧 `earnings_screener` unknown args false-pass を除去。`pytest tests/test_financial_parameters.py -q` は **15 passed / 0 skipped / 0 failed**、default pytest は **261 passed / 79 skipped / 0 failed**。#42 quarantine は **0 marker occurrences / 実効 0 tests** に到達。
