import threading
from collections import deque
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backtest import run_ma_backtest
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
DEFAULT_INITIAL_BALANCE = 1000
DEFAULT_BACKTEST_LIMIT = 500
DEFAULT_BUY_CONDITION = "above"
DEFAULT_SELL_CONDITION = "below"
VALID_CONDITIONS = {"above", "below"}

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
    "buy_condition": DEFAULT_BUY_CONDITION,
    "sell_condition": DEFAULT_SELL_CONDITION,
    "risk_percent": RISK_PERCENT,
    "initial_balance": DEFAULT_INITIAL_BALANCE,
    "backtest_limit": DEFAULT_BACKTEST_LIMIT,
    "test_mode": TEST_MODE,
    "price": None,
    "signal": "UNKNOWN",
    "amount": None,
    "last_update": None,
    "next_check_seconds": POLL_SECONDS,
    "error": None,
}


class StrategySettings(BaseModel):
    symbol: str = Field(min_length=3)
    timeframe: str
    short_ma: int = Field(gt=0, le=500)
    long_ma: int = Field(gt=1, le=1000)
    buy_condition: str = DEFAULT_BUY_CONDITION
    sell_condition: str = DEFAULT_SELL_CONDITION
    risk_percent: float = Field(gt=0, le=1)
    initial_balance: float = Field(gt=0)
    backtest_limit: int = Field(ge=50, le=1000)


def get_settings():
    with state_lock:
        return {
            "symbol": bot_state["symbol"].upper().strip(),
            "timeframe": bot_state["timeframe"],
            "short_ma": int(bot_state["short_ma"]),
            "long_ma": int(bot_state["long_ma"]),
            "buy_condition": bot_state["buy_condition"],
            "sell_condition": bot_state["sell_condition"],
            "risk_percent": float(bot_state["risk_percent"]),
            "initial_balance": float(bot_state["initial_balance"]),
            "backtest_limit": int(bot_state["backtest_limit"]),
            "test_mode": bool(bot_state["test_mode"]),
        }


def validate_strategy_settings(settings):
    if settings["short_ma"] >= settings["long_ma"]:
        raise ValueError("short_ma must be smaller than long_ma")
    if settings["buy_condition"] not in VALID_CONDITIONS:
        raise ValueError("Unsupported buy condition")
    if settings["sell_condition"] not in VALID_CONDITIONS:
        raise ValueError("Unsupported sell condition")
    if settings["buy_condition"] == settings["sell_condition"]:
        raise ValueError("Buy and sell conditions must be different")


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
    settings = get_settings()
    validate_strategy_settings(settings)

    data = get_ohlcv(settings["symbol"], settings["timeframe"])
    signal = generate_signal(
        data,
        settings["short_ma"],
        settings["long_ma"],
        buy_condition=settings["buy_condition"],
        sell_condition=settings["sell_condition"],
    )
    ticker = exchange.fetch_ticker(settings["symbol"])
    price = ticker["last"]
    amount = calculate_position(
        settings["initial_balance"],
        settings["risk_percent"],
        price,
    )

    update_state(
        price=price,
        signal=signal,
        amount=amount,
        last_update=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        next_check_seconds=POLL_SECONDS,
        error=None,
    )

    add_log(
        f"{settings['symbol']} {settings['timeframe']} price={price}, "
        f"signal={signal}, amount={amount}"
    )

    if signal == "BUY":
        if settings["test_mode"]:
            add_log(f"Test mode: skipped market BUY {amount} {settings['symbol']}")
        else:
            create_market_buy(settings["symbol"], amount)
            add_log(f"Sent market BUY {amount} {settings['symbol']}", "trade")
    elif signal == "SELL":
        if settings["test_mode"]:
            add_log(f"Test mode: skipped market SELL {amount} {settings['symbol']}")
        else:
            create_market_sell(settings["symbol"], amount)
            add_log(f"Sent market SELL {amount} {settings['symbol']}", "trade")
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


@app.post("/api/settings")
def update_settings(settings: StrategySettings):
    try:
        values = settings.model_dump()
        values["symbol"] = values["symbol"].upper().strip()
        validate_strategy_settings(values)

        update_state(
            **values,
            price=None,
            signal="UNKNOWN",
            amount=None,
            last_update=None,
            error=None,
        )
        add_log(
            f"Settings updated: {values['symbol']} {values['timeframe']} "
            f"MA{values['short_ma']}/MA{values['long_ma']} "
            f"buy={values['buy_condition']} sell={values['sell_condition']}"
        )
        return {"ok": True, **get_snapshot()}
    except Exception as exc:
        update_state(error=str(exc))
        return {"ok": False, "error": str(exc), **get_snapshot()}


@app.post("/api/run-once")
def api_run_once():
    try:
        run_once()
        return {"ok": True, **get_snapshot()}
    except Exception as exc:
        update_state(error=str(exc))
        add_log(f"Manual run failed: {exc}", "error")
        return {"ok": False, "error": str(exc), **get_snapshot()}


@app.post("/api/backtest")
def api_backtest():
    try:
        settings = get_settings()
        validate_strategy_settings(settings)

        data = get_ohlcv(
            settings["symbol"],
            settings["timeframe"],
            limit=settings["backtest_limit"],
        )
        result = run_ma_backtest(
            data,
            short_window=settings["short_ma"],
            long_window=settings["long_ma"],
            initial_balance=settings["initial_balance"],
            buy_condition=settings["buy_condition"],
            sell_condition=settings["sell_condition"],
        )
        return {"ok": True, "backtest": result}
    except Exception as exc:
        add_log(f"Backtest failed: {exc}", "error")
        return {"ok": False, "error": str(exc)}


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
