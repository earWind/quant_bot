import ccxt
from config import API_KEY, API_SECRET, HTTP_PROXY, HTTPS_PROXY

exchange_config = {
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'timeout': 15000,
    'options': {
        'defaultType': 'spot',
    },
}

if HTTP_PROXY or HTTPS_PROXY:
    exchange_config['proxies'] = {
        'http': HTTP_PROXY,
        'https': HTTPS_PROXY or HTTP_PROXY,
    }

exchange = ccxt.binance(exchange_config)

def get_ohlcv(symbol, timeframe, limit=200):
    return exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

def create_market_buy(symbol, amount):
    return exchange.create_market_buy_order(symbol, amount)

def create_market_sell(symbol, amount):
    return exchange.create_market_sell_order(symbol, amount)
