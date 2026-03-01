#!/usr/bin/env python3
"""
Lumibot Backtest Script
Simple backtesting interface for OpenClaw
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    from lumibot.strategies import Strategy
    from lumibot.backtesting import YahooDataBacktesting
    from lumibot.entities import Asset
except ImportError:
    print("Error: lumibot not installed. Run: pip install lumibot")
    sys.exit(1)


class BuyAndHold(Strategy):
    """Simple buy and hold strategy"""
    
    def initialize(self):
        self.sleeptime = "1D"
    
    def on_trading_iteration(self):
        if self.first_iteration:
            symbol = self.parameters.get("symbol", "AAPL")
            price = self.get_last_price(symbol)
            if price and self.portfolio_value > 0:
                quantity = int(self.portfolio_value * 0.95 / price)
                if quantity > 0:
                    order = self.create_order(symbol, quantity, "buy")
                    self.submit_order(order)


class Momentum(Strategy):
    """Simple momentum strategy"""
    
    def initialize(self):
        self.sleeptime = "1D"
        self.period = self.parameters.get("period", 20)
    
    def on_trading_iteration(self):
        symbol = self.parameters.get("symbol", "AAPL")
        prices = self.get_historical_prices(symbol, self.period, "day")
        
        if prices and len(prices.df) >= self.period:
            current_price = prices.df["close"].iloc[-1]
            avg_price = prices.df["close"].mean()
            
            position = self.get_position(symbol)
            
            if current_price > avg_price:
                if not position:
                    quantity = int(self.portfolio_value * 0.95 / current_price)
                    if quantity > 0:
                        self.create_order(symbol, quantity, "buy")
            else:
                if position:
                    self.sell_all(symbol)


STRATEGIES = {
    "buy_and_hold": BuyAndHold,
    "momentum": Momentum,
}


def run_backtest(strategy_name, symbol, start_date, end_date, initial_cash=100000):
    """Run backtest with specified parameters"""
    
    if strategy_name not in STRATEGIES:
        print(f"Error: Unknown strategy '{strategy_name}'")
        print(f"Available strategies: {', '.join(STRATEGIES.keys())}")
        return None
    
    StrategyClass = STRATEGIES[strategy_name]
    
    print(f"\n{'='*60}")
    print(f"Running Backtest")
    print(f"{'='*60}")
    print(f"Strategy: {strategy_name}")
    print(f"Symbol: {symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Cash: ${initial_cash:,.2f}")
    print(f"{'='*60}\n")
    
    try:
        result = StrategyClass.backtest(
            YahooDataBacktesting,
            start_date=start_date,
            end_date=end_date,
            parameters={"symbol": symbol},
            initial_cash=initial_cash,
        )
        
        print(f"\n{'='*60}")
        print(f"Backtest Results")
        print(f"{'='*60}")
        
        if result:
            print(f"Final Portfolio Value: ${result.get('portfolio_value', 0):,.2f}")
            print(f"Total Return: {result.get('total_return', 0):.2%}")
            print(f"{'='*60}\n")
        
        return result
        
    except Exception as e:
        print(f"\nError during backtest: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Lumibot Backtest Script for OpenClaw"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        required=True,
        choices=list(STRATEGIES.keys()),
        help="Strategy to backtest"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="AAPL",
        help="Stock symbol (default: AAPL)"
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2023-01-01",
        help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end",
        type=str,
        default="2024-01-01",
        help="End date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--initial-cash",
        type=float,
        default=100000,
        help="Initial cash (default: 100000)"
    )
    
    args = parser.parse_args()
    
    result = run_backtest(
        args.strategy,
        args.symbol,
        args.start,
        args.end,
        args.initial_cash
    )
    
    if result:
        print("✅ Backtest completed successfully!")
        sys.exit(0)
    else:
        print("❌ Backtest failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
