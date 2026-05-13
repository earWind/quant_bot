import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"


def cache_key(symbol, timeframe, market_type="spot"):
    safe_symbol = symbol.replace("/", "_").replace(":", "_")
    return f"{market_type}_{safe_symbol}_{timeframe}".upper()


def cache_path(symbol, timeframe, market_type="spot"):
    return DATA_DIR / f"{cache_key(symbol, timeframe, market_type)}.ohlcv.json"


def readable_cache_path(symbol, timeframe, market_type="spot"):
    path = cache_path(symbol, timeframe, market_type)
    if path.exists():
        return path
    legacy_path = DATA_DIR / f"{symbol.replace('/', '_').replace(':', '_')}_{timeframe}".upper()
    legacy_path = legacy_path.with_suffix(".ohlcv.json")
    if market_type == "spot" and legacy_path.exists():
        return legacy_path
    return path


def load_ohlcv_cache(symbol, timeframe, limit, market_type="spot"):
    path = readable_cache_path(symbol, timeframe, market_type)
    if not path.exists():
        raise FileNotFoundError(f"No local OHLCV cache found for {symbol} {timeframe}")

    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    candles = payload.get("candles", [])
    if len(candles) < limit:
        raise ValueError(
            f"Local cache only has {len(candles)} candles, requested {limit}"
        )

    return candles[-limit:]


def save_ohlcv_cache(symbol, timeframe, candles, market_type="spot"):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = cache_path(symbol, timeframe, market_type)
    deduped = {
        int(candle[0]): candle
        for candle in candles
    }
    ordered = [
        deduped[timestamp]
        for timestamp in sorted(deduped)
    ]
    payload = {
        "symbol": symbol,
        "timeframe": timeframe,
        "market_type": market_type,
        "count": len(ordered),
        "first_timestamp": ordered[0][0] if ordered else None,
        "last_timestamp": ordered[-1][0] if ordered else None,
        "candles": ordered,
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, separators=(",", ":"))

    return payload


def get_cache_info(symbol, timeframe, market_type="spot"):
    path = readable_cache_path(symbol, timeframe, market_type)
    if not path.exists():
        return {
            "exists": False,
            "path": str(path),
            "count": 0,
            "first_timestamp": None,
            "last_timestamp": None,
        }

    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    return {
        "exists": True,
        "path": str(path),
        "count": int(payload.get("count", len(payload.get("candles", [])))),
        "first_timestamp": payload.get("first_timestamp"),
        "last_timestamp": payload.get("last_timestamp"),
    }
