quantbot-ai-live — Alpaca Live Trading example (conservative, safety-first)

IMPORTANT: This repository is a template for live trading. DO NOT run live trading until you fully reviewed and tested on paper.

Quick start:
1) Copy files to a new Git repository.
2) Create a .env from .env.template and fill your Alpaca LIVE API keys and email app password.
3) Install dependencies:
   pip install -r requirements.txt
4) Run locally in TEST mode (paper) first — set TRADING_MODE=paper in .env
   python main.py
   # then in another terminal:
   curl -X POST http://127.0.0.1:10000/run -H "X-Invoke-Token: <INVOKE_SECRET>"

Deployment:
- Push to GitHub and deploy to Render or Replit.
- Set environment variables in the hosting service.
- Schedule cron-job.org or Render Cron to call https://<your-service>/run weekly with header X-Invoke-Token.

SAFETY: This template includes caps:
- MAX_POSITION_PCT (max 20% capital per position)
- MAX_DAILY_LOSS (stop trading for the day after 2% loss)
- MAX_DAILY_TRADES (cap trades per day)
- TRADING_MODE must be 'live' to actually place live orders.
