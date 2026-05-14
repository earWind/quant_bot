import pandas as pd


STRATEGY_MA_CROSS = "ma_cross"
STRATEGY_MA_TURN = "ma_turn"
STRATEGY_MA_REVERSION = "ma_reversion"
STRATEGY_MARTINGALE = "martingale"
REVERSION_DROP_THRESHOLD = -0.005
MARTINGALE_ENTRY_DROP_THRESHOLD = -0.005


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

    ma20_recent = ma20_values.dropna().tail(3)
    ma20_is_rising = len(ma20_recent) == 3 and ma20_recent.iloc[-1] > ma20_recent.iloc[0]
    bullish_alignment = latest_close > latest_ma5 > latest_ma10 > latest_ma20
    trend_broken = latest_close < latest_ma20 or latest_ma5 < latest_ma10

    if bullish_alignment and ma20_is_rising:
        return "BUY"
    if trend_broken:
        return "SELL"

    return "HOLD"


def generate_ma_turn_signal(df, ma_window):
    if len(df) < 20:
        return "HOLD"

    ma5 = df["close"].rolling(5).mean()
    ma10 = df["close"].rolling(10).mean()
    ma20 = df["close"].rolling(20).mean()
    return ma_bullish_alignment_signal(df["close"], ma5, ma10, ma20)


def ma_reversion_entry_signal(close_values, ma5_values, ma10_values, ma20_values):
    if len(close_values) < 2:
        return "HOLD"

    latest_ma5 = ma5_values.iloc[-1]
    latest_ma10 = ma10_values.iloc[-1]
    latest_ma20 = ma20_values.iloc[-1]

    if pd.isna(latest_ma5) or pd.isna(latest_ma10) or pd.isna(latest_ma20):
        return "HOLD"

    previous_close = close_values.iloc[-2]
    latest_close = close_values.iloc[-1]
    latest_drop = latest_close / previous_close - 1

    if (
        latest_ma5 > latest_ma10 > latest_ma20
        and latest_drop <= REVERSION_DROP_THRESHOLD
        and latest_close < latest_ma5
    ):
        return "BUY"

    return "HOLD"


def generate_ma_reversion_signal(df):
    if len(df) < 20:
        return "HOLD"

    ma5 = df["close"].rolling(5).mean()
    ma10 = df["close"].rolling(10).mean()
    ma20 = df["close"].rolling(20).mean()
    return ma_reversion_entry_signal(df["close"], ma5, ma10, ma20)


def generate_martingale_signal(df):
    if len(df) < 2:
        return "HOLD"

    previous_close = df["close"].iloc[-2]
    latest_close = df["close"].iloc[-1]
    latest_drop = latest_close / previous_close - 1

    if latest_drop <= MARTINGALE_ENTRY_DROP_THRESHOLD:
        return "BUY"

    return "HOLD"


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
    if strategy_type == STRATEGY_MA_REVERSION:
        return generate_ma_reversion_signal(df)
    if strategy_type == STRATEGY_MARTINGALE:
        return generate_martingale_signal(df)

    raise ValueError(f"Unsupported strategy type: {strategy_type}")
