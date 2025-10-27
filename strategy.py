# strategy.py (conservative live strategy)
import numpy as np
import pandas as pd

def compute_indicators(df, short_window=15, long_window=80, atr_period=14):
    df = df.copy()
    df['short_ma'] = df['close'].rolling(short_window).mean()
    df['long_ma'] = df['close'].rolling(long_window).mean()
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(atr_period).mean()
    df.dropna(inplace=True)
    return df

def generate_signals(data_dict, short_window=15, long_window=80, atr_period=14, atr_multiplier=2.0):
    decisions = []
    for symbol, df in data_dict.items():
        df2 = compute_indicators(df, short_window, long_window, atr_period)
        latest = df2.iloc[-1]
        if latest['short_ma'] > latest['long_ma']:
            entry_price = float(latest['close'])
            atr = float(latest['atr']) if latest['atr'] > 0 else 1.0
            stop_price = entry_price - atr * atr_multiplier
            take_profit = entry_price + 2 * atr
            decisions.append({
                "symbol": symbol,
                "action": "buy",
                "entry_price": entry_price,
                "stop_price": stop_price,
                "take_profit": take_profit,
                "atr": atr
            })
        else:
            decisions.append({"symbol": symbol, "action": "hold"})
    return decisions
