import pandas as pd


def condition_matches(short_ma, long_ma, condition):
    if condition == "above":
        return short_ma > long_ma
    if condition == "below":
        return short_ma < long_ma
    raise ValueError(f"Unsupported condition: {condition}")


def generate_signal(
    data,
    short_window=5,
    long_window=20,
    buy_condition="above",
    sell_condition="below",
):

    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high',
        'low', 'close', 'volume'
    ])

    df['short_ma'] = df['close'].rolling(short_window).mean()
    df['long_ma'] = df['close'].rolling(long_window).mean()

    latest = df.iloc[-1]

    if condition_matches(latest['short_ma'], latest['long_ma'], buy_condition):
        return 'BUY'

    elif condition_matches(latest['short_ma'], latest['long_ma'], sell_condition):
        return 'SELL'

    return 'HOLD'
