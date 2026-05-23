"""每个策略的 decide() 纯函数测试。

decide() 是 lumibot 之外的纯逻辑，可以直接喂价格序列断言决策。
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.strategies import (
    BuyAndHold,
    DualMA,
    MeanReversion,
    Momentum,
    RSIReversal,
    STRATEGIES,
)
from scripts.strategies._base import Action


@dataclass
class FakePosition:
    quantity: float


# --- BuyAndHold ---------------------------------------------------------------

def test_buy_and_hold_buys_when_no_position():
    s = BuyAndHold()
    d = s.decide(prices=[100.0], position=None, params=s.DEFAULT_PARAMETERS)
    assert d.action == Action.BUY


def test_buy_and_hold_holds_when_has_position():
    s = BuyAndHold()
    pos = FakePosition(quantity=10)
    d = s.decide(prices=[100.0], position=pos, params=s.DEFAULT_PARAMETERS)
    assert d.action == Action.HOLD


def test_buy_and_hold_holds_when_no_prices():
    s = BuyAndHold()
    d = s.decide(prices=[], position=None, params=s.DEFAULT_PARAMETERS)
    assert d.action == Action.HOLD


# --- Momentum -----------------------------------------------------------------

def test_momentum_buys_when_price_above_ma():
    s = Momentum()
    # 后 5 个明显高于前 15 个，最后一根远高于均值
    prices = [100] * 15 + [110, 115, 120, 125, 130]
    d = s.decide(prices=prices, position=None,
                 params={**s.DEFAULT_PARAMETERS, "period": 20})
    assert d.action == Action.BUY


def test_momentum_sells_when_price_below_ma_and_has_position():
    s = Momentum()
    prices = [120] * 15 + [110, 100, 90, 85, 80]
    pos = FakePosition(quantity=10)
    d = s.decide(prices=prices, position=pos,
                 params={**s.DEFAULT_PARAMETERS, "period": 20})
    assert d.action == Action.SELL


def test_momentum_holds_when_data_too_short():
    s = Momentum()
    d = s.decide(prices=[100, 101, 102], position=None,
                 params={**s.DEFAULT_PARAMETERS, "period": 20})
    assert d.action == Action.HOLD


def test_momentum_holds_when_already_positioned_and_above():
    s = Momentum()
    prices = [100] * 15 + [110, 115, 120, 125, 130]
    pos = FakePosition(quantity=10)
    d = s.decide(prices=prices, position=pos,
                 params={**s.DEFAULT_PARAMETERS, "period": 20})
    assert d.action == Action.HOLD


# --- DualMA -------------------------------------------------------------------

def test_dual_ma_buys_on_golden_cross():
    s = DualMA()
    # 短期上升 > 长期：构造短期 MA10 > MA30
    prices = [100] * 20 + [110, 115, 120, 125, 130, 135, 140, 145, 150, 155]
    d = s.decide(prices=prices, position=None, params=s.DEFAULT_PARAMETERS)
    assert d.action == Action.BUY


def test_dual_ma_sells_on_death_cross():
    s = DualMA()
    prices = [150] * 20 + [140, 130, 120, 110, 100, 90, 80, 70, 60, 50]
    pos = FakePosition(quantity=10)
    d = s.decide(prices=prices, position=pos, params=s.DEFAULT_PARAMETERS)
    assert d.action == Action.SELL


def test_dual_ma_rejects_invalid_periods():
    s = DualMA()
    with pytest.raises(ValueError, match="fast_period"):
        s.decide(prices=[100] * 50, position=None,
                 params={**s.DEFAULT_PARAMETERS, "fast_period": 30, "slow_period": 10})


def test_dual_ma_holds_when_history_too_short():
    s = DualMA()
    d = s.decide(prices=[100] * 5, position=None, params=s.DEFAULT_PARAMETERS)
    assert d.action == Action.HOLD


# --- MeanReversion ------------------------------------------------------------

def test_mean_reversion_buys_when_z_score_below_negative_threshold():
    s = MeanReversion()
    # 前 19 个稳定在 100，最后一个暴跌到 50 → z 远低于 -1.5
    prices = [100] * 19 + [50]
    d = s.decide(prices=prices, position=None,
                 params={**s.DEFAULT_PARAMETERS, "period": 20, "z_threshold": 1.5})
    assert d.action == Action.BUY


def test_mean_reversion_sells_when_z_score_above_positive_threshold():
    s = MeanReversion()
    prices = [100] * 19 + [200]
    pos = FakePosition(quantity=10)
    d = s.decide(prices=prices, position=pos,
                 params={**s.DEFAULT_PARAMETERS, "period": 20, "z_threshold": 1.5})
    assert d.action == Action.SELL


def test_mean_reversion_holds_in_range():
    s = MeanReversion()
    prices = [100 + i for i in range(20)]  # 缓慢上升
    d = s.decide(prices=prices, position=None,
                 params={**s.DEFAULT_PARAMETERS, "period": 20, "z_threshold": 1.5})
    assert d.action == Action.HOLD


def test_mean_reversion_holds_when_std_zero():
    s = MeanReversion()
    prices = [100] * 20
    d = s.decide(prices=prices, position=None,
                 params={**s.DEFAULT_PARAMETERS, "period": 20})
    assert d.action == Action.HOLD


# --- RSIReversal --------------------------------------------------------------

def test_rsi_reversal_buys_on_oversold():
    s = RSIReversal()
    # 全部下跌 → RSI 趋近 0
    prices = list(range(100, 80, -1))  # 长度 20，单调下降
    d = s.decide(prices=prices, position=None, params=s.DEFAULT_PARAMETERS)
    assert d.action == Action.BUY


def test_rsi_reversal_sells_on_overbought():
    s = RSIReversal()
    prices = list(range(80, 100))  # 长度 20，单调上升
    pos = FakePosition(quantity=10)
    d = s.decide(prices=prices, position=pos, params=s.DEFAULT_PARAMETERS)
    assert d.action == Action.SELL


def test_rsi_reversal_holds_when_history_too_short():
    s = RSIReversal()
    d = s.decide(prices=[100, 101], position=None, params=s.DEFAULT_PARAMETERS)
    assert d.action == Action.HOLD


# --- registry -----------------------------------------------------------------

def test_strategies_registry_has_all_five():
    expected = {"buy_and_hold", "momentum", "dual_ma", "mean_reversion", "rsi_reversal"}
    assert set(STRATEGIES.keys()) == expected


def test_all_strategies_have_default_parameters():
    for name, cls in STRATEGIES.items():
        assert hasattr(cls, "DEFAULT_PARAMETERS"), f"{name} 缺 DEFAULT_PARAMETERS"
        assert isinstance(cls.DEFAULT_PARAMETERS, dict)
        assert "symbol" in cls.DEFAULT_PARAMETERS, f"{name} 默认参数缺 symbol"


def test_merged_parameters_overrides_defaults():
    s = Momentum()
    merged = s.merged_parameters({"period": 50})
    assert merged["period"] == 50
    assert merged["symbol"] == "AAPL"  # 默认保留


def test_merged_parameters_ignores_none_values():
    s = Momentum()
    merged = s.merged_parameters({"period": None, "symbol": "MSFT"})
    # None 应被忽略，保留默认
    assert merged["period"] == 20
    assert merged["symbol"] == "MSFT"
