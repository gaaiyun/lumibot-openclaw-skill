"""极简事件驱动回测：对接每个策略的 ``decide()`` 纯函数。

为什么不直接用 lumibot 的 YahooDataBacktesting？
- lumibot 跑一次回测要起内置事件循环 + 拉 yfinance + 数据缓存到 ~/Caches，
  慢、依赖重、不可在 CI 跑。
- 这里只测策略**逻辑**：给定一个价格序列，策略一天天看 lookback 窗口，
  做出 buy/sell/hold 决策，记录组合净值。

实盘和 lumibot 真回测仍走 ``__main__.py backtest`` 那条路径，这里是离线
"快速 sanity check + 多策略对比" 用。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from .strategies._base import Action, Decision, StrategyBase


@dataclass
class _Position:
    """Lumibot 那边的 Position 我们只用到 quantity 属性。"""
    quantity: float = 0.0


@dataclass
class BacktestRun:
    strategy_name: str
    equity_curve: List[float]      # 每个 step 的组合净值
    decisions: List[Decision]      # 每天的决策（长度 = step 数）
    initial_cash: float
    final_value: float
    n_trades: int

    @property
    def total_return(self) -> float:
        if self.initial_cash <= 0:
            return 0.0
        return self.final_value / self.initial_cash - 1


def run(strategy: StrategyBase, prices: Sequence[float],
        params: Optional[dict] = None,
        initial_cash: float = 100_000.0,
        allocation: float = 0.95,
        warmup: Optional[int] = None) -> BacktestRun:
    """对单个策略 + 一条价格序列跑回测。

    Parameters
    ----------
    strategy : StrategyBase 实例（不是类）
    prices : 价格序列，逐 step 喂入
    params : 覆盖策略默认参数；None 用默认
    initial_cash : 初始资金
    allocation : 单次建仓使用资金比例
    warmup : 前 warmup 步只看不交易（避免指标没算出来就乱动）；
             None 时自动取策略默认 period
    """
    params = strategy.merged_parameters(params or {})
    if warmup is None:
        warmup = params.get("slow_period", params.get("period", 20))

    cash = initial_cash
    qty = 0.0
    position = _Position(quantity=0)
    equity_curve = []
    decisions = []
    n_trades = 0

    for i in range(len(prices)):
        window = list(prices[: i + 1])
        current = window[-1]
        if i < warmup:
            equity_curve.append(cash + qty * current)
            decisions.append(Decision(Action.HOLD, "warmup"))
            continue

        position.quantity = qty
        decision = strategy.decide(prices=window, position=position, params=params)
        decisions.append(decision)

        if decision.action == Action.BUY and qty == 0:
            buy_cash = cash * allocation
            new_qty = buy_cash / current
            qty = new_qty
            cash -= new_qty * current
            n_trades += 1
        elif decision.action == Action.SELL and qty > 0:
            cash += qty * current
            qty = 0
            n_trades += 1

        equity_curve.append(cash + qty * current)

    final_value = cash + qty * prices[-1] if len(prices) else initial_cash
    return BacktestRun(
        strategy_name=type(strategy).__name__,
        equity_curve=equity_curve,
        decisions=decisions,
        initial_cash=initial_cash,
        final_value=final_value,
        n_trades=n_trades,
    )
