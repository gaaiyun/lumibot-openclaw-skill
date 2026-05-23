"""可插拔的 Lumibot 策略库。

每个策略文件导出一个 ``IStrategy`` 子类（``Strategy``），
通过 ``STRATEGIES`` 注册表暴露给 CLI / compare 命令。

设计原则：
- 单文件即一个策略，类名即策略名
- 必须有 ``initialize()`` 和 ``on_trading_iteration()``
- 参数从 ``self.parameters`` 取，全部带 sensible default
- 没有不可剔除的硬编码 ticker
"""
from .buy_and_hold import BuyAndHold
from .momentum import Momentum
from .dual_ma import DualMA
from .mean_reversion import MeanReversion
from .rsi_reversal import RSIReversal


STRATEGIES = {
    "buy_and_hold": BuyAndHold,
    "momentum": Momentum,
    "dual_ma": DualMA,
    "mean_reversion": MeanReversion,
    "rsi_reversal": RSIReversal,
}


__all__ = [
    "STRATEGIES",
    "BuyAndHold",
    "Momentum",
    "DualMA",
    "MeanReversion",
    "RSIReversal",
]
