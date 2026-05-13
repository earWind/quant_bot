import pandas as pd


STRATEGY_MA_CROSS = "ma_cross"
STRATEGY_MA_TURN = "ma_turn"


def condition_matches(short_ma, long_ma, condition):
    if condition == "above":
        return short_ma > long_ma
    if condition == "below":
        return short_ma < long_ma
    raise ValueError(f"Unsupported condition: {condition}")


def ma_turn_signal(ma_values):
    recent = ma_values.dropna().tail(3)

    if len(recent) < 3:
        return "HOLD"

    previous_delta = recent.iloc[-2] - recent.iloc[-3]
    current_delta = recent.iloc[-1] - recent.iloc[-2]

    if previous_delta <= 0 and current_delta > 0:
        return "BUY"
    if previous_delta >= 0 and current_delta < 0:
        return "SELL"

    return "HOLD"


def generate_ma_cross_signal(
    df,
    short_window,
    long_window,
    buy_condition,
    sell_condition,
):
    if len(df) < long_window:
        return "HOLD"

    df["short_ma"] = df["close"].rolling(short_window).mean()
    df["long_ma"] = df["close"].rolling(long_window).mean()

    latest = df.iloc[-1]

    if pd.isna(latest["short_ma"]) or pd.isna(latest["long_ma"]):
        return "HOLD"
    if condition_matches(latest["short_ma"], latest["long_ma"], buy_condition):
        return "BUY"
    if condition_matches(latest["short_ma"], latest["long_ma"], sell_condition):
        return "SELL"

    return "HOLD"


def ma_turn_or_price_below_signal(close_values, ma_values):
    if len(close_values) == 0:
        return "HOLD"

    latest_close = close_values.iloc[-1]
    latest_ma = ma_values.iloc[-1]

    if pd.isna(latest_ma):
        return "HOLD"
    if latest_close < latest_ma:
        return "SELL"

    return ma_turn_signal(ma_values)


def ma_bullish_alignment_signal(close_values, ma5_values, ma10_values, ma20_values):
    if len(close_values) == 0:
        return "HOLD"

    latest_close = close_values.iloc[-1]
    latest_ma5 = ma5_values.iloc[-1]
    latest_ma10 = ma10_values.iloc[-1]
    latest_ma20 = ma20_values.iloc[-1]

    if pd.isna(latest_ma5) or pd.isna(latest_ma10) or pd.isna(latest_ma20):
        return "HOLD"
    if latest_close < latest_ma20:
        return "SELL"

    turn_signal = ma_turn_signal(ma20_values)
    if turn_signal == "SELL":
        return "SELL"
    if turn_signal == "BUY" and latest_ma5 > latest_ma10 > latest_ma20:
        return "BUY"

    return "HOLD"


def generate_ma_turn_signal(df, ma_window):
    if len(df) < ma_window:
        return "HOLD"

    ma5 = df["close"].rolling(5).mean()
    ma10 = df["close"].rolling(10).mean()
    ma20 = df["close"].rolling(ma_window).mean()
    return ma_bullish_alignment_signal(df["close"], ma5, ma10, ma20)


def generate_signal(
    data,
    short_window=5,
    long_window=20,
    buy_condition="above",
    sell_condition="below",
    strategy_type=STRATEGY_MA_CROSS,
):

    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high',
        'low', 'close', 'volume'
    ])

    if strategy_type == STRATEGY_MA_CROSS:
        return generate_ma_cross_signal(
            df,
            short_window,
            long_window,
            buy_condition,
            sell_condition,
        )
    if strategy_type == STRATEGY_MA_TURN:
        return generate_ma_turn_signal(df, long_window)

    raise ValueError(f"Unsupported strategy type: {strategy_type}")
