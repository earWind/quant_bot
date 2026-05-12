import pandas as pd

def generate_signal(data, short_window=5, long_window=20):

    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high',
        'low', 'close', 'volume'
    ])

    df['short_ma'] = df['close'].rolling(short_window).mean()
    df['long_ma'] = df['close'].rolling(long_window).mean()

    latest = df.iloc[-1]

    if latest['short_ma'] > latest['long_ma']:
        return 'BUY'

    elif latest['short_ma'] < latest['long_ma']:
        return 'SELL'

    return 'HOLD'
