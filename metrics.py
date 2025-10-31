import numpy as np
import pandas as pd

def calc_returns(adj_close_df):
    return adj_close_df.pct_change().dropna()

def avg_corr(returns_df):
    corr = returns_df.corr()
    # average off-diagonal correlation
    m = corr.values
    n = m.shape[0]
    if n <= 1:
        return 0.0
    sum_off = (m.sum() - n) / (n*(n-1))
    return float(sum_off)

def herfindahl(weights):
    w = np.array(weights)
    return float((w**2).sum())

def diversification_ratio(weights, returns_df):
    vols = returns_df.std()
    cov = returns_df.cov().values
    w = np.array(weights)
    num = (w * vols.values).sum()
    den = (w @ cov @ w.T)**0.5
    return float(num / den) if den > 0 else 0.0
