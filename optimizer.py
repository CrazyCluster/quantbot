import optuna
import json
from data_loader import load_adj_close
from strategy import simulate_strategy_for_opt
BEST_FILE = 'best_params_v3.json'

def optimize_symbol(symbol, start='2020-01-01', n_trials=20):
    df = load_adj_close(symbol, start=start)
    df = df.dropna()
    if df.empty:
        return None
    def objective(trial):
        short = trial.suggest_int('short', 5, 30)
        long = trial.suggest_int('long', 40, 200)
        atr_mult = trial.suggest_float('atr_mult', 1.0, 3.5)
        score = simulate_strategy_for_opt(df, short, long, atr_mult)
        return score
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study.best_params

def optimize_all(symbols, start='2020-01-01', n_trials=20):
    results = {}
    for s in symbols:
        try:
            bp = optimize_symbol(s, start=start, n_trials=n_trials)
            if bp:
                results[s] = bp
        except Exception as e:
            print('opt error', s, e)
    with open(BEST_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    return results

def load_best():
    try:
        with open(BEST_FILE,'r') as f:
            return json.load(f)
    except:
        return {}
