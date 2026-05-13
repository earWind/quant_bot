# 启动操作说明

## 1. 进入项目目录

```powershell
cd D:\_git\quant_bot
```

## 2. 安装依赖

```powershell
python -m pip install -r requirements.txt
```

如果遇到代理导致安装失败，可以先检查或清理当前代理环境变量。

## 3. 启动 Web 面板

```powershell
python -m uvicorn web_app:app --host 127.0.0.1 --port 8000
```

启动成功后，在浏览器打开：

```text
http://127.0.0.1:8000/
```

## 4. 页面操作

- 点击“刷新一次”：立即获取一次行情并计算当前信号。
- 点击“启动”：按固定间隔循环运行策略。
- 点击“停止”：停止循环运行。
- 点击“查看回测”：拉取 Binance 最近 500 根 K 线，对当前策略做一次回测。

## 5. 当前策略配置

配置文件在 `config.py`。

当前关键参数：

```python
SYMBOL = 'BTC/USDT'
TIMEFRAME = '15m'
SHORT_MA = 5
LONG_MA = 20
RISK_PERCENT = 0.01
TEST_MODE = True
```

`TEST_MODE = True` 时不会真实下单，只会记录交易信号和模拟操作。切换到真实交易前，必须确认 API 权限、资金规模、风控参数和交易所连接状态。

## 6. 常见检查命令

检查 Python 文件是否能编译：

```powershell
python -m py_compile config.py exchange.py strategy.py risk.py backtest.py web_app.py main.py
```

运行单元测试：

```powershell
python -m unittest
```

检查接口状态：

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/status
```

触发一次回测：

```powershell
Invoke-WebRequest -UseBasicParsing -Method Post http://127.0.0.1:8000/api/backtest
```

## 7. 代理说明

`config.py` 默认从环境变量读取代理；如果没有环境变量，会使用：

```python
HTTP_PROXY = "http://127.0.0.1:7897"
HTTPS_PROXY = HTTP_PROXY
```

如果本机没有开启这个代理，访问 Binance 可能失败。可以在启动前设置可用代理，或修改 `config.py` 中的代理配置。
