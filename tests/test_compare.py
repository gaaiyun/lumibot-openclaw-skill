"""compare.py 测试。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.compare import (
    CompareRow,
    _daily_returns,
    _max_drawdown,
    compare_strategies,
    render_table,
    summarize,
)
from scripts.simple_backtester import BacktestRun, run
from scripts.strategies import STRATEGIES, BuyAndHold


# --- helpers ------------------------------------------------------------------

def test_daily_returns_basic():
    rets = _daily_returns([100, 110, 121])
    assert len(rets) == 2
    assert abs(rets[0] - 0.10) < 1e-9
    assert abs(rets[1] - 0.10) < 1e-9


def test_daily_returns_empty_or_short():
    assert _daily_returns([]) == []
    assert _daily_returns([100]) == []


def test_daily_returns_handles_zero_division():
    """前一天净值为 0 时不应崩。"""
    rets = _daily_returns([100, 0, 50])
    assert len(rets) == 2
    assert rets[1] == 0.0


def test_max_drawdown_monotone_up_is_zero():
    assert _max_drawdown([1, 2, 3, 4, 5]) == 0.0


def test_max_drawdown_simple_dip():
    # 1 → 2 → 1 → 1.5：peak=2, trough=1, dd = (1-2)/2 = -0.5
    assert abs(_max_drawdown([1, 2, 1, 1.5]) - (-0.5)) < 1e-9


def test_max_drawdown_empty():
    assert _max_drawdown([]) == 0.0


# --- summarize ---------------------------------------------------------------

def test_summarize_buy_and_hold_on_uptrend():
    s = BuyAndHold()
    prices = list(range(100, 200))
    result = run(s, prices, initial_cash=10_000.0, warmup=0)
    row = summarize(result)
    assert isinstance(row, CompareRow)
    assert row.total_return > 0
    assert row.n_trades == 1


def test_summarize_with_empty_run():
    empty_run = BacktestRun(
        strategy_name="empty", equity_curve=[],
        decisions=[], initial_cash=1000, final_value=1000, n_trades=0,
    )
    row = summarize(empty_run)
    assert row.total_return == 0
    assert row.sharpe == 0


def test_summarize_to_dict_is_json_serializable():
    import json
    s = BuyAndHold()
    prices = list(range(100, 150))
    result = run(s, prices, warmup=0)
    row = summarize(result)
    d = row.to_dict()
    s_json = json.dumps(d)
    assert "buy_and_hold" in s_json.lower() or "BuyAndHold" in s_json


# --- compare_strategies ------------------------------------------------------

def test_compare_strategies_returns_one_row_per_strategy():
    instances = {name: cls() for name, cls in STRATEGIES.items()}
    prices = [100 + (i % 10) - 5 for i in range(100)]  # 震荡
    rows = compare_strategies(instances, prices, initial_cash=10_000.0)
    assert len(rows) == len(STRATEGIES)
    assert {r.strategy_name for r in rows} == set(STRATEGIES.keys())


def test_compare_strategies_each_row_has_valid_metrics():
    instances = {"bh": BuyAndHold()}
    prices = list(range(100, 200))
    rows = compare_strategies(instances, prices)
    r = rows[0]
    assert r.strategy_name == "bh"
    assert r.total_return >= 0   # 持有单调上升
    assert r.n_trades == 1


# --- render_table ------------------------------------------------------------

def test_render_table_includes_strategy_names():
    instances = {name: cls() for name, cls in STRATEGIES.items()}
    prices = list(range(100, 200))
    rows = compare_strategies(instances, prices)
    out = render_table(rows)
    for name in STRATEGIES.keys():
        assert name in out
    # Header & separator
    assert "Strategy" in out
    assert "Sharpe" in out


def test_render_table_has_separator_line():
    instances = {"bh": BuyAndHold()}
    prices = list(range(100, 200))
    rows = compare_strategies(instances, prices)
    out = render_table(rows)
    lines = out.split("\n")
    assert lines[1].startswith("-")
