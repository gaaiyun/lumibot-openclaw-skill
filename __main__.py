"""lumibot-openclaw-skill CLI。

子命令：
    backtest <strategy> --symbol AAPL --start 2023-01-01 --end 2024-01-01
        用真 lumibot + YahooDataBacktesting 跑（需要 pip install lumibot）

    compare --symbol AAPL --start 2023-01-01 --end 2024-01-01
        用极简事件回测对所有内置策略在同一份数据上做对比表
        （不需要 lumibot，只需要 yfinance 或 CSV）

    list-strategies
        列出可用策略 + 默认参数
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _fetch_prices(symbol: str, start: str, end: Optional[str]) -> List[float]:
    """从 yfinance 抓收盘价。"""
    try:
        import yfinance as yf
    except ImportError as e:
        raise ImportError(
            "yfinance 未安装。运行 pip install yfinance 后再用 compare/fetch。"
        ) from e
    df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
    if df is None or df.empty:
        raise RuntimeError(f"yfinance 没返回 {symbol} 的数据")
    return df["Close"].astype(float).tolist()


def _read_prices_csv(path: str, column: str = "Close") -> List[float]:
    import csv
    out = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                out.append(float(row[column]))
            except (KeyError, ValueError):
                continue
    if not out:
        raise RuntimeError(f"在 {path} 列 {column} 没读到任何数字")
    return out


def cmd_backtest(args) -> int:
    """走 lumibot 真回测路径。"""
    try:
        from lumibot.backtesting import YahooDataBacktesting   # type: ignore
    except ImportError:
        sys.stderr.write("[error] lumibot 未安装。pip install lumibot 后重试。\n")
        return 2

    from scripts.strategies import STRATEGIES
    if args.strategy not in STRATEGIES:
        sys.stderr.write(f"[error] 未知策略 {args.strategy}，可选 {list(STRATEGIES)}\n")
        return 1
    StrategyClass = STRATEGIES[args.strategy]

    params = {"symbol": args.symbol}
    sys.stderr.write(
        f"[info] backtest {args.strategy} on {args.symbol} "
        f"{args.start}→{args.end} cash={args.initial_cash}\n"
    )
    try:
        result = StrategyClass.backtest(
            YahooDataBacktesting,
            start_date=args.start, end_date=args.end,
            parameters=params, initial_cash=args.initial_cash,
        )
    except Exception as e:  # pragma: no cover - 实盘真回测才会跑到
        sys.stderr.write(f"[error] backtest 抛错：{e}\n")
        return 3

    sys.stderr.write("[ok] 回测完成\n")
    if isinstance(result, dict):
        for k, v in result.items():
            print(f"  {k}: {v}")
    return 0


def cmd_compare(args) -> int:
    if args.csv:
        prices = _read_prices_csv(args.csv, column=args.csv_column)
        source = args.csv
    else:
        try:
            prices = _fetch_prices(args.symbol, args.start, args.end)
        except ImportError as e:
            sys.stderr.write(f"[error] {e}\n")
            return 2
        except Exception as e:
            sys.stderr.write(f"[error] fetch failed: {e}\n")
            return 3
        source = f"yfinance({args.symbol})"

    sys.stderr.write(f"[ok] 价格序列长度 {len(prices)}（来自 {source}）\n")

    from scripts.strategies import STRATEGIES
    from scripts.compare import compare_strategies, render_table

    strategies = {name: cls() for name, cls in STRATEGIES.items()}
    rows = compare_strategies(strategies, prices, initial_cash=args.initial_cash)
    rows.sort(key=lambda r: r.sharpe, reverse=True)

    print()
    print(render_table(rows))
    print()

    if args.output:
        payload = {
            "source": source,
            "n_prices": len(prices),
            "initial_cash": args.initial_cash,
            "rows": [r.to_dict() for r in rows],
        }
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        sys.stderr.write(f"[ok] 写入 {args.output}\n")
    return 0


def cmd_list(args) -> int:
    from scripts.strategies import STRATEGIES
    print(f"{'name':<18} {'default parameters'}")
    print("-" * 60)
    for name, cls in STRATEGIES.items():
        defaults = ", ".join(f"{k}={v}" for k, v in cls.DEFAULT_PARAMETERS.items())
        print(f"{name:<18} {defaults}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lumibot-skill",
        description="多策略 lumibot 回测 + 离线 compare 对比表"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("backtest", help="走 lumibot YahooDataBacktesting 真回测")
    sp.add_argument("strategy")
    sp.add_argument("--symbol", default="AAPL")
    sp.add_argument("--start", default="2023-01-01")
    sp.add_argument("--end", default="2024-01-01")
    sp.add_argument("--initial-cash", type=float, default=100_000.0)
    sp.set_defaults(func=cmd_backtest)

    sp = sub.add_parser("compare", help="离线对比所有内置策略（不需要 lumibot）")
    sp.add_argument("--symbol", default="AAPL")
    sp.add_argument("--start", default="2023-01-01")
    sp.add_argument("--end", default="2024-01-01")
    sp.add_argument("--csv", help="改用 CSV 数据源（避开 yfinance）")
    sp.add_argument("--csv-column", default="Close", help="CSV 里取哪一列价格")
    sp.add_argument("--initial-cash", type=float, default=100_000.0)
    sp.add_argument("-o", "--output", help="输出 JSON 报告")
    sp.set_defaults(func=cmd_compare)

    sp = sub.add_parser("list-strategies", help="列出可用策略")
    sp.set_defaults(func=cmd_list)

    return p


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
