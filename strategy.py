import pandas as pd
import numpy as np

def compute_indicators(df, short=10, long=50, atr_period=14):
    df = df.copy()
    if 'Adj Close' not in df.columns and 'Adj Close' in df:
        # ensure column exists
        pass
    df['short_ma'] = df['Adj Close'].rolling(short).mean()
    df['long_ma'] = df['Adj Close'].rolling(long).mean()
    if 'High' in df.columns and 'Low' in df.columns:
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Adj Close'].shift()).abs()
        low_close = (df['Low'] - df['Adj Close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(atr_period).mean()
    else:
        df['atr'] = df['Adj Close'].pct_change().rolling(atr_period).std() * df['Adj Close']
        df['atr'].fillna(method='bfill', inplace=True)
    df.dropna(inplace=True)
    return df

def generate_signal(df, params):
    df2 = compute_indicators(df, params.get('short',10), params.get('long',50), 14)
    latest = df2.iloc[-1]
    if latest['short_ma'] > latest['long_ma']:
        entry = float(latest['Adj Close'])
        atr = float(latest['atr']) if latest['atr']>0 else 1.0
        stop = entry - params.get('atr_mult',1.5)*atr
        take = entry + 2*atr
        return {'action':'buy','entry':entry,'stop':round(stop,2),'take':round(take,2)}
    return {'action':'hold'}

def simulate_strategy_for_opt(df, short, long, atr_mult):
    df2 = compute_indicators(df, short, long)
    df2['signal'] = (df2['short_ma'] > df2['long_ma']).astype(int)
    df2['returns'] = df2['Adj Close'].pct_change()
    df2['strategy'] = df2['signal'].shift(1) * df2['returns']
    total = df2['strategy'].sum()
    sharpe = (df2['strategy'].mean() / df2['strategy'].std()) * (252**0.5) if df2['strategy'].std()>0 else 0
    return total * 0.6 + sharpe * 0.4
