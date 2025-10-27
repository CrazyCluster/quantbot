# logger_util.py
import csv
import os
from datetime import datetime

LOGFILE = "trades_live.csv"
HEADERS = ["timestamp","symbol","side","qty","price","order_id","status","mode","notes"]

def append_trade(row: dict):
    exists = os.path.exists(LOGFILE)
    with open(LOGFILE, "a", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        if not exists:
            writer.writeheader()
        row2 = {k: row.get(k,"") for k in HEADERS}
        writer.writerow(row2)

def trades_today_count():
    if not os.path.exists(LOGFILE):
        return 0
    today = datetime.utcnow().date()
    c = 0
    with open(LOGFILE, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            ts = datetime.fromisoformat(r["timestamp"])
            if ts.date() == today:
                c += 1
    return c
