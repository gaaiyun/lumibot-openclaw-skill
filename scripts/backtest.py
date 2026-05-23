"""legacy 入口：用 lumibot YahooDataBacktesting 跑单策略真回测。

新代码请用顶层 ``python __main__.py backtest <strategy> --symbol AAPL ...``
（同样的策略注册表 + 多个内置策略 + 一致的 CLI 风格）。

本文件保留是为了不破坏 README 老示例和已有调用脚本。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.strategies import STRATEGIES


def run_backtest(strategy_name: str, symbol: str, start_date: str,
                 end_date: str, initial_cash: float = 100_000.0):
    try:
        from lumibot.backtesting import YahooDataBacktesting   # type: ignore
    except ImportError:
        print("Error: lumibot not installed. Run: pip install lumibot")
        return None

    if strategy_name not in STRATEGIES:
        print(f"Error: Unknown strategy '{strategy_name}'")
        print(f"Available strategies: {', '.join(STRATEGIES.keys())}")
        return None
    StrategyClass = STRATEGIES[strategy_name]

    print("=" * 60)
    print("Running Backtest")
    print("=" * 60)
    print(f"Strategy: {strategy_name}")
    print(f"Symbol: {symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Cash: ${initial_cash:,.2f}")
    print("=" * 60)

    try:
        result = StrategyClass.backtest(
            YahooDataBacktesting,
            start_date=start_date, end_date=end_date,
            parameters={"symbol": symbol}, initial_cash=initial_cash,
        )
    except Exception as e:
        print(f"\nError during backtest: {e}")
        import traceback
        traceback.print_exc()
        return None

    print()
    print("=" * 60)
    print("Backtest Results")
    print("=" * 60)
    if isinstance(result, dict):
        for k, v in result.items():
            print(f"  {k}: {v}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Lumibot Backtest Script (legacy entry)")
    parser.add_argument("--strategy", required=True, choices=list(STRATEGIES.keys()))
    parser.add_argument("--symbol", default="AAPL")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2024-01-01")
    parser.add_argument("--initial-cash", type=float, default=100_000.0)

    args = parser.parse_args()
    result = run_backtest(args.strategy, args.symbol, args.start, args.end,
                          args.initial_cash)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
