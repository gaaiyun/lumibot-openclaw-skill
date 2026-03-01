---
name: lumibot-skill
description: Backtesting and trading framework for stocks, options, crypto, futures and more. Unified code for backtesting and live trading with OpenClaw integration.
---

# Lumibot Skill for OpenClaw

## 1. 什么时候用我？

当用户说：
- "回测这个策略"
- "测试股票交易策略"
- "backtest my strategy"
- "创建交易机器人"
- "测试期权策略"
- "加密货币回测"
- 任何需要回测或实盘交易的场景

## 2. 我能做什么？

### 统一的回测和实盘代码
- **相同代码** - 回测和实盘使用相同的策略代码
- **快速切换** - 一键从回测切换到实盘
- **无缝过渡** - 回测验证后直接上线

### 多资产类别支持
- **股票** - 美股、A股等
- **期权** - 期权策略回测
- **加密货币** - BTC、ETH 等
- **期货** - 商品期货、股指期货
- **外汇** - FOREX 交易

### 强大的回测引擎
- **历史数据** - 支持多数据源（Yahoo, ThetaData, Polygon）
- **快速回测** - 优化的回测引擎
- **详细报告** - 完整的性能指标
- **可视化** - 图表展示回测结果

### 实盘交易支持
- **多券商** - Interactive Brokers, Alpaca, Tradier 等
- **实时数据** - 实时行情和交易
- **风险管理** - 内置风险控制
- **订单管理** - 完整的订单生命周期

## 3. 使用示例

### 基础回测
```python
from lumibot.strategies import Strategy
from lumibot.backtesting import YahooDataBacktesting

class MyStrategy(Strategy):
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
MyStrategy.backtest(
    YahooDataBacktesting,
    start_date="2023-01-01",
    end_date="2024-01-01"
)
```

### 快速开始（OpenClaw 命令）
```bash
# 回测示例策略
python scripts/backtest.py --strategy buy_and_hold --symbol AAPL --start 2023-01-01 --end 2024-01-01

# 查看策略模板
python scripts/list_templates.py

# 创建新策略
python scripts/create_strategy.py --name my_strategy --template momentum
```

### OpenClaw 调用
```python
# 在 OpenClaw 中自动触发
用户："帮我回测一个买入持有 AAPL 的策略"
→ 自动调用 lumibot-skill
→ 生成策略代码
→ 运行回测
→ 返回结果报告
```

## 4. 配置说明

### 环境变量
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
```

### 配置文件（config/default.yaml）
```yaml
backtesting:
  data_source: yahoo
  start_date: "2023-01-01"
  end_date: "2024-01-01"
  initial_cash: 100000

live_trading:
  broker: alpaca
  paper_trading: true
  risk_limit: 0.02
```

## 5. 策略模板

### 买入持有策略
```python
class BuyAndHold(Strategy):
    def initialize(self):
        self.sleeptime = "1D"
    
    def on_trading_iteration(self):
        if self.first_iteration:
            self.buy_all(self.parameters["symbol"])
```

### 动量策略
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

### 网格交易策略
```python
class GridTrading(Strategy):
    def initialize(self):
        self.sleeptime = "1H"
        self.grid_levels = 10
        self.grid_spacing = 0.01
    
    def on_trading_iteration(self):
        # 网格交易逻辑
        pass
```

## 6. 回测报告示例

```
=== Backtest Results ===
Strategy: BuyAndHold
Symbol: AAPL
Period: 2023-01-01 to 2024-01-01

Performance Metrics:
- Total Return: 45.2%
- Sharpe Ratio: 1.85
- Max Drawdown: -12.3%
- Win Rate: 65%
- Total Trades: 1

Portfolio Value:
- Initial: $100,000
- Final: $145,200
- Profit: $45,200
```

## 7. 依赖项

### Python 包
- Python 3.10+
- lumibot
- pandas
- numpy
- matplotlib
- yfinance (Yahoo 数据)
- thetadata (ThetaData，可选)

### 安装
```bash
pip install lumibot yfinance pandas numpy matplotlib
```

## 8. 注意事项

1. **数据源选择**: Yahoo 免费但数据有限，ThetaData 需要订阅但数据更全
2. **回测限制**: 历史数据不代表未来表现
3. **实盘风险**: 实盘交易有风险，建议先用 paper trading
4. **策略验证**: 充分回测后再上线实盘

## 9. 故障排除

### 常见问题
- **数据获取失败**: 检查网络连接和 API 配置
- **回测速度慢**: 减少回测周期或使用更快的数据源
- **策略报错**: 检查策略代码逻辑

### 日志位置
- `~/.openclaw/workspace/logs/lumibot.log`

---

_基于 [Lumibot](https://github.com/Lumiwealth/lumibot) 二次开发_
_OpenClaw Skill 封装版本_
