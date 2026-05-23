"""RSI 反转策略：RSI < 30 买入超卖，RSI > 70 卖出超买。

经典 14 期 RSI，用 Wilder smoothing 简化为 SMA 版（避免依赖 talib）。
"""
from __future__ import annotations

from ._base import Decision, StrategyBase, _try_import_lumibot_strategy

_LumiStrategy = _try_import_lumibot_strategy()


def _rsi_sma(prices, period: int = 14) -> float:
    """SMA 版 RSI（不是 Wilder，但够指标化判断）。"""
    if len(prices) < period + 1:
        return 50.0  # 数据不够时给中性
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    recent = deltas[-period:]
    gains = [d for d in recent if d > 0]
    losses = [-d for d in recent if d < 0]
    avg_gain = sum(gains) / period if gains else 0.0
    avg_loss = sum(losses) / period if losses else 0.0
    if avg_loss <= 1e-12:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


class _RSIReversalLogic(StrategyBase):
    DEFAULT_PARAMETERS = {
        "symbol": "AAPL",
        "period": 14,
        "oversold": 30,
        "overbought": 70,
        "allocation": 0.95,
    }

    def decide(self, prices, position, params: dict) -> Decision:
        period = params["period"]
        oversold = params["oversold"]
        overbought = params["overbought"]
        if prices is None or len(prices) < period + 1:
            return Decision.hold(f"价格长度不足，需要 {period + 1} 个点")
        rsi = _rsi_sma(list(prices), period)
        has_position = position is not None and getattr(position, "quantity", 0) > 0

        if rsi < oversold and not has_position:
            return Decision.buy(f"RSI={rsi:.1f} < {oversold}（超卖）")
        if rsi > overbought and has_position:
            return Decision.sell(f"RSI={rsi:.1f} > {overbought}（超买，止盈）")
        return Decision.hold(f"RSI={rsi:.1f}（中性区）")


if _LumiStrategy is not None:
    class RSIReversal(_LumiStrategy, _RSIReversalLogic):
        parameters = _RSIReversalLogic.DEFAULT_PARAMETERS

        def initialize(self):
            self.sleeptime = "1D"

        def on_trading_iteration(self):
            params = self.merged_parameters(self.parameters)
            symbol = params["symbol"]
            length = params["period"] + 10  # 多拉一些点保证 RSI 算法稳定
            hist = self.get_historical_prices(symbol, length, "day")
            if hist is None or hist.df is None or len(hist.df) < params["period"] + 1:
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
    RSIReversal = _RSIReversalLogic  # type: ignore
