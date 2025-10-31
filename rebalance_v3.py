import os, json, math, uuid
from datetime import datetime
STATE_FILE = 'rebalance_state_v3.json'
LOG_FILE = 'rebalance_trades_v3.json'

def _load_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return { 'last_week': None }

def _save_state(s):
    with open(STATE_FILE, 'w') as f:
        json.dump(s, f, indent=2)

def _append_log(entry):
    arr = []
    try:
        with open(LOG_FILE,'r') as f:
            arr = json.load(f)
    except:
        arr = []
    arr.append(entry)
    with open(LOG_FILE,'w') as f:
        json.dump(arr, f, indent=2)

def _unique_client_id(sym):
    return f"{sym}-{uuid.uuid4().hex[:8]}"

def rebalance(api, growth_symbols, defensive_symbols, growth_pct=0.7, defensive_pct=0.3, max_position_pct=0.25, max_total_exposure=0.9, min_order_usd=1.0, require_market_open=True):
    state = _load_state()
    week = datetime.utcnow().isocalendar()[1]
    if state.get('last_week') == week:
        return { 'status':'skipped', 'reason':'already_rebalanced_this_week', 'week': week }

    try:
        clock = api.get_clock()
        if require_market_open and not clock.is_open:
            return { 'status':'skipped', 'reason':'market_closed' }
    except Exception:
        pass

    acc = api.get_account()
    equity = float(getattr(acc, 'equity', getattr(acc, 'portfolio_value', getattr(acc, 'cash', 0))))
    if equity <= 0:
        return { 'status':'error', 'reason':'invalid_equity', 'equity': equity }

    all_syms = list(dict.fromkeys(list(growth_symbols)+list(defensive_symbols)))
    if not all_syms:
        return { 'status':'error', 'reason':'no_symbols' }

    targets = {}
    if growth_symbols:
        per = equity * growth_pct / len(growth_symbols)
        for s in growth_symbols:
            targets[s] = per
    if defensive_symbols:
        per = equity * defensive_pct / len(defensive_symbols)
        for s in defensive_symbols:
            targets[s] = per

    allowed = equity * max_total_exposure
    ssum = sum(targets.values())
    if ssum > allowed:
        scale = allowed/ssum
        for k in targets:
            targets[k] *= scale

    cap = equity * max_position_pct
    for k in list(targets.keys()):
        if targets[k] > cap:
            targets[k] = cap

    pos_map = {}
    try:
        for p in api.list_positions():
            pos_map[p.symbol] = { 'qty': float(p.qty), 'market_value': float(p.market_value) }
    except Exception:
        pos_map = {}

    orders = []
    for s, tval in targets.items():
        curval = pos_map.get(s, {}).get('market_value', 0.0)
        delta = tval - curval
        try:
            pr = api.get_latest_trade(s).price
            price = float(pr)
        except Exception:
            price = None
        if price is None or price <= 0:
            continue
        if abs(delta) < min_order_usd:
            continue
        if delta > 0:
            qty = int(math.floor(delta / price))
            if qty <= 0:
                continue
            bp = float(getattr(acc,'buying_power', getattr(acc,'cash',0)))
            max_aff = int(bp // price)
            qty = min(qty, max_aff)
            if qty <= 0:
                continue
            orders.append({'symbol':s,'side':'buy','qty':qty,'price':price})
        else:
            qty = int(math.floor((-delta)/price))
            owned = int(pos_map.get(s,{}).get('qty',0))
            qty = min(qty, owned)
            if qty <= 0:
                continue
            orders.append({'symbol':s,'side':'sell','qty':qty,'price':price})

    executed = []
    for o in orders:
        try:
            client_id = _unique_client_id(o['symbol'])
            order = api.submit_order(symbol=o['symbol'], qty=o['qty'], side=o['side'], type='market', time_in_force='day', client_order_id=client_id)
            entry = { 'timestamp': datetime.utcnow().isoformat(), 'symbol': o['symbol'], 'side': o['side'], 'qty': o['qty'], 'price': o['price'], 'client_id': client_id, 'alpaca_id': getattr(order,'id',''), 'status':'submitted' }
            _append_log(entry)
            executed.append(entry)
        except Exception as e:
            entry = { 'timestamp': datetime.utcnow().isoformat(), 'symbol': o['symbol'], 'side': o['side'], 'qty': o['qty'], 'price': o['price'], 'status':'error', 'error': str(e) }
            _append_log(entry)

    state['last_week'] = week
    _save_state(state)
    return { 'status':'done', 'week': week, 'equity': equity, 'orders': executed }
