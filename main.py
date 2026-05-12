import time

from config import (
    LONG_MA,
    RISK_PERCENT,
    SHORT_MA,
    SYMBOL,
    TEST_MODE,
    TIMEFRAME,
)
from exchange import create_market_buy, create_market_sell, exchange, get_ohlcv
from risk import calculate_position
from strategy import generate_signal


def run_bot():
    while True:
        try:
            data = get_ohlcv(SYMBOL, TIMEFRAME)

            signal = generate_signal(
                data,
                SHORT_MA,
                LONG_MA
            )

            ticker = exchange.fetch_ticker(SYMBOL)
            price = ticker['last']

            balance = 1000
            amount = calculate_position(
                balance,
                RISK_PERCENT,
                price
            )

            print(f"当前价格: {price}")
            print(f"交易信号: {signal}")

            if signal == 'BUY':
                print(f"买入 {amount}")

                if not TEST_MODE:
                    create_market_buy(SYMBOL, amount)

            elif signal == 'SELL':
                print(f"卖出 {amount}")

                if not TEST_MODE:
                    create_market_sell(SYMBOL, amount)

            else:
                print("保持观望")

            if TEST_MODE:
                print("测试模式: 未发送真实订单")

            time.sleep(60)

        except KeyboardInterrupt:
            print("已停止")
            break

        except Exception as e:
            print("错误:", e)
            time.sleep(10)


if __name__ == "__main__":
    run_bot()
