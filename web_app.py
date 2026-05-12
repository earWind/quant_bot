import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
POLL_SECONDS = 60

app = FastAPI(title="Quant Bot Dashboard")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

state_lock = threading.Lock()
logs = deque(maxlen=200)
bot_thread = None
stop_event = threading.Event()
bot_running = False

bot_state = {
    "running": False,
    "symbol": SYMBOL,
    "timeframe": TIMEFRAME,
    "short_ma": SHORT_MA,
    "long_ma": LONG_MA,
    "risk_percent": RISK_PERCENT,
    "test_mode": TEST_MODE,
    "price": None,
    "signal": "UNKNOWN",
    "amount": None,
    "last_update": None,
    "next_check_seconds": POLL_SECONDS,
    "error": None,
}


def add_log(message, level="info"):
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "level": level,
        "message": message,
    }
    with state_lock:
        logs.appendleft(entry)


def update_state(**kwargs):
    with state_lock:
        bot_state.update(kwargs)


def get_snapshot():
    with state_lock:
        return {
            "state": dict(bot_state),
            "logs": list(logs),
        }


def run_once():
    data = get_ohlcv(SYMBOL, TIMEFRAME)
    signal = generate_signal(data, SHORT_MA, LONG_MA)
    ticker = exchange.fetch_ticker(SYMBOL)
    price = ticker["last"]
    amount = calculate_position(1000, RISK_PERCENT, price)

    update_state(
        price=price,
        signal=signal,
        amount=amount,
        last_update=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        next_check_seconds=POLL_SECONDS,
        error=None,
    )

    add_log(f"{SYMBOL} price={price}, signal={signal}, amount={amount}")

    if signal == "BUY":
        if TEST_MODE:
            add_log(f"Test mode: skipped market BUY {amount} {SYMBOL}")
        else:
            create_market_buy(SYMBOL, amount)
            add_log(f"Sent market BUY {amount} {SYMBOL}", "trade")
    elif signal == "SELL":
        if TEST_MODE:
            add_log(f"Test mode: skipped market SELL {amount} {SYMBOL}")
        else:
            create_market_sell(SYMBOL, amount)
            add_log(f"Sent market SELL {amount} {SYMBOL}", "trade")
    else:
        add_log("No trade signal. Holding position.")


def bot_loop():
    global bot_running

    update_state(running=True, error=None)
    add_log("Bot started.")

    try:
        while not stop_event.is_set():
            try:
                run_once()
            except Exception as exc:
                update_state(error=str(exc))
                add_log(f"Error: {exc}", "error")

            for remaining in range(POLL_SECONDS, 0, -1):
                if stop_event.wait(1):
                    break
                update_state(next_check_seconds=remaining - 1)
    finally:
        bot_running = False
        update_state(running=False, next_check_seconds=POLL_SECONDS)
        add_log("Bot stopped.")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def status():
    return get_snapshot()


@app.post("/api/run-once")
def api_run_once():
    try:
        run_once()
        return {"ok": True, **get_snapshot()}
    except Exception as exc:
        update_state(error=str(exc))
        add_log(f"Manual run failed: {exc}", "error")
        return {"ok": False, "error": str(exc), **get_snapshot()}


@app.post("/api/start")
def start_bot():
    global bot_thread, bot_running

    if bot_running:
        return {"ok": True, "message": "Bot already running", **get_snapshot()}

    stop_event.clear()
    bot_running = True
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()

    return {"ok": True, "message": "Bot started", **get_snapshot()}


@app.post("/api/stop")
def stop_bot():
    stop_event.set()
    return {"ok": True, "message": "Stopping bot", **get_snapshot()}
