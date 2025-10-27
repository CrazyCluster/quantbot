# optimizer.py (Optuna for live parameters - conservative bounds)
import optuna
import json
from data_loader import load_history
from strategy import compute_indicators

BEST_PARAMS_FILE = "best_params_live.json"

def simulate_strategy(df, short_window, long_window, atr_mult):
    df = compute_indicators(df, short_window, long_window)
    df['signal'] = (df['short_ma'] > df['long_ma']).astype(int)
    df['returns'] = df['close'].pct_change()
    df['strategy'] = df['signal'].shift(1) * df['returns']
    total_return = df['strategy'].cumsum().iloc[-1]
    sharpe = (df['strategy'].mean() / df['strategy'].std()) * (252**0.5) if df['strategy'].std() != 0 else 0
    return total_return * 0.6 + sharpe * 0.4

def optimize_for_symbol(symbol, start="2023-01-01", end=None, n_trials=15):
    df = load_history(symbol, start, end)
    df.dropna(inplace=True)
    def objective(trial):
        short_window = trial.suggest_int("short_window", 10, 30)
        long_window = trial.suggest_int("long_window", 60, 200)
        atr_mult = trial.suggest_float("atr_multiplier", 1.5, 3.5)
        score = simulate_strategy(df, short_window, long_window, atr_mult)
        return score
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study.best_params, study.best_value

def optimize_all(symbols, start="2023-01-01"):
    results = {}
    for s in symbols:
        try:
            best_params, best_score = optimize_for_symbol(s, start)
            results[s] = {"params": best_params, "score": best_score}
            print(f"Optimized {s}: {best_params}, score={best_score:.4f}")
        except Exception as e:
            print("Error optimizing", s, e)
    with open(BEST_PARAMS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    return results

def load_best_params():
    try:
        with open(BEST_PARAMS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}
