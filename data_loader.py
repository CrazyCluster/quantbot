import yfinance as yf
import pandas as pd

def load_adj_close(symbols, start, end=None):
    df = yf.download(symbols, start=start, end=end, progress=False, auto_adjust=True)
    if isinstance(symbols, (list, tuple)) and len(symbols) > 1:
        return df['Adj Close']
    else:
        return df['Adj Close'].to_frame()
