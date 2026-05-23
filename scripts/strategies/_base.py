"""所有策略共享的工具与基类适配。

Lumibot 的 ``Strategy`` 是运行时依赖；为了让纯策略逻辑能在没装 lumibot
的 CI 环境跑测试，这里给一个"逻辑层"基类，把决策逻辑和 lumibot 的
broker 交互层解耦：

- ``decide(...)`` 接收数据（价格序列、当前仓位）返回 ``Decision``
- 真正的 ``on_trading_iteration`` 从 lumibot 拉数据然后调 ``decide``

这样 ``decide`` 是纯函数，可以无 lumibot 跑单测。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Action(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(frozen=True)
class Decision:
    action: Action
    reason: str = ""

    @classmethod
    def buy(cls, reason: str = "") -> "Decision":
        return cls(Action.BUY, reason)

    @classmethod
    def sell(cls, reason: str = "") -> "Decision":
        return cls(Action.SELL, reason)

    @classmethod
    def hold(cls, reason: str = "") -> "Decision":
        return cls(Action.HOLD, reason)


def _try_import_lumibot_strategy():
    """运行时去 import lumibot；CI / 测试场景下 lumibot 不存在就返回 None。"""
    try:
        from lumibot.strategies import Strategy  # type: ignore
        return Strategy
    except ImportError:
        return None


class StrategyBase:
    """所有策略继承这个，按需在子类里 mixin Lumibot Strategy。

    决策逻辑：``decide(prices, position) -> Decision`` 是纯函数，能直接单测。
    """

    DEFAULT_PARAMETERS: dict = {}

    @classmethod
    def merged_parameters(cls, overrides: Optional[dict] = None) -> dict:
        merged = dict(cls.DEFAULT_PARAMETERS)
        if overrides:
            merged.update({k: v for k, v in overrides.items() if v is not None})
        return merged

    def decide(self, prices, position, params: dict) -> Decision:  # pragma: no cover
        raise NotImplementedError
