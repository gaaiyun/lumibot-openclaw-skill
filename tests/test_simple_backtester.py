"""simple_backtester 测试。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.simple_backtester import BacktestRun, run
from scripts.strategies import BuyAndHold, Momentum, DualMA
from scripts.strategies._base import Action


def test_buy_and_hold_buys_once_and_holds():
    s = BuyAndHold()
    prices = [100.0] * 50
    # 提供 50 个一样的价格 → 买入后不卖
    result = run(s, prices, initial_cash=10_000.0, warmup=0)
    assert isinstance(result, BacktestRun)
    assert result.n_trades == 1
    # 最终净值应该接近初始（价格没变）
    assert abs(result.final_value - 10_000.0) < 100  # ≤1% 误差（仅 allocation 留 5% 现金）


def test_buy_and_hold_captures_price_appreciation():
    s = BuyAndHold()
    prices = list(range(100, 200))  # 价格翻倍
    result = run(s, prices, initial_cash=10_000.0, warmup=0)
    # 95% 仓位 × 翻倍 + 5% 现金，最终约 ~1.95 × 10_000
    assert result.final_value > 18_000


def test_momentum_makes_multiple_trades_on_oscillating_prices():
    s = Momentum()
    # 涨 30 跌 30 涨 30
    prices = (list(range(100, 130)) + list(range(130, 100, -1))
              + list(range(100, 130)))
    result = run(s, prices, initial_cash=10_000.0,
                 params={"period": 10}, warmup=10)
    assert result.n_trades >= 2  # 至少有一次买 + 一次卖


def test_run_returns_equity_curve_length_matches_prices():
    s = BuyAndHold()
    prices = [100, 101, 102, 103, 104]
    result = run(s, prices, warmup=0)
    assert len(result.equity_curve) == len(prices)
    assert len(result.decisions) == len(prices)


def test_run_decision_actions_during_warmup_are_hold():
    s = Momentum()
    prices = [100] * 30
    result = run(s, prices, warmup=20)
    for i in range(20):
        assert result.decisions[i].action == Action.HOLD


def test_run_handles_empty_prices_gracefully():
    s = BuyAndHold()
    result = run(s, prices=[], initial_cash=5000.0, warmup=0)
    assert result.final_value == 5000.0
    assert result.equity_curve == []
    assert result.n_trades == 0


def test_run_total_return_calculation():
    s = BuyAndHold()
    prices = [100.0] * 5 + [200.0] * 5   # 价格翻倍
    result = run(s, prices, initial_cash=10_000.0, warmup=0)
    # ~ 0.95 * 10_000 → 95 股，再 + 5% 现金留 500
    # final = 500 + 95 × 200 = 19_500 → ret = +95%
    assert 0.85 <= result.total_return <= 1.0


def test_run_with_custom_params_overrides_defaults():
    s = Momentum()
    prices = list(range(100, 200))
    # 用极短 period=5 应该比 period=50 多交易
    result_short = run(s, prices, params={"period": 5},
                       initial_cash=10_000.0, warmup=5)
    result_long = run(s, prices, params={"period": 50},
                      initial_cash=10_000.0, warmup=50)
    # 单调上涨，period=5 触发更快、但都不会卖
    assert result_short.n_trades >= 1
    assert result_long.n_trades >= 1
