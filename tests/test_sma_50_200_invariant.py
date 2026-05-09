"""
Regression test for the ``sma_50_above_sma_200()`` invariant's
``field_getter`` semantics (re-review of PR #23).

The invariant documents that Finviz may omit either of ``sma_50`` /
``sma_200`` on individual rows and is therefore declared
``optional=True``. The framework decides whether an optional invariant
counts as "verified" for a stock by calling ``field_getter(stock)`` and
applying ``_is_missing`` to the return value.

Bug pinned by this test: a previous version of ``field_getter`` returned
only ``s.sma_50``. If a row had ``sma_50`` populated but ``sma_200=None``,
the framework saw the value as present, counted the row as verified,
then ``check()`` failed because it dereferenced ``s.sma_200``. That
contradicted the helper's own contract that "either SMA may be omitted".

The fix returns ``None`` from ``field_getter`` whenever EITHER SMA is
missing, so the row is treated as "field missing" and tolerated under
``optional=True``.
"""

import pytest

from src.models import StockData
from tests.test_e2e_screener_invariants import (
    Invariant,
    assert_invariants,
    sma_50_above_sma_200,
)


def _stock(ticker: str, sma_50, sma_200) -> StockData:
    return StockData(
        ticker=ticker,
        company_name=ticker,
        sector="Sector",
        industry="Industry",
        country="USA",
        market_cap=12_000.0,  # in millions, well above any threshold
        price=150.0,
        sma_50=sma_50,
        sma_200=sma_200,
    )


class TestSma50Above200FieldGetter:
    def test_pair_returns_none_when_either_missing(self):
        inv: Invariant = sma_50_above_sma_200()
        # Both present -> framework gets a non-None pair
        assert inv.field_getter(_stock("BOTH", 100.0, 80.0)) is not None
        # sma_50 only -> getter returns None (treated as missing)
        assert inv.field_getter(_stock("ONLY50", 100.0, None)) is None
        # sma_200 only -> getter returns None
        assert inv.field_getter(_stock("ONLY200", None, 80.0)) is None
        # Both missing -> getter returns None
        assert inv.field_getter(_stock("NEITHER", None, None)) is None

    def test_partial_row_does_not_fail_optional_invariant(self):
        """
        One row has sma_50 only; another row has both SMAs and satisfies
        the check. Per the optional-invariant contract, the partial row
        must be tolerated and the test must pass.
        """
        results = [
            _stock("PARTIAL", 100.0, None),  # tolerated by optional
            _stock("OK", 110.0, 80.0),  # verified, sma_50 > sma_200
        ]
        # Should not raise / fail — at least one row was verified.
        assert_invariants(
            "test_screener",
            results,
            invariants=[sma_50_above_sma_200()],
        )

    def test_all_rows_missing_one_side_fails_unverifiable(self):
        """
        If every result is missing at least one of the two SMAs, no row
        is counted as verified, so the optional invariant becomes
        UNVERIFIABLE and the test must fail. (Otherwise the framework
        silently passes a documented filter we never actually checked.)
        """
        results = [
            _stock("A", 100.0, None),
            _stock("B", None, 80.0),
            _stock("C", None, None),
        ]
        with pytest.raises(BaseException) as excinfo:
            assert_invariants(
                "test_screener",
                results,
                invariants=[sma_50_above_sma_200()],
            )
        # The point of this test is to distinguish "no data was checkable"
        # (UNVERIFIABLE) from "data was checked and found to violate the
        # rule" (a regular VIOLATION). Asserting only on the invariant
        # name would erase that distinction.
        assert "UNVERIFIABLE" in str(excinfo.value)

    def test_violation_when_check_actually_fails(self):
        """
        With both SMAs present but sma_50 <= sma_200, the row is verified
        and the check legitimately fails — the framework should report
        this as a violation, not silently pass.
        """
        results = [
            _stock("BAD", 50.0, 80.0),  # sma_50 < sma_200 -> check returns False
        ]
        with pytest.raises(BaseException):
            assert_invariants(
                "test_screener",
                results,
                invariants=[sma_50_above_sma_200()],
            )
