"""均值回归：价格偏离 N 日均线 z-score > 阈值 时反向操作。

价格 z-score = (price - MA) / sigma：
- z < -threshold → 价格偏低，买入（赌它回归）
- z > +threshold → 价格偏高，卖出
- 中间区间 → 持有
"""
from __future__ import annotations

from statistics import mean, pstdev

from ._base import Decision, StrategyBase, _try_import_lumibot_strategy

_LumiStrategy = _try_import_lumibot_strategy()


class _MeanReversionLogic(StrategyBase):
    DEFAULT_PARAMETERS = {
        "symbol": "AAPL",
        "period": 20,
        "z_threshold": 1.5,
        "allocation": 0.95,
    }

    def decide(self, prices, position, params: dict) -> Decision:
        period = params["period"]
        threshold = params["z_threshold"]
        if prices is None or len(prices) < period:
            return Decision.hold(f"价格长度 {len(prices) if prices else 0} < {period}")

        window = list(prices[-period:])
        ma = mean(window)
        sd = pstdev(window) if len(window) > 1 else 0
        if sd <= 1e-9:
            return Decision.hold("波动率太低")

        current = window[-1]
        z = (current - ma) / sd
        has_position = position is not None and getattr(position, "quantity", 0) > 0

        if z < -threshold and not has_position:
            return Decision.buy(f"z={z:.2f} < -{threshold}（偏低，赌回归）")
        if z > threshold and has_position:
            return Decision.sell(f"z={z:.2f} > +{threshold}（已回升，止盈）")
        return Decision.hold(f"z={z:.2f}（区间内）")


if _LumiStrategy is not None:
    class MeanReversion(_LumiStrategy, _MeanReversionLogic):
        parameters = _MeanReversionLogic.DEFAULT_PARAMETERS

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
    MeanReversion = _MeanReversionLogic  # type: ignore
