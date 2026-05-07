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
| 2 | code-review-2026-05-07.md | High | `pyproject.toml` に `mcp` / `sec-edgar-api` が未登録。クリーン環境で import 失敗 | [#7](https://github.com/tradermonty/finviz-mcp-server/issues/7) | [#8](https://github.com/tradermonty/finviz-mcp-server/pull/8) | 🔵 Approved | repository-prs-review-2026-05-07.md で Approve / mergeable。 |
| 3 | code-review-2026-05-07.md | Medium | `run_tests.py` がサブプロセスで `python` / `pip` を直接呼び出すため、別 interpreter / 不在環境で失敗 | [#9](https://github.com/tradermonty/finviz-mcp-server/issues/9) | [#10](https://github.com/tradermonty/finviz-mcp-server/pull/10) | 🔵 Approved | repository-prs-review-2026-05-07.md で Approve / mergeable。 |
| 4 | code-review-2026-05-07.md | Medium | `get_relative_volume_stocks` の inline conditional で `0` 値が `N/A` になる + 表示崩れ | [#11](https://github.com/tradermonty/finviz-mcp-server/issues/11) | [#12](https://github.com/tradermonty/finviz-mcp-server/pull/12) | 🔵 Approved | repository-prs-review-2026-05-07.md で Approve / mergeable。フォローアップで `volume=0` の明示的 assertion を 03b8183 で追加。 |
| 5 | code-review-2026-05-07.md | Low | pytest 9 で `tests/test_basic.py` の test 関数が値を返しており `PytestReturnNotNoneWarning` | [#13](https://github.com/tradermonty/finviz-mcp-server/issues/13) | [#14](https://github.com/tradermonty/finviz-mcp-server/pull/14) | 🔵 Approved | repository-prs-review-2026-05-07.md で Approve / mergeable。 |
| 6 | repository-prs-review-2026-05-07.md | **P1** | PR #3: HTTP transport で DNS rebinding 保護がデフォルト無効化、`MCP_HOST=0.0.0.0` 公開でセキュリティ後退 | (PR #3 author 対応待ち) | [#3](https://github.com/tradermonty/finviz-mcp-server/pull/3) | ⛔ Blocked | **Security regression**。`src/server.py:2080-2107`, `Dockerfile:25`。DNS rebinding protection をデフォルト enabled に。 |
| 7 | repository-prs-review-2026-05-07.md | **P1** | PR #3: 実行可能 Python ファイル先頭に UTF-8 BOM (`ef bb bf`) が混入、shebang 無効化 | (PR #3 author 対応待ち) | [#3](https://github.com/tradermonty/finviz-mcp-server/pull/3) | ⛔ Blocked | `run_server.py:1`, `run_release_tests.py:1`, `src/server.py:1` 他。pre-commit に encoding チェック追加推奨。 |
| 8 | repository-prs-review-2026-05-07.md | P2 | PR #3: タイトルと無関係なテキスト churn (`Unit testsrun`, `Environment checkrunning...`, `detectstocks` 等) でレポート出力が破損 | (PR #3 author 対応待ち) | [#3](https://github.com/tradermonty/finviz-mcp-server/pull/3) | ⛔ Blocked | PR を transport / security 専用に分割推奨。無関係な書き換えを revert。 |

## Remaining Risks (Deferred)

| # | Risk | Status | Notes |
|---|------|--------|-------|
| R1 | `tests/test_mcp_integration.py` が現行の `mcp` API とずれており複数失敗 | ⚪ Deferred | `FastMCP.list_tools()` の同期/非同期扱いが異なる。別途 issue 化を検討。 |
| R2 | ネットワーク / API キー前提テストが unit テストと混在 | ⚪ Deferred | `integration` / `requires_network` / `requires_finviz_api_key` の marker 分離が必要。レビュアーが `tests/conftest.py` で auto-mark/auto-skip の試作を提供済み。 |
| R3 | `src/server.py` が肥大（MCPツール層・validation・formatting・client が密結合） | ⚪ Deferred | ツール毎の formatter / validation の分割をリファクタリング issue として整理。 |

## Quality Infrastructure (Deferred)

レビュアーがローカルに追加した以下のファイルは品質基盤として別 PR で取り込み予定（本トラッキングのスコープ外）:

- `.flake8` — Linter 設定
- `.github/workflows/ci.yml` — GitHub Actions CI
- `.pre-commit-config.yaml` — pre-commit hooks
- `tests/conftest.py` — テスト共通 fixture (e2e auto-marker / auto-skip)
- `tests/test_e2e_screener_invariants.py` — E2E スクリーナー不変式テスト
- `scripts/run_e2e_invariants.py` — E2E 実行スクリプト
- `tests/E2E_TESTING.md` — E2E テスト手順書

## Recommended Merge Order (per repository-prs-review-2026-05-07.md)

1. **#8** (runtime dependency packaging) — まず最初にマージ
2. **#10**, **#14** (test tooling hygiene) — 並列マージ可
3. **#12** (user-facing formatter bug fix)
4. **#15** (tracking metadata) — チームが tracker 採用に合意した後
5. **#3** は現状でマージしない。Request changes で分割を依頼

## Update History

- 2026-05-07: 初版作成。PR #6 のレビュー指摘1件は対応済み。
- 2026-05-07: code-review-2026-05-07.md の High 1件・Medium 2件・Low 1件について Issue (#7, #9, #11, #13) と PR (#8, #10, #12, #14) を作成。
- 2026-05-07: repository-prs-review-2026-05-07.md の結果を反映。PR #8/#10/#12/#14/#15 が Approved 判定。PR #12 にはフォローアップ assertion を追加 (03b8183)。PR #3 に P1×2 / P2×1 の blocker 判定（コメント投稿はユーザー判断で見送り、ローカル tracker のみに記録）。
