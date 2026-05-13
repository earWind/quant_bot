import pandas as pd

from strategy import condition_matches


def run_ma_backtest(
    data,
    short_window=5,
    long_window=20,
    initial_balance=1000,
    buy_condition="above",
    sell_condition="below",
):
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume"
    ])

    if len(df) < long_window:
        raise ValueError("Not enough candle data for the long moving average")

    df["short_ma"] = df["close"].rolling(short_window).mean()
    df["long_ma"] = df["close"].rolling(long_window).mean()

    cash = float(initial_balance)
    position = 0.0
    trades = []
    equity_curve = []

    for _, row in df.iterrows():
        price = float(row["close"])

        if pd.isna(row["short_ma"]) or pd.isna(row["long_ma"]):
            equity_curve.append(cash + position * price)
            continue

        if condition_matches(row["short_ma"], row["long_ma"], buy_condition) and cash > 0:
            position = cash / price
            trades.append({
                "side": "BUY",
                "price": round(price, 2),
                "amount": round(position, 8),
                "equity": round(cash, 2),
            })
            cash = 0.0
        elif condition_matches(row["short_ma"], row["long_ma"], sell_condition) and position > 0:
            cash = position * price
            trades.append({
                "side": "SELL",
                "price": round(price, 2),
                "amount": round(position, 8),
                "equity": round(cash, 2),
            })
            position = 0.0

        equity_curve.append(cash + position * price)

    final_price = float(df.iloc[-1]["close"])
    final_equity = cash + position * final_price
    buy_hold_equity = initial_balance / float(df.iloc[0]["close"]) * final_price
    peak = equity_curve[0]
    max_drawdown = 0.0

    for equity in equity_curve:
        peak = max(peak, equity)
        if peak > 0:
            max_drawdown = min(max_drawdown, (equity - peak) / peak)

    return {
        "initial_balance": round(initial_balance, 2),
        "final_equity": round(final_equity, 2),
        "return_pct": round((final_equity / initial_balance - 1) * 100, 2),
        "buy_hold_pct": round((buy_hold_equity / initial_balance - 1) * 100, 2),
        "max_drawdown_pct": round(max_drawdown * 100, 2),
        "trade_count": len(trades),
        "position_open": position > 0,
        "last_price": round(final_price, 2),
        "trades": trades[-20:],
    }
