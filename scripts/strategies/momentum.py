"""动量策略：当前价 > N 日均价 → 持仓；否则空仓。

经典趋势跟踪。N=20 是常见默认值（约一个月日线）。
"""
from __future__ import annotations

from statistics import mean

from ._base import Decision, StrategyBase, _try_import_lumibot_strategy

_LumiStrategy = _try_import_lumibot_strategy()


class _MomentumLogic(StrategyBase):
    DEFAULT_PARAMETERS = {
        "symbol": "AAPL",
        "period": 20,
        "allocation": 0.95,
    }

    def decide(self, prices, position, params: dict) -> Decision:
        period = params["period"]
        if prices is None or len(prices) < period:
            return Decision.hold(f"价格序列长度 {len(prices) if prices else 0} < {period}")
        recent = list(prices[-period:])
        current = recent[-1]
        avg = mean(recent)
        has_position = position is not None and getattr(position, "quantity", 0) > 0

        if current > avg and not has_position:
            return Decision.buy(f"current {current:.2f} > MA{period} {avg:.2f}")
        if current <= avg and has_position:
            return Decision.sell(f"current {current:.2f} ≤ MA{period} {avg:.2f}")
        return Decision.hold("无信号")


if _LumiStrategy is not None:
    class Momentum(_LumiStrategy, _MomentumLogic):
        parameters = _MomentumLogic.DEFAULT_PARAMETERS

        def initialize(self):
            self.sleeptime = "1D"

        def on_trading_iteration(self):
            params = self.merged_parameters(self.parameters)
            symbol = params["symbol"]
            hist = self.get_historical_prices(symbol, params["period"], "day")
            if hist is None or hist.df is None or len(hist.df) < params["period"]:
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
    Momentum = _MomentumLogic  # type: ignore
