"""双均线交叉策略（Golden / Death Cross）。

短期 MA 上穿长期 MA → 买入；下穿 → 卖出。
默认 fast=10, slow=30 是日线常见组合。
"""
from __future__ import annotations

from statistics import mean

from ._base import Decision, StrategyBase, _try_import_lumibot_strategy

_LumiStrategy = _try_import_lumibot_strategy()


class _DualMALogic(StrategyBase):
    DEFAULT_PARAMETERS = {
        "symbol": "AAPL",
        "fast_period": 10,
        "slow_period": 30,
        "allocation": 0.95,
    }

    def decide(self, prices, position, params: dict) -> Decision:
        fast = params["fast_period"]
        slow = params["slow_period"]
        if fast >= slow:
            raise ValueError(f"fast_period ({fast}) 必须 < slow_period ({slow})")
        if prices is None or len(prices) < slow:
            return Decision.hold(f"价格长度 {len(prices) if prices else 0} < slow {slow}")

        fast_ma = mean(prices[-fast:])
        slow_ma = mean(prices[-slow:])
        has_position = position is not None and getattr(position, "quantity", 0) > 0

        if fast_ma > slow_ma and not has_position:
            return Decision.buy(f"MA{fast}={fast_ma:.2f} > MA{slow}={slow_ma:.2f}")
        if fast_ma < slow_ma and has_position:
            return Decision.sell(f"MA{fast}={fast_ma:.2f} < MA{slow}={slow_ma:.2f}")
        return Decision.hold("无交叉")


if _LumiStrategy is not None:
    class DualMA(_LumiStrategy, _DualMALogic):
        parameters = _DualMALogic.DEFAULT_PARAMETERS

        def initialize(self):
            self.sleeptime = "1D"

        def on_trading_iteration(self):
            params = self.merged_parameters(self.parameters)
            symbol = params["symbol"]
            hist = self.get_historical_prices(symbol, params["slow_period"], "day")
            if hist is None or hist.df is None or len(hist.df) < params["slow_period"]:
                return
            prices = hist.df["close"].tolist()
            position = self.get_position(symbol)
            decision = self.decide(prices=prices, position=position, params=params)
            current_price = prices[-1]
            if decision.action.value == "buy":
                qty = int(self.portfolio_value * params["allocation"] / current_price)
                if qty > 0:
                    self.create_order(symbol, qty, "buy")
            elif decision.action.value == "sell":
                self.sell_all(symbol)
else:
    DualMA = _DualMALogic  # type: ignore
