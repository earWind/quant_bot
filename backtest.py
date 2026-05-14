import pandas as pd

from strategy import (
    STRATEGY_MA_CROSS,
    STRATEGY_MA_REVERSION,
    STRATEGY_MARTINGALE,
    STRATEGY_MA_TURN,
    MARTINGALE_ENTRY_DROP_THRESHOLD,
    REVERSION_DROP_THRESHOLD,
    condition_matches,
    ma_bullish_alignment_signal,
    ma_reversion_entry_signal,
)


MARTINGALE_BASE_FRACTION = 0.1
MARTINGALE_PRICE_STEP = 0.01
MARTINGALE_MULTIPLIER = 2
MARTINGALE_MAX_LEVELS = 5
MARTINGALE_TAKE_PROFIT = 0.008


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

    required_window = 2 if strategy_type == STRATEGY_MARTINGALE else long_window

    if len(df) < required_window:
        raise ValueError("Not enough candle data for the selected strategy")

    df["ma5"] = df["close"].rolling(5).mean()
    df["ma10"] = df["close"].rolling(10).mean()
    df["ma20"] = df["close"].rolling(20).mean()

    if strategy_type == STRATEGY_MA_CROSS:
        df["short_ma"] = df["close"].rolling(short_window).mean()
        df["long_ma"] = df["close"].rolling(long_window).mean()
    elif strategy_type in {STRATEGY_MA_TURN, STRATEGY_MA_REVERSION, STRATEGY_MARTINGALE}:
        df["signal_ma"] = df["close"].rolling(long_window).mean()
    else:
        raise ValueError(f"Unsupported strategy type: {strategy_type}")

    cash = float(initial_balance)
    position = 0.0
    total_fees = 0.0
    trades = []
    equity_curve = []
    entry_index = None
    martingale_level = 0
    martingale_next_buy_price = None
    cost_basis = 0.0

    for _, row in df.iterrows():
        price = float(row["close"])
        signal = "HOLD"

        if strategy_type == STRATEGY_MA_CROSS:
            if pd.isna(row["short_ma"]) or pd.isna(row["long_ma"]):
                signal = "HOLD"
            elif condition_matches(row["short_ma"], row["long_ma"], buy_condition):
                signal = "BUY"
            elif condition_matches(row["short_ma"], row["long_ma"], sell_condition):
                signal = "SELL"
            else:
                signal = "HOLD"
        elif strategy_type == STRATEGY_MA_TURN:
            signal = ma_bullish_alignment_signal(
                df.loc[:row.name, "close"],
                df.loc[:row.name, "ma5"],
                df.loc[:row.name, "ma10"],
                df.loc[:row.name, "ma20"],
            )
        elif strategy_type == STRATEGY_MA_REVERSION:
            previous_close = float(df.loc[row.name - 1, "close"]) if row.name > 0 else price
            candle_return = price / previous_close - 1
            exit_due_to_time = entry_index is not None and row.name > entry_index
            exit_due_to_drop = position > 0 and candle_return <= REVERSION_DROP_THRESHOLD

            if position > 0 and (exit_due_to_time or exit_due_to_drop):
                signal = "SELL"
            elif position == 0:
                signal = ma_reversion_entry_signal(
                    df.loc[:row.name, "close"],
                    df.loc[:row.name, "ma5"],
                    df.loc[:row.name, "ma10"],
                    df.loc[:row.name, "ma20"],
                )
            else:
                signal = "HOLD"
        else:
            previous_close = float(df.loc[row.name - 1, "close"]) if row.name > 0 else price
            candle_return = price / previous_close - 1
            average_cost = cost_basis / position if position > 0 else None

            if position > 0 and average_cost and price >= average_cost * (1 + MARTINGALE_TAKE_PROFIT):
                signal = "SELL"
            elif position == 0 and candle_return <= MARTINGALE_ENTRY_DROP_THRESHOLD:
                signal = "BUY"
            elif (
                position > 0
                and martingale_level < MARTINGALE_MAX_LEVELS
                and martingale_next_buy_price is not None
                and price <= martingale_next_buy_price
                and cash > 0
            ):
                signal = "BUY"

        if signal == "BUY" and cash > 0:
            if strategy_type == STRATEGY_MARTINGALE:
                base_order = initial_balance * MARTINGALE_BASE_FRACTION
                order_cash = min(cash, base_order * (MARTINGALE_MULTIPLIER ** martingale_level))
            else:
                order_cash = cash

            fee = order_cash * fee_rate
            net_cash = order_cash - fee
            bought_amount = net_cash / price
            position += bought_amount
            cost_basis += net_cash
            total_fees += fee
            trades.append({
                "side": "BUY",
                "index": int(row.name),
                "timestamp": int(row["timestamp"]),
                "price": round(price, 2),
                "amount": round(bought_amount, 8),
                "equity": round(cash, 2),
                "fee": round(fee, 4),
            })
            cash -= order_cash
            entry_index = int(row.name)
            if strategy_type == STRATEGY_MARTINGALE:
                martingale_level += 1
                martingale_next_buy_price = price * (1 - MARTINGALE_PRICE_STEP)
        elif signal == "SELL" and position > 0:
            gross_cash = position * price
            fee = gross_cash * fee_rate
            cash += gross_cash - fee
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
            cost_basis = 0.0
            entry_index = None
            if strategy_type == STRATEGY_MARTINGALE:
                martingale_level = 0
                martingale_next_buy_price = None

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
