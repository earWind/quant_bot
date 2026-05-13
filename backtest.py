import pandas as pd

from strategy import (
    STRATEGY_MA_CROSS,
    STRATEGY_MA_TURN,
    condition_matches,
    ma_bullish_alignment_signal,
)


def run_ma_backtest(
    data,
    short_window=5,
    long_window=20,
    initial_balance=1000,
    buy_condition="above",
    sell_condition="below",
    strategy_type=STRATEGY_MA_CROSS,
    fee_rate=0.001,
):
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume"
    ])

    required_window = long_window

    if len(df) < required_window + 2:
        raise ValueError("Not enough candle data for the long moving average")

    df["ma5"] = df["close"].rolling(5).mean()
    df["ma10"] = df["close"].rolling(10).mean()
    df["ma20"] = df["close"].rolling(20).mean()

    if strategy_type == STRATEGY_MA_CROSS:
        df["short_ma"] = df["close"].rolling(short_window).mean()
        df["long_ma"] = df["close"].rolling(long_window).mean()
    elif strategy_type == STRATEGY_MA_TURN:
        df["signal_ma"] = df["close"].rolling(long_window).mean()
    else:
        raise ValueError(f"Unsupported strategy type: {strategy_type}")

    cash = float(initial_balance)
    position = 0.0
    total_fees = 0.0
    trades = []
    equity_curve = []

    for _, row in df.iterrows():
        price = float(row["close"])

        if strategy_type == STRATEGY_MA_CROSS:
            if pd.isna(row["short_ma"]) or pd.isna(row["long_ma"]):
                signal = "HOLD"
            elif condition_matches(row["short_ma"], row["long_ma"], buy_condition):
                signal = "BUY"
            elif condition_matches(row["short_ma"], row["long_ma"], sell_condition):
                signal = "SELL"
            else:
                signal = "HOLD"
        else:
            signal = ma_bullish_alignment_signal(
                df.loc[:row.name, "close"],
                df.loc[:row.name, "ma5"],
                df.loc[:row.name, "ma10"],
                df.loc[:row.name, "ma20"],
            )

        if signal == "BUY" and cash > 0:
            fee = cash * fee_rate
            net_cash = cash - fee
            position = net_cash / price
            total_fees += fee
            trades.append({
                "side": "BUY",
                "index": int(row.name),
                "timestamp": int(row["timestamp"]),
                "price": round(price, 2),
                "amount": round(position, 8),
                "equity": round(cash, 2),
                "fee": round(fee, 4),
            })
            cash = 0.0
        elif signal == "SELL" and position > 0:
            gross_cash = position * price
            fee = gross_cash * fee_rate
            cash = gross_cash - fee
            total_fees += fee
            trades.append({
                "side": "SELL",
                "index": int(row.name),
                "timestamp": int(row["timestamp"]),
                "price": round(price, 2),
                "amount": round(position, 8),
                "equity": round(cash, 2),
                "fee": round(fee, 4),
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

    chart_window = min(5000, len(df))
    chart_start = len(df) - chart_window
    chart_df = df.iloc[chart_start:].copy()
    markers = [
        {
            "side": trade["side"],
            "index": trade["index"] - chart_start,
            "price": trade["price"],
        }
        for trade in trades
        if trade["index"] >= chart_start
    ]

    candles = []
    for index, row in chart_df.iterrows():
        ma5 = row["ma5"] if not pd.isna(row["ma5"]) else None
        ma10 = row["ma10"] if not pd.isna(row["ma10"]) else None
        ma20 = row["ma20"] if not pd.isna(row["ma20"]) else None
        candles.append({
            "index": int(index - chart_start),
            "timestamp": int(row["timestamp"]),
            "open": round(float(row["open"]), 2),
            "high": round(float(row["high"]), 2),
            "low": round(float(row["low"]), 2),
            "close": round(float(row["close"]), 2),
            "ma5": round(float(ma5), 2) if ma5 is not None else None,
            "ma10": round(float(ma10), 2) if ma10 is not None else None,
            "ma20": round(float(ma20), 2) if ma20 is not None else None,
        })

    return {
        "initial_balance": round(initial_balance, 2),
        "final_equity": round(final_equity, 2),
        "return_pct": round((final_equity / initial_balance - 1) * 100, 2),
        "buy_hold_pct": round((buy_hold_equity / initial_balance - 1) * 100, 2),
        "max_drawdown_pct": round(max_drawdown * 100, 2),
        "fee_rate_pct": round(fee_rate * 100, 4),
        "total_fees": round(total_fees, 2),
        "trade_count": len(trades),
        "position_open": position > 0,
        "last_price": round(final_price, 2),
        "trades": trades[-20:],
        "chart": {
            "candles": candles,
            "markers": markers,
            "ma_windows": [5, 10, 20],
        },
    }
