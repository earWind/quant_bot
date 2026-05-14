import unittest

from risk import calculate_position
from backtest import run_ma_backtest
from strategy import (
    STRATEGY_MA_REVERSION,
    STRATEGY_MARTINGALE,
    STRATEGY_MA_TURN,
    generate_signal,
)


def make_ohlcv(closes):
    return [
        [index, close, close, close, close, 1]
        for index, close in enumerate(closes)
    ]


class StrategyTests(unittest.TestCase):
    def test_generate_buy_signal(self):
        data = make_ohlcv([1, 1, 1, 1, 1, 5, 5, 5])

        signal = generate_signal(data, short_window=3, long_window=5)

        self.assertEqual(signal, "BUY")

    def test_generate_sell_signal(self):
        data = make_ohlcv([5, 5, 5, 5, 5, 1, 1, 1])

        signal = generate_signal(data, short_window=3, long_window=5)

        self.assertEqual(signal, "SELL")

    def test_generate_ma_turn_buy_signal(self):
        data = make_ohlcv(list(range(1, 31)))

        signal = generate_signal(
            data,
            short_window=5,
            long_window=20,
            strategy_type=STRATEGY_MA_TURN,
        )

        self.assertEqual(signal, "BUY")

    def test_generate_ma_turn_sell_signal(self):
        data = make_ohlcv(list(range(30, 0, -1)))

        signal = generate_signal(
            data,
            short_window=5,
            long_window=20,
            strategy_type=STRATEGY_MA_TURN,
        )

        self.assertEqual(signal, "SELL")

    def test_generate_ma_turn_uses_fixed_trend_windows(self):
        data = make_ohlcv(list(range(1, 31)))

        signal = generate_signal(
            data,
            short_window=5,
            long_window=30,
            strategy_type=STRATEGY_MA_TURN,
        )

        self.assertEqual(signal, "BUY")

    def test_generate_ma_turn_sells_on_trend_break(self):
        data = make_ohlcv([30] * 15 + [25, 20, 15, 10, 5])

        signal = generate_signal(
            data,
            short_window=5,
            long_window=20,
            strategy_type=STRATEGY_MA_TURN,
        )

        self.assertEqual(signal, "SELL")

    def test_generate_ma_turn_holds_without_trend_break(self):
        data = make_ohlcv([10] * 30)

        signal = generate_signal(
            data,
            short_window=5,
            long_window=20,
            strategy_type=STRATEGY_MA_TURN,
        )

        self.assertEqual(signal, "HOLD")

    def test_generate_ma_reversion_buy_signal(self):
        data = make_ohlcv([10 + i * 0.1 for i in range(24)] + [11.9])

        signal = generate_signal(
            data,
            strategy_type=STRATEGY_MA_REVERSION,
        )

        self.assertEqual(signal, "BUY")

    def test_generate_ma_reversion_holds_when_drop_stays_above_ma5(self):
        data = make_ohlcv(list(range(1, 30)) + [28.6])

        signal = generate_signal(
            data,
            strategy_type=STRATEGY_MA_REVERSION,
        )

        self.assertEqual(signal, "HOLD")

    def test_generate_ma_reversion_holds_without_alignment(self):
        data = make_ohlcv(list(range(30, 5, -1)) + [5.9])

        signal = generate_signal(
            data,
            strategy_type=STRATEGY_MA_REVERSION,
        )

        self.assertEqual(signal, "HOLD")

    def test_ma_reversion_backtest_exits_next_candle(self):
        data = make_ohlcv([10 + i * 0.1 for i in range(24)] + [11.9, 12.2])

        result = run_ma_backtest(
            data,
            strategy_type=STRATEGY_MA_REVERSION,
            fee_rate=0,
        )

        self.assertEqual(result["trade_count"], 2)
        self.assertEqual(result["trades"][0]["side"], "BUY")
        self.assertEqual(result["trades"][1]["side"], "SELL")

    def test_generate_martingale_buy_signal(self):
        data = make_ohlcv([100, 99.4])

        signal = generate_signal(
            data,
            strategy_type=STRATEGY_MARTINGALE,
        )

        self.assertEqual(signal, "BUY")

    def test_martingale_backtest_adds_and_takes_profit(self):
        data = make_ohlcv([100, 99.4, 98.3, 99.8])

        result = run_ma_backtest(
            data,
            strategy_type=STRATEGY_MARTINGALE,
            fee_rate=0,
        )

        self.assertEqual(result["trade_count"], 3)
        self.assertEqual(result["trades"][0]["side"], "BUY")
        self.assertEqual(result["trades"][1]["side"], "BUY")
        self.assertEqual(result["trades"][2]["side"], "SELL")


class RiskTests(unittest.TestCase):
    def test_calculate_position(self):
        amount = calculate_position(balance=1000, risk_percent=0.01, price=50000)

        self.assertEqual(amount, 0.0002)


if __name__ == "__main__":
    unittest.main()
