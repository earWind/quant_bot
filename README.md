# 币圈量化交易系统（基础版）

这是一个基于 Python + CCXT 的基础量化交易机器人示例，用于学习行情获取、双均线策略、仓位管理和自动下单流程。

> 数字货币交易风险很高。本项目仅用于学习和测试，默认开启测试模式，不会真实下单。

## 功能

- 获取 Binance 行情数据
- 使用双均线策略生成买卖信号
- 根据账户资金和风险比例计算仓位
- 支持测试模式和真实下单模式
- 循环运行并定时检查行情

## 项目结构

```text
quant_bot/
├── config.py
├── exchange.py
├── main.py
├── risk.py
├── strategy.py
├── requirements.txt
└── README.md
```

## 安装

```bash
pip install -r requirements.txt
```

如果系统没有全局 Python，可以使用项目中的虚拟环境：

```powershell
.\.venv\Scripts\python.exe main.py
```

## 配置 API

默认从环境变量读取 Binance API：

```powershell
$env:BINANCE_API_KEY="你的 API KEY"
$env:BINANCE_API_SECRET="你的 SECRET KEY"
```

配置文件在 `config.py`：

```python
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1h'
SHORT_MA = 5
LONG_MA = 20
RISK_PERCENT = 0.01
TEST_MODE = True
```

保持 `TEST_MODE = True` 时只会打印交易信号，不会发送真实订单。切换到真实交易前，请先确认 API 权限、交易对、资金规模和风控参数。

## 运行

```powershell
.\.venv\Scripts\python.exe main.py
```

程序会每 60 秒获取一次行情。如果发生网络或交易所接口错误，会等待 10 秒后重试。按 `Ctrl+C` 可以停止程序。

## 策略逻辑

当前使用双均线策略：

- `MA5 > MA20`：买入信号
- `MA5 < MA20`：卖出信号
- 均线相等：观望

该策略更适合趋势行情，不适合长期横盘或剧烈震荡行情。

## 风控建议

- 单次交易风险建议控制在总资金的 1% 到 2%
- 新手不要满仓，不要使用高杠杆
- 真实交易前必须增加止损、止盈和异常订单处理
- 建议先加入回测模块，再考虑实盘

## 后续升级方向

- 增加历史回测
- 保存交易日志和订单记录
- 支持更多交易对轮动
- 接入 WebSocket 实时行情
- 增加 RSI、MACD、布林带等策略
- 增加止损、止盈、最大回撤控制
