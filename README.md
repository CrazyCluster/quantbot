Quantbot-AI v3 — Dynamic Watchlist + Optuna + Weekly Rebalance (70/30)
====================================================================

Overview:
- Weekly automatic selection of top Growth & Defensive stocks from combined static + dynamic watchlists
- Weekly Optuna optimization (parameter tuning) performed before trading
- Weekly rebalancing to 70% Growth / 30% Defensive
- Paper trading by default; safe caps and daily-loss circuit-breaker included
- Weekly email report with selection, trades and performance chart

Quick start:
1) Unzip project and create a .env from .env.template with your keys and settings.
2) Install dependencies:
   pip install -r requirements.txt
3) Run locally:
   python main.py
4) Trigger endpoints (with header X-Invoke-Token or ?token=...):
   - /auto_select_rebalance  (select + optimize + rebalance)
   - /rebalance  (rebalance using last selection)
   - /optimize  (run Optuna)
   - /report (send email report)

Important:
- Test thoroughly in TRADING_MODE=paper before switching to live.
- Do not commit your real .env to any public repository.
