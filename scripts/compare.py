"""多策略同价格序列对比报告。

对一组策略 + 同一份价格数据跑离线回测（``simple_backtester.run``），
按累计收益 / 最大回撤 / Sharpe 出表。

注：这里 Sharpe 用日收益简单年化（× √252），不考虑无风险利率。
回测口径与 lumibot 真回测会有差异（不模拟成交滑点、佣金、盘前盘后），
适合"哪种策略在这只票上更靠谱"的粗粒度比较。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from .simple_backtester import BacktestRun, run
from .strategies._base import StrategyBase


@dataclass
class CompareRow:
    strategy_name: str
    total_return: float
    annualized_return: float
    annualized_vol: float
    sharpe: float
    max_drawdown: float
    n_trades: int

    def to_dict(self) -> dict:
        return {
            "strategy_name": self.strategy_name,
            "total_return": float(self.total_return),
            "annualized_return": float(self.annualized_return),
            "annualized_vol": float(self.annualized_vol),
            "sharpe": float(self.sharpe),
            "max_drawdown": float(self.max_drawdown),
            "n_trades": int(self.n_trades),
        }


def _daily_returns(equity_curve: Sequence[float]) -> List[float]:
    out = []
    for i in range(1, len(equity_curve)):
        prev = equity_curve[i - 1]
        if prev <= 0:
            out.append(0.0)
        else:
            out.append(equity_curve[i] / prev - 1)
    return out


def _max_drawdown(equity_curve: Sequence[float]) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for v in equity_curve:
        if v > peak:
            peak = v
        if peak > 0:
            dd = v / peak - 1
            if dd < max_dd:
                max_dd = dd
    return max_dd


def summarize(run_result: BacktestRun, periods_per_year: int = 252) -> CompareRow:
    rets = _daily_returns(run_result.equity_curve)
    if not rets:
        return CompareRow(run_result.strategy_name, 0, 0, 0, 0, 0, run_result.n_trades)

    mean_r = sum(rets) / len(rets)
    var = sum((r - mean_r) ** 2 for r in rets) / max(len(rets) - 1, 1)
    std = math.sqrt(var)
    ann_ret = (1 + mean_r) ** periods_per_year - 1
    ann_vol = std * math.sqrt(periods_per_year)
    sharpe = (mean_r / std * math.sqrt(periods_per_year)) if std > 1e-12 else 0.0
    mdd = _max_drawdown(run_result.equity_curve)
    return CompareRow(
        strategy_name=run_result.strategy_name,
        total_return=run_result.total_return,
        annualized_return=ann_ret,
        annualized_vol=ann_vol,
        sharpe=sharpe,
        max_drawdown=mdd,
        n_trades=run_result.n_trades,
    )


def compare_strategies(
    strategies: Dict[str, StrategyBase],
    prices: Sequence[float],
    params: Optional[Dict[str, dict]] = None,
    initial_cash: float = 100_000.0,
) -> List[CompareRow]:
    """对一组 {name: strategy_instance} 同价格跑回测，返回 CompareRow 列表。"""
    params = params or {}
    rows = []
    for name, strat in strategies.items():
        result = run(strat, prices, params=params.get(name),
                     initial_cash=initial_cash)
        result.strategy_name = name
        rows.append(summarize(result))
    return rows


def render_table(rows: List[CompareRow]) -> str:
    headers = ["Strategy", "TotalRet", "AnnRet", "AnnVol", "Sharpe", "MaxDD", "Trades"]
    table = [headers]
    for r in rows:
        table.append([
            r.strategy_name,
            f"{r.total_return:.2%}",
            f"{r.annualized_return:.2%}",
            f"{r.annualized_vol:.2%}",
            f"{r.sharpe:.2f}",
            f"{r.max_drawdown:.2%}",
            str(r.n_trades),
        ])
    widths = [max(len(row[c]) for row in table) for c in range(len(headers))]
    out = []
    for i, row in enumerate(table):
        out.append("  ".join(cell.ljust(widths[j]) for j, cell in enumerate(row)))
        if i == 0:
            out.append("-" * len(out[-1]))
    return "\n".join(out)
