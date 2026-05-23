# lumibot-openclaw-skill

围绕 [Lumibot](https://github.com/Lumiwealth/lumibot) 的策略库 + 离线对比工具。

两条路径：

1. **lumibot 真回测**（需要 `pip install lumibot`）—— 把策略类喂给 `YahooDataBacktesting` 跑事件驱动回测。
2. **离线纯逻辑对比**（标准库 + 可选 yfinance）—— 把策略的 `decide()` 纯函数喂入价格序列，跑一遍极简事件回测，输出多策略对比表。

第二条路径是 v2 新增的核心 —— Lumibot 真回测要起本地服务 + 拉数据缓存几十秒，
不适合 CI 跑 / 不适合"在五只票上五个策略各跑一遍出表"这种粗筛。

## v2 新增

| 模块 | 干什么 |
|---|---|
| `scripts/strategies/` | 5 个内置策略：`buy_and_hold` / `momentum` / `dual_ma` / `mean_reversion` / `rsi_reversal`。每个策略把 `decide(prices, position, params) -> Decision` 拆出来当纯函数，便于单测 |
| `scripts/simple_backtester.py` | 极简事件回测：逐 step 喂价格调 `decide`，记录组合净值、决策、交易数 |
| `scripts/compare.py` | 多策略 + 同数据 → CompareRow 表（TotalRet / AnnRet / AnnVol / Sharpe / MaxDD / Trades） |
| `__main__.py` | 统一 CLI：`backtest` / `compare` / `list-strategies` |
| `tests/` | 43 个 pytest，无 lumibot / yfinance 依赖，100ms 跑完 |

## 安装

```bash
pip install -r requirements.txt
# 离线 compare 路径：仅需 yfinance（标准库够剩下的）
# 真回测路径：还需 pip install lumibot pandas numpy matplotlib
```

## 快速开始

```bash
# 列出所有内置策略 + 默认参数
python __main__.py list-strategies

# 离线对比：把 5 个策略在 AAPL 上跑一遍出表（用 yfinance）
python __main__.py compare --symbol AAPL --start 2023-01-01 --end 2024-01-01 \
    -o report.json

# 或者用本地 CSV（不联网）
python __main__.py compare --csv data/aapl.csv -o report.json

# 用真 lumibot 回测单策略（需要 pip install lumibot）
python __main__.py backtest momentum --symbol TSLA --start 2023-01-01 --end 2024-01-01
```

`compare` 命令是核心 —— 同一份数据上 5 个策略各跑一遍，按 Sharpe 排序出表，
不用提前挑指标 / 挑参数地图地"我的策略很赚钱"。

## 一个真实的对比输出

```
$ python __main__.py compare --csv data/synth.csv
[ok] 价格序列长度 253（来自 data/synth.csv）

Strategy        TotalRet  AnnRet  AnnVol  Sharpe  MaxDD   Trades
----------------------------------------------------------------
mean_reversion  24.90%    25.35%  8.50%   2.66    -2.35%  7
buy_and_hold    67.49%    71.54%  21.95%  2.46    -8.32%  1
momentum        48.83%    51.64%  19.42%  2.15    -4.63%  15
dual_ma         45.75%    48.85%  20.59%  1.93    -8.30%  6
rsi_reversal    11.06%    11.24%  5.77%   1.85    -2.35%  3
```

排序按 Sharpe 降序。`mean_reversion` 收益不是最高，但风险调整后回报最好 ——
在 22% 年化波动率的上涨行情里，`buy_and_hold` 拿到 67% 总回报但回撤也大。
按你自己的偏好（追求 Sharpe / 追求总收益 / 最小回撤）挑列读。

## 库调用

```python
from scripts.strategies import STRATEGIES, Momentum
from scripts.simple_backtester import run
from scripts.compare import compare_strategies, render_table

# 单策略
momentum = Momentum()
result = run(momentum, prices=[100, 101, 102, ...],
             initial_cash=10_000, params={"period": 20})
print(f"final value: {result.final_value:.2f}, "
      f"trades: {result.n_trades}")

# 多策略对比
instances = {name: cls() for name, cls in STRATEGIES.items()}
rows = compare_strategies(instances, prices=[...], initial_cash=10_000)
print(render_table(rows))
```

## 内置策略

| 名称 | 信号 | 默认参数 |
|---|---|---|
| `buy_and_hold` | 首迭代 all-in，不卖 | `allocation=0.95` |
| `momentum` | 价 > MA(period) → 买；价 ≤ MA → 卖 | `period=20` |
| `dual_ma` | MA(fast) 上穿 MA(slow) → 买；下穿 → 卖 | `fast_period=10, slow_period=30` |
| `mean_reversion` | z-score < -threshold → 买；> +threshold → 卖 | `period=20, z_threshold=1.5` |
| `rsi_reversal` | RSI < oversold → 买；> overbought → 卖 | `period=14, oversold=30, overbought=70` |

要加新策略：

1. 在 `scripts/strategies/` 新建 `my_strategy.py`，参考 `momentum.py` 的结构
2. 实现 `_MyStrategyLogic.decide(prices, position, params) -> Decision`
3. 在 `scripts/strategies/__init__.py` 注册到 `STRATEGIES` 字典

`decide` 返回 `Decision.buy(reason)` / `Decision.sell(reason)` / `Decision.hold(reason)`，
回测器和 lumibot 包装层都按 `decision.action` 走。

## 项目结构

```
lumibot-openclaw-skill/
├── __main__.py                       # v2 统一 CLI
├── scripts/
│   ├── strategies/                   # v2 可插拔策略库
│   │   ├── _base.py                  # Decision + StrategyBase
│   │   ├── buy_and_hold.py
│   │   ├── momentum.py
│   │   ├── dual_ma.py
│   │   ├── mean_reversion.py
│   │   ├── rsi_reversal.py
│   │   └── __init__.py               # STRATEGIES 注册表
│   ├── simple_backtester.py          # v2 极简事件回测
│   ├── compare.py                    # v2 多策略对比报告
│   └── backtest.py                   # v1 legacy lumibot 单策略回测入口
├── tests/                            # 43 个测试，无 lumibot 依赖
├── config/
│   └── default.yaml                  # 配置（v1）
└── requirements.txt
```

## 设计取舍

- **不依赖 lumibot 也能用**：`decide()` 拆成纯函数后，CI、本地实验、教学场景
  都能跑 —— lumibot 装起来要 ~30+ 包，绝大多数用户只是想看"我的策略大概是不是赚钱"。
- **离线回测不模拟真实成交**：没有滑点 / 佣金 / 盘前盘后 / 部分成交。这是粗筛
  工具，跑完后挑出几个候选再用 lumibot 真回测验证。
- **策略默认 95% 仓位**：留 5% 现金应对真实场景的部分成交 + 手续费。要拉满改
  `allocation=1.0`。
- **不内置实盘交易包装**：lumibot 自己的 `IBKR` / `Alpaca` / `Tradier` broker 集成
  已经完备，本仓库不重复造，需要实盘直接读 lumibot 文档。

## 测试

```bash
pip install pytest
pytest tests/ -v
```

43 个测试，全部跑在 100ms 内，无网络 / 无 lumibot 依赖。

## 已知限制

- `mean_reversion` 用 z-score 阈值切买卖，过低的阈值容易频繁交易（trade count 见
  compare 输出）。
- `rsi_reversal` 用 SMA 版 RSI 而不是 Wilder 平滑版 —— 在收敛速度上略有差异但
  足够指标化判断。
- `compare` 默认按 Sharpe 排序，可能让人忽视最大回撤；自己读表时三个指标一起看。
- 离线 compare 不能跑期权 / 加密货币 / 期货策略（数据接口没接），那些仍要走真
  lumibot 路径。

## 许可

MIT
