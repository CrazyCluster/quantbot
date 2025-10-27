# data_loader.py
import yfinance as yf
import pandas as pd

def load_history(symbol, start, end=None):
    df = yf.download(symbol, start=start, end=end, auto_adjust=False)
    df.dropna(inplace=True)
    df.columns = [c.lower() for c in df.columns]
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    return df
