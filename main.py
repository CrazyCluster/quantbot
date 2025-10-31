from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from stock_selector import select_top_stocks
from rebalance_v3 import rebalance
from optimizer import optimize_all, load_best
from email_report import send_weekly_report
from alpaca_client import get_alpaca_client

load_dotenv()
app = Flask(__name__)
INVOKE_SECRET = os.getenv('INVOKE_SECRET','')

growth_static = ['AAPL','MSFT','NVDA','AMZN','GOOGL','META','TSLA']
defensive_static = ['JNJ','PG','KO','PEP','MCD','XOM','CVX']

@app.route('/auto_select_rebalance', methods=['POST','GET'])
def auto_select_rebalance():
    token = request.headers.get('X-Invoke-Token') or request.args.get('token')
    if INVOKE_SECRET and token != INVOKE_SECRET:
        return ('Unauthorized', 401)
    # extend with index lists (simple example)
    nasdaq = ['AAPL','MSFT','NVDA','META','TSLA','AMZN','GOOGL','ADBE','NFLX','AVGO','COST']
    sp_def = ['PG','KO','PEP','MCD','WMT','CL','KMB','MDLZ','GIS','HSY']
    growth_pool = list(set(growth_static + nasdaq))
    def_pool = list(set(defensive_static + sp_def))
    # 1) selection
    selected = select_top_stocks(growth_pool, def_pool, top_n_growth=5, top_n_def=3)
    # 2) optimize (optuna) for selected symbols
    try:
        optimize_all(selected.get('growth',[]) + selected.get('defensive',[]), start='2020-01-01', n_trials=int(os.getenv('OPTUNA_TRIALS',20)))
    except Exception as e:
        print('optimize_all error', e)
    # 3) rebalance using best params (rebalance uses equal weight per group)
    api = get_alpaca_client()
    res = rebalance(api, selected.get('growth',[]), selected.get('defensive',[]), growth_pct=0.7, defensive_pct=0.3)
    return jsonify({'selected': selected, 'rebalance': res}), 200

@app.route('/optimize', methods=['POST'])
def trigger_optimize():
    token = request.headers.get('X-Invoke-Token') or request.args.get('token')
    if INVOKE_SECRET and token != INVOKE_SECRET:
        return ('Unauthorized', 401)
    pool = growth_static + defensive_static
    res = optimize_all(pool, start='2020-01-01', n_trials=int(os.getenv('OPTUNA_TRIALS',20)))
    return jsonify({'optimized': list(res.keys())}), 200

@app.route('/rebalance', methods=['POST','GET'])
def trigger_rebalance():
    token = request.headers.get('X-Invoke-Token') or request.args.get('token')
    if INVOKE_SECRET and token != INVOKE_SECRET:
        return ('Unauthorized', 401)
    api = get_alpaca_client()
    # fallback: use static lists
    res = rebalance(api, growth_static[:5], defensive_static[:3], growth_pct=0.7, defensive_pct=0.3)
    return jsonify({'rebalance': res}), 200

@app.route('/report', methods=['POST','GET'])
def report():
    token = request.headers.get('X-Invoke-Token') or request.args.get('token')
    if INVOKE_SECRET and token != INVOKE_SECRET:
        return ('Unauthorized', 401)
    send_weekly_report()
    return jsonify({'status':'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','10000')))
