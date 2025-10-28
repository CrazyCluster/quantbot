# alpaca_client.py
import os
import time
import uuid
from alpaca_trade_api.rest import REST, APIError, TimeFrame

from dotenv import load_dotenv
load_dotenv()

def get_alpaca_client():
    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_API_SECRET")
    base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    return REST(key, secret, base)

def get_account(api):
    return api.get_account()

def get_last_price(api, symbol):
    try:
        trade = api.get_latest_trade(symbol)
        return float(trade.price)
    except Exception:
        bars = api.get_bars(symbol, TimeFrame.Day, limit=1)
        return float(bars[-1].c) if bars else None

def get_position_or_none(api, symbol):
    try:
        return api.get_position(symbol)
    except APIError:
        return None

def calc_qty_by_risk_and_caps(api, entry_price, stop_price, risk_per_trade, max_position_pct, max_total_exposure):
    acc = api.get_account()
    equity = float(getattr(acc, 'equity', acc.cash))
    cash = float(acc.cash) if float(acc.cash) > 0 else float(acc.buying_power)
    # risk amount per trade
    risk_amount = equity * float(risk_per_trade)
    per_share_risk = entry_price - stop_price
    if per_share_risk <= 0:
        return 0
    qty = int(risk_amount / per_share_risk)
    if qty < 1:
        return 0
    # cap by max position pct
    max_by_position = int((equity * float(max_position_pct)) / entry_price)
    max_affordable = int((equity * float(max_total_exposure)) / entry_price)
    qty = min(qty, max_by_position, max_affordable)
    return max(qty, 0)

def place_bracket_order(api, symbol, qty, side="buy", take_profit=None, stop_loss=None, client_tag=None):
    client_id = f"{symbol}-{int(time.time())}-{uuid.uuid4().hex[:6]}" if client_tag is None else f"{client_tag}-{int(time.time())}"
    try:
        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type="market",
            time_in_force="day",
            order_class="bracket",
            take_profit={"limit_price": str(take_profit)} if take_profit is not None else None,
            stop_loss={"stop_price": str(stop_loss)} if stop_loss is not None else None,
            client_order_id=client_id
        )
        return order
    except Exception as e:
        raise
