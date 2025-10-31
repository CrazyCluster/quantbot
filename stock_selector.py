import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def compute_metrics(symbol, start, end):
    try:
        df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty:
            return None
        adj = df['Adj Close'].dropna()
        returns = adj.pct_change().dropna()
        perf = (adj.iloc[-1] / adj.iloc[0]) - 1
        vol = returns.std()
        sharpe = returns.mean() / vol * (252**0.5) if vol > 0 else 0.0
        # RSI
        delta = adj.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_latest = float(rsi.dropna().iloc[-1]) if not rsi.dropna().empty else 50.0

        return { 'symbol': symbol, 'perf': perf, 'vol': vol, 'sharpe': sharpe, 'rsi': rsi_latest }
    except Exception as e:
        print('compute_metrics error', symbol, e)
        return None

def select_top_stocks(growth_watchlist, defensive_watchlist, top_n_growth=5, top_n_def=3, lookback_days=90):
    end = datetime.today()
    start = end - timedelta(days=lookback_days)
    rows = []
    symbols = list(dict.fromkeys(list(growth_watchlist) + list(defensive_watchlist)))
    for s in symbols:
        m = compute_metrics(s, start, end)
        if m:
            rows.append(m)
    if not rows:
        return { 'growth': [], 'defensive': [] }
    df = pd.DataFrame(rows).set_index('symbol')
    for col in ['perf','sharpe']:
        if df[col].max() - df[col].min() > 0:
            df[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
        else:
            df[col] = 0.0
    df['growth_score'] = df['perf'] * 0.65 + df['sharpe'] * 0.35
    df['def_score'] = (1 / (1 + df['vol'])) * 0.7 + (100 - abs(df['rsi'] - 50)) / 100 * 0.3
    growth_df = df.loc[df.index.isin(growth_watchlist)].nlargest(top_n_growth, 'growth_score')
    def_df = df.loc[df.index.isin(defensive_watchlist)].nlargest(top_n_def, 'def_score')
    selected = { 'growth': growth_df.index.tolist(), 'defensive': def_df.index.tolist() }
    df.to_csv('selection_metrics.csv')
    return selected
