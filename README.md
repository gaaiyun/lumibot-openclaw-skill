# Lumibot Skill for OpenClaw

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Lumibot](https://img.shields.io/badge/Powered%20by-Lumibot-green.svg)](https://lumibot.lumiwealth.com/)

**统一的回测和实盘交易框架 - OpenClaw 集成版**

基于 [Lumibot](https://github.com/Lumiwealth/lumibot) 的 OpenClaw Skill，提供统一的回测和实盘交易接口。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd C:\Users\gaaiy\.openclaw\workspace\skills\lumibot-skill

# 安装核心依赖
pip install lumibot yfinance pandas numpy matplotlib
```

### 2. 运行示例回测

```bash
# 回测买入持有策略
python scripts/backtest.py --strategy buy_and_hold --symbol AAPL --start 2023-01-01 --end 2024-01-01

# 回测动量策略
python scripts/backtest.py --strategy momentum --symbol TSLA --start 2023-01-01 --end 2024-01-01
```

### 3. 查看策略模板

```bash
# 列出所有可用策略模板
python scripts/list_templates.py

# 创建新策略
python scripts/create_strategy.py --name my_strategy --template momentum
```

---

## 📖 功能特性

### 统一的回测和实盘代码
- ✅ **相同代码** - 回测和实盘使用相同的策略代码
- ✅ **快速切换** - 一键从回测切换到实盘
- ✅ **无缝过渡** - 回测验证后直接上线

### 多资产类别支持
- ✅ **股票** - 美股、A股等
- ✅ **期权** - 期权策略回测
- ✅ **加密货币** - BTC、ETH 等
- ✅ **期货** - 商品期货、股指期货
- ✅ **外汇** - FOREX 交易

### 强大的回测引擎
- ✅ **历史数据** - 支持多数据源（Yahoo, ThetaData, Polygon）
- ✅ **快速回测** - 优化的回测引擎
- ✅ **详细报告** - 完整的性能指标
- ✅ **可视化** - 图表展示回测结果

### 实盘交易支持
- ✅ **多券商** - Interactive Brokers, Alpaca, Tradier 等
- ✅ **实时数据** - 实时行情和交易
- ✅ **风险管理** - 内置风险控制
- ✅ **订单管理** - 完整的订单生命周期

---

## 📝 使用示例

### 示例 1: 买入持有策略

```python
from lumibot.strategies import Strategy
from lumibot.backtesting import YahooDataBacktesting

class BuyAndHold(Strategy):
    def initialize(self):
        self.sleeptime = "1D"
    
    def on_trading_iteration(self):
        if self.first_iteration:
            symbol = "AAPL"
            price = self.get_last_price(symbol)
            quantity = self.portfolio_value // price
            order = self.create_order(symbol, quantity, "buy")
            self.submit_order(order)

# 回测
BuyAndHold.backtest(
    YahooDataBacktesting,
    start_date="2023-01-01",
    end_date="2024-01-01"
)
```

### 示例 2: 动量策略

```python
class Momentum(Strategy):
    def initialize(self):
        self.sleeptime = "1D"
        self.period = 20
    
    def on_trading_iteration(self):
        symbol = self.parameters["symbol"]
        prices = self.get_historical_prices(symbol, self.period, "day")
        
        if prices.df["close"][-1] > prices.df["close"].mean():
            if not self.get_position(symbol):
                self.buy_all(symbol)
        else:
            if self.get_position(symbol):
                self.sell_all(symbol)
```

### 示例 3: 命令行使用

```bash
# 回测策略
python scripts/backtest.py \
  --strategy buy_and_hold \
  --symbol AAPL \
  --start 2023-01-01 \
  --end 2024-01-01 \
  --initial-cash 100000

# 查看结果
python scripts/show_results.py --result-file results/backtest_20240301.json
```

---

## ⚙️ 配置说明

### 环境变量

创建 `.env` 文件：

```bash
# 数据源配置
BACKTESTING_DATA_SOURCE=yahoo  # yahoo, thetadata, polygon, ibkr

# ThetaData（推荐，需要订阅）
THETA_USERNAME=your_username
THETA_PASSWORD=your_password

# Interactive Brokers（实盘）
IBKR_USERNAME=your_username
IBKR_PASSWORD=your_password
IBKR_ACCOUNT=your_account

# Alpaca（实盘）
ALPACA_API_KEY=your_api_key
ALPACA_API_SECRET=your_api_secret
ALPACA_PAPER=true
```

### 配置文件

编辑 `config/default.yaml`：

```yaml
backtesting:
  data_source: yahoo
  start_date: "2023-01-01"
  end_date: "2024-01-01"
  initial_cash: 100000
  commission: 0.001

live_trading:
  broker: alpaca
  paper_trading: true
  risk_limit: 0.02
  max_position_size: 0.1

strategies:
  buy_and_hold:
    enabled: true
    symbols: ["AAPL", "MSFT", "GOOGL"]
  
  momentum:
    enabled: true
    period: 20
    symbols: ["TSLA", "NVDA"]
```

---

## 📊 回测报告示例

```
=== Backtest Results ===
Strategy: BuyAndHold
Symbol: AAPL
Period: 2023-01-01 to 2024-01-01

Performance Metrics:
┌─────────────────────┬──────────┐
│ Metric              │ Value    │
├─────────────────────┼──────────┤
│ Total Return        │ 45.2%    │
│ Annual Return       │ 45.2%    │
│ Sharpe Ratio        │ 1.85     │
│ Max Drawdown        │ -12.3%   │
│ Win Rate            │ 65.0%    │
│ Total Trades        │ 1        │
└─────────────────────┴──────────┘

Portfolio Value:
- Initial: $100,000.00
- Final: $145,200.00
- Profit: $45,200.00 (+45.2%)

[Chart: Portfolio Value Over Time]
```

---

## 📁 项目结构

```
lumibot-skill/
├── SKILL.md              # OpenClaw Skill 描述
├── README.md             # 本文档
├── requirements.txt      # 依赖列表
├── scripts/
│   ├── backtest.py       # 回测脚本
│   ├── list_templates.py # 列出策略模板
│   ├── create_strategy.py# 创建新策略
│   └── show_results.py   # 显示回测结果
├── config/
│   └── default.yaml      # 默认配置
├── examples/
│   ├── buy_and_hold.py   # 买入持有示例
│   ├── momentum.py       # 动量策略示例
│   └── grid_trading.py   # 网格交易示例
└── references/
    └── .env.example      # 环境变量模板
```

---

## 🔧 故障排除

### 常见问题

**Q: 数据获取失败**
```
A: 检查网络连接和 API 配置
   - Yahoo Finance 可能有限流
   - ThetaData 需要有效订阅
```

**Q: 回测速度慢**
```
A: 优化建议
   - 减少回测周期
   - 使用更快的数据源（ThetaData）
   - 增加 sleeptime 间隔
```

**Q: 策略报错**
```
A: 检查策略代码
   - 确保 initialize() 方法正确
   - 检查 on_trading_iteration() 逻辑
   - 查看日志文件
```

### 日志位置

```
~/.openclaw/workspace/logs/lumibot.log
```

---

## 📚 策略模板库

### 1. 买入持有（Buy and Hold）
- **适用**: 长期投资
- **风险**: 低
- **复杂度**: 简单

### 2. 动量策略（Momentum）
- **适用**: 趋势跟踪
- **风险**: 中
- **复杂度**: 中等

### 3. 网格交易（Grid Trading）
- **适用**: 震荡市场
- **风险**: 中
- **复杂度**: 中等

### 4. 均值回归（Mean Reversion）
- **适用**: 震荡市场
- **风险**: 中高
- **复杂度**: 中等

### 5. 配对交易（Pairs Trading）
- **适用**: 市场中性
- **风险**: 低中
- **复杂度**: 高

---

## 🙏 致谢

- 原项目：[Lumibot](https://github.com/Lumiwealth/lumibot)
- 数据源：[Yahoo Finance](https://finance.yahoo.com/), [ThetaData](https://www.thetadata.net/)
- 社区：[Lumiwealth](https://lumiwealth.com/)

---

## 📄 许可证

MIT License

---

## ⚠️ 免责声明

本工具仅供教育和研究目的。不构成投资建议。

交易有风险，投资需谨慎。请在充分了解风险的情况下使用本工具。

---

_基于 [Lumibot](https://github.com/Lumiwealth/lumibot) 二次开发_
_OpenClaw Skill 封装版本_
