---
name: lumibot-openclaw-skill
description: Lumibot 5 个内置策略（buy_and_hold / momentum / dual_ma / mean_reversion / rsi_reversal）+ 离线纯逻辑对比回测 + 真回测两条路径。
---

# lumibot-openclaw-skill

## 什么时候用

- "对 AAPL 在过去一年回测均线突破策略"
- "把买入持有、动量、双均线三个策略在同一只票上对比一下"
- "我想看看 RSI 反转 vs 均值回归哪个 Sharpe 更高"
- "用 lumibot 跑实盘前先离线 sanity check 一下"

## 入口

```bash
python __main__.py list-strategies                          # 看可用策略
python __main__.py compare --symbol AAPL --start 2023-01-01 # 5 策略对比
python __main__.py compare --csv data.csv -o report.json    # 本地 CSV 数据
python __main__.py backtest momentum --symbol TSLA          # lumibot 真回测
```

库调用：

- `scripts.strategies::STRATEGIES` — `{"buy_and_hold": cls, "momentum": cls, ...}`
- `scripts.strategies::*::decide(prices, position, params) -> Decision` — 纯函数
- `scripts.simple_backtester::run(strategy, prices, params)` — 极简回测
- `scripts.compare::compare_strategies(strategies, prices)` — 对比报告

## 评估指标

| 列 | 含义 |
|---|---|
| `TotalRet` | 整段累计收益 |
| `AnnRet` | 按 252 期/年 年化 |
| `AnnVol` | 年化波动 |
| `Sharpe` | (mean / std) × √252，未减无风险利率 |
| `MaxDD` | 净值最大回撤 |
| `Trades` | 交易次数（一次买入一次卖出算 2 次） |

## 依赖

- 必需：Python 3.10+，标准库
- 可选 yfinance：抓真实日线
- 可选 lumibot：用真事件驱动回测引擎

## 注意事项

- 离线回测不模拟滑点 / 佣金 / 部分成交，结果偏乐观，仅作粗筛。
- 默认 95% 仓位 + 5% 现金，需要满仓改 `allocation=1.0`。
- Sharpe 排序可能忽视最大回撤，自己读表时综合判断。
