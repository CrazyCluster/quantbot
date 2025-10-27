# main.py (Live-capable entrypoint, conservative behavior)
import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from data_loader import load_history
from strategy import generate_signals
from alpaca_client import get_alpaca_client, get_account, get_position_or_none, calc_qty_by_risk_and_caps, place_bracket_order
from logger_util import append_trade, trades_today_count
from optimizer import load_best_params, optimize_all
from email_report import send_weekly_email
from datetime import datetime

load_dotenv()

app = Flask(__name__)

INVOKE_SECRET = os.getenv("INVOKE_SECRET", "")
TRADING_MODE = os.getenv("TRADING_MODE", "paper")
MAX_DAILY_TRADES = int(os.getenv("MAX_DAILY_TRADES", "5"))
MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "0.02"))
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.01"))
MAX_POSITION_PCT = float(os.getenv("MAX_POSITION_PCT", "0.20"))
MAX_TOTAL_EXPOSURE = float(os.getenv("MAX_TOTAL_EXPOSURE", "0.8"))
TICKERS = os.getenv("TICKERS", "AAPL,MSFT,NVDA,AMZN,GOOGL").split(",")
START_DATE = os.getenv("START_DATE", "2023-01-01")

# For simple daily-loss tracking, keep a very small persistent file
STATE_FILE = "bot_state.json"

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"start_equity": None, "stopped_until": None}

def save_state(s):
    with open(STATE_FILE, "w") as f:
        json.dump(s, f)

@app.route("/run", methods=["POST","GET"])
def run_all():
    token = request.headers.get("X-Invoke-Token") or request.args.get("token")
    if INVOKE_SECRET and token != INVOKE_SECRET:
        return ("Unauthorized", 401)

    state = load_state()
    api = get_alpaca_client()
    account = get_account(api)
    equity = float(getattr(account, 'equity', getattr(account, 'cash', 0)))

    # initialize start equity for day
    if state.get("start_equity") is None:
        state["start_equity"] = equity
        save_state(state)

    # Circuit-breaker: if stopped_until set and in future -> skip
    stopped_until = state.get("stopped_until")
    if stopped_until:
        try:
            until_ts = datetime.fromisoformat(stopped_until)
            if until_ts > datetime.utcnow():
                return jsonify({"status":"stopped","reason":"circuit_breaker","until":stopped_until}), 200
        except:
            pass

    # daily loss check
    start_eq = float(state.get("start_equity", equity))
    if start_eq > 0 and (start_eq - equity) / start_eq >= MAX_DAILY_LOSS:
        # set stopped until next day
        from datetime import timedelta
        stop_until = (datetime.utcnow() + timedelta(days=1)).isoformat()
        state["stopped_until"] = stop_until
        save_state(state)
        return jsonify({"status":"stopped","reason":"max_daily_loss_reached","stopped_until":stop_until}), 200

    today_trades = trades_today_count()
    if today_trades >= MAX_DAILY_TRADES:
        return jsonify({"status":"skipped", "reason":"daily trade cap reached", "today_trades":today_trades}), 200

    params = load_best_params()
    if not params:
        optimize_all(TICKERS, start=START_DATE)
        params = load_best_params()

    # load data
    data = {}
    for t in TICKERS:
        try:
            data[t] = load_history(t, START_DATE, None)
        except Exception as e:
            print("Data load error", t, e)

    decisions = []
    for t in TICKERS:
        df = data.get(t)
        if df is None or df.empty:
            continue
        p = params.get(t, {}).get("params", {"short_window":15, "long_window":80, "atr_multiplier":2.0})
        d = generate_signals({t: df}, short_window=p['short_window'], long_window=p['long_window'], atr_period=14, atr_multiplier=p['atr_multiplier'])
        decisions.extend(d)

    results = []
    for dec in decisions:
        symbol = dec['symbol']
        action = dec.get('action','hold')
        if action != 'buy':
            results.append({'symbol':symbol, 'action':'hold'})
            continue

        pos = get_position_or_none(api, symbol)
        if pos:
            results.append({'symbol':symbol, 'action':'already_position'})
            continue

        entry_price = dec['entry_price']
        stop_price = dec['stop_price']
        atr = dec['atr']
        qty = calc_qty_by_risk_and_caps(api, entry_price, stop_price, RISK_PER_TRADE, MAX_POSITION_PCT, MAX_TOTAL_EXPOSURE)
        if qty <= 0:
            results.append({'symbol':symbol, 'action':'skipped_qty0'})
            continue

        if TRADING_MODE != 'live':
            # If not live, just simulate/place to paper endpoint
            try:
                order = place_bracket_order(api, symbol, qty, side='buy', take_profit=dec['take_profit'], stop_loss=round(stop_price,2), client_tag='sim')
                append_trade({
                    'timestamp': datetime.utcnow().isoformat(),
                    'symbol': symbol,
                    'side': 'buy',
                    'qty': qty,
                    'price': entry_price,
                    'order_id': getattr(order, 'id',''),
                    'status':'submitted',
                    'mode': TRADING_MODE,
                    'notes':'bracket order placed (sim)'
                })
                results.append({'symbol':symbol, 'action':'submitted', 'order_id': getattr(order,'id','')})
            except Exception as e:
                append_trade({
                    'timestamp': datetime.utcnow().isoformat(),
                    'symbol': symbol,
                    'side': 'buy',
                    'qty': qty,
                    'price': entry_price,
                    'order_id': '',
                    'status':'error',
                    'mode': TRADING_MODE,
                    'notes': str(e)
                })
                results.append({'symbol':symbol, 'action':'error', 'error':str(e)})
        else:
            # LIVE mode: place real order (still uses same function)
            try:
                order = place_bracket_order(api, symbol, qty, side='buy', take_profit=dec['take_profit'], stop_loss=round(stop_price,2), client_tag='live')
                append_trade({
                    'timestamp': datetime.utcnow().isoformat(),
                    'symbol': symbol,
                    'side': 'buy',
                    'qty': qty,
                    'price': entry_price,
                    'order_id': getattr(order, 'id',''),
                    'status':'submitted',
                    'mode': TRADING_MODE,
                    'notes':'bracket order placed (live)'
                })
                results.append({'symbol':symbol, 'action':'submitted', 'order_id': getattr(order,'id','')})
            except Exception as e:
                append_trade({
                    'timestamp': datetime.utcnow().isoformat(),
                    'symbol': symbol,
                    'side': 'buy',
                    'qty': qty,
                    'price': entry_price,
                    'order_id': '',
                    'status':'error',
                    'mode': TRADING_MODE,
                    'notes': str(e)
                })
                results.append({'symbol':symbol, 'action':'error', 'error':str(e)})

    return jsonify({'status':'done','results':results}), 200

@app.route('/optimize', methods=['POST'])
def trigger_optimize():
    token = request.headers.get('X-Invoke-Token')
    if INVOKE_SECRET and token != INVOKE_SECRET:
        return ('Unauthorized', 401)
    optimize_all(TICKERS, start=START_DATE)
    return jsonify({'status':'ok','message':'Optimization done.'})

@app.route('/report', methods=['POST'])
def trigger_report():
    token = request.headers.get('X-Invoke-Token')
    if INVOKE_SECRET and token != INVOKE_SECRET:
        return ('Unauthorized', 401)
    send_weekly_email()
    return jsonify({'status':'ok','message':'Report sent.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','10000')))
