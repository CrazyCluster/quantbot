import os
from alpaca_trade_api.rest import REST, TimeFrame, APIError

def get_alpaca_client():
    key = os.getenv('ALPACA_API_KEY')
    secret = os.getenv('ALPACA_API_SECRET')
    base = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
    return REST(key, secret, base)

def get_latest_price(api, symbol):
    try:
        t = api.get_latest_trade(symbol)
        return float(t.price)
    except Exception:
        try:
            bars = api.get_bars(symbol, TimeFrame.Day, limit=1)
            if bars:
                return float(bars[-1].c)
        except Exception:
            return None
        return None
