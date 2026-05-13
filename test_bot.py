import unittest

from risk import calculate_position
from strategy import STRATEGY_MA_TURN, generate_signal


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
        data = make_ohlcv([10] * 17 + [7, 7, 7, 7, 50])

        signal = generate_signal(
            data,
            short_window=5,
            long_window=20,
            strategy_type=STRATEGY_MA_TURN,
        )

        self.assertEqual(signal, "BUY")

    def test_generate_ma_turn_sell_signal(self):
        data = make_ohlcv([10] * 17 + [13, 13, 13, 13, 2])

        signal = generate_signal(
            data,
            short_window=5,
            long_window=20,
            strategy_type=STRATEGY_MA_TURN,
        )

        self.assertEqual(signal, "SELL")

    def test_generate_ma_turn_uses_long_ma_window(self):
        data = make_ohlcv([10] * 17 + [7, 7, 7, 7, 50])

        signal = generate_signal(
            data,
            short_window=5,
            long_window=20,
            strategy_type=STRATEGY_MA_TURN,
        )

        self.assertEqual(signal, "BUY")

    def test_generate_ma_turn_sells_when_price_below_long_ma(self):
        data = make_ohlcv([10] * 19 + [9])

        signal = generate_signal(
            data,
            short_window=5,
            long_window=20,
            strategy_type=STRATEGY_MA_TURN,
        )

        self.assertEqual(signal, "SELL")

    def test_generate_ma_turn_holds_without_bullish_alignment(self):
        data = make_ohlcv([10] * 17 + [7, 7, 7, 7, 12])

        signal = generate_signal(
            data,
            short_window=5,
            long_window=20,
            strategy_type=STRATEGY_MA_TURN,
        )

        self.assertEqual(signal, "HOLD")


class RiskTests(unittest.TestCase):
    def test_calculate_position(self):
        amount = calculate_position(balance=1000, risk_percent=0.01, price=50000)

        self.assertEqual(amount, 0.0002)


if __name__ == "__main__":
    unittest.main()
