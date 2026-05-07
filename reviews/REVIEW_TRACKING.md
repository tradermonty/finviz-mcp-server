# Review Findings Tracking

レビュー指摘事項の対応状況を記録するトラッキング表。

## Status Legend

- 🔴 Open: 未着手
- 🟡 In Progress: Issue / PR 作成済み、レビュー待ち
- 🟢 Done: マージ済み
- ⚪ Deferred: 別途対応 / スコープ外

## Findings

| # | Source | Priority | Finding | Issue | PR | Status | Notes |
|---|--------|----------|---------|-------|----|----|-------|
| 1 | pr-6-review-2026-05-07.md | Medium | `price_change_min` preset guard が `_safe_numeric_conversion` 後の値を見ており機能しない | (PR #6 内対応) | [#6](https://github.com/tradermonty/finviz-mcp-server/pull/6) | 🟢 Done | コミット 3c19d95 で修正、main にマージ済み (9a18400)。重複ハンドラ削除 + 上流ブロックに一元化。回帰テスト5件追加。 |
| 2 | code-review-2026-05-07.md | High | `pyproject.toml` に `mcp` / `sec-edgar-api` が未登録。クリーン環境で import 失敗 | [#7](https://github.com/tradermonty/finviz-mcp-server/issues/7) | [#8](https://github.com/tradermonty/finviz-mcp-server/pull/8) | 🟡 In Progress | `mcp>=1.9.1`, `sec-edgar-api>=0.3.0` を `pyproject.toml` に追加。`requirements.txt` に `beautifulsoup4>=4.12.0` を追加。 |
| 3 | code-review-2026-05-07.md | Medium | `run_tests.py` がサブプロセスで `python` / `pip` を直接呼び出すため、別 interpreter / 不在環境で失敗 | [#9](https://github.com/tradermonty/finviz-mcp-server/issues/9) | [#10](https://github.com/tradermonty/finviz-mcp-server/pull/10) | 🟡 In Progress | `sys.executable -m pytest` / `sys.executable -m pip` への統一。 |
| 4 | code-review-2026-05-07.md | Medium | `get_relative_volume_stocks` の inline conditional で `0` 値が `N/A` になる + 表示崩れ | [#11](https://github.com/tradermonty/finviz-mcp-server/issues/11) | [#12](https://github.com/tradermonty/finviz-mcp-server/pull/12) | 🟡 In Progress | 先に str を組み立てる実装へ変更。`is not None` 判定。回帰テスト追加。 |
| 5 | code-review-2026-05-07.md | Low | pytest 9 で `tests/test_basic.py` の test 関数が値を返しており `PytestReturnNotNoneWarning` | [#13](https://github.com/tradermonty/finviz-mcp-server/issues/13) | [#14](https://github.com/tradermonty/finviz-mcp-server/pull/14) | 🟡 In Progress | `assert` のみで検証する形へ修正。`main()` も例外なしを passed として扱う。 |

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

## Update History

- 2026-05-07: 初版作成。PR #6 のレビュー指摘1件は対応済み。
- 2026-05-07: code-review-2026-05-07.md の High 1件・Medium 2件・Low 1件について Issue (#7, #9, #11, #13) と PR (#8, #10, #12, #14) を作成。
