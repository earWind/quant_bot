import ccxt
from config import API_KEY, API_SECRET, HTTP_PROXY, HTTPS_PROXY


VALID_MARKET_TYPES = {"spot", "swap"}
_exchanges = {}


def normalize_market_type(market_type="spot"):
    if market_type not in VALID_MARKET_TYPES:
        raise ValueError(f"Unsupported market type: {market_type}")
    return market_type


def create_exchange(market_type="spot"):
    market_type = normalize_market_type(market_type)
    ccxt_market_type = "future" if market_type == "swap" else market_type
    exchange_config = {
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'timeout': 15000,
        'options': {
            'defaultType': ccxt_market_type,
        },
    }

    if HTTP_PROXY or HTTPS_PROXY:
        exchange_config['proxies'] = {
            'http': HTTP_PROXY,
            'https': HTTPS_PROXY or HTTP_PROXY,
        }

    return ccxt.binance(exchange_config)


def get_exchange(market_type="spot"):
    market_type = normalize_market_type(market_type)
    if market_type not in _exchanges:
        _exchanges[market_type] = create_exchange(market_type)
    return _exchanges[market_type]


def normalize_symbol(symbol, market_type="spot"):
    return symbol


exchange = get_exchange("spot")


def get_ohlcv(symbol, timeframe, limit=200, market_type="spot"):
    active_exchange = get_exchange(market_type)
    symbol = normalize_symbol(symbol, market_type)
    max_batch = 1000

    if limit <= max_batch:
        return active_exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    timeframe_ms = active_exchange.parse_timeframe(timeframe) * 1000
    now_ms = active_exchange.milliseconds()
    since = now_ms - timeframe_ms * limit
    candles_by_time = {}

    while len(candles_by_time) < limit:
        batch = active_exchange.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            since=since,
            limit=min(max_batch, limit - len(candles_by_time)),
        )

        if not batch:
            break

        for candle in batch:
            candles_by_time[candle[0]] = candle

        next_since = batch[-1][0] + timeframe_ms
        if next_since <= since:
            break

        since = next_since

        if len(batch) < max_batch:
            break

    return [
        candles_by_time[timestamp]
        for timestamp in sorted(candles_by_time)
    ][-limit:]


def fetch_ticker(symbol, market_type="spot"):
    return get_exchange(market_type).fetch_ticker(normalize_symbol(symbol, market_type))


def create_market_buy(symbol, amount, market_type="spot"):
    return get_exchange(market_type).create_market_buy_order(
        normalize_symbol(symbol, market_type),
        amount,
    )


def create_market_sell(symbol, amount, market_type="spot"):
    return get_exchange(market_type).create_market_sell_order(
        normalize_symbol(symbol, market_type),
        amount,
    )
