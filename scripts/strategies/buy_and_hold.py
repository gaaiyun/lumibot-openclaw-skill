"""买入持有：第一次迭代 all-in，之后什么也不做。

最简单的基准，几乎所有别的策略都应该至少打过它。
"""
from __future__ import annotations

from ._base import Decision, StrategyBase, _try_import_lumibot_strategy

_LumiStrategy = _try_import_lumibot_strategy()


class _BuyAndHoldLogic(StrategyBase):
    DEFAULT_PARAMETERS = {
        "symbol": "AAPL",
        "allocation": 0.95,   # 用 95% 仓位买入
    }

    def decide(self, prices, position, params: dict) -> Decision:
        # 已有仓位 → 持有
        if position is not None and getattr(position, "quantity", 0) > 0:
            return Decision.hold("已建仓")
        if prices is None or len(prices) == 0:
            return Decision.hold("无价格数据")
        return Decision.buy(f"首次建仓 {params['symbol']}")


if _LumiStrategy is not None:
    class BuyAndHold(_LumiStrategy, _BuyAndHoldLogic):
        """Lumibot 兼容的买入持有策略。"""
        parameters = _BuyAndHoldLogic.DEFAULT_PARAMETERS

        def initialize(self):
            self.sleeptime = "1D"

        def on_trading_iteration(self):
            params = self.merged_parameters(self.parameters)
            symbol = params["symbol"]
            price = self.get_last_price(symbol)
            position = self.get_position(symbol)
            decision = self.decide(prices=[price] if price else [],
                                   position=position, params=params)
            if decision.action.value == "buy" and price and self.portfolio_value > 0:
                qty = int(self.portfolio_value * params["allocation"] / price)
                if qty > 0:
                    order = self.create_order(symbol, qty, "buy")
                    self.submit_order(order)
else:
    # lumibot 没装：仅暴露逻辑类（够测试用）
    BuyAndHold = _BuyAndHoldLogic  # type: ignore
