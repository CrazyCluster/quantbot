# email_report.py (weekly report with performance chart)
import os
import smtplib
import ssl
import matplotlib.pyplot as plt
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from alpaca_client import get_alpaca_client, get_account

def generate_performance_chart(trades_file="trades_live.csv", output_file="performance_live.png"):
    if not os.path.exists(trades_file):
        return None
    df = pd.read_csv(trades_file)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.sort_values("timestamp", inplace=True)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    # simplistic PnL calc: assume 'sell' entries add pnl, 'buy' subtract
    df["pnl"] = df.apply(lambda r: r["qty"]*r["price"] * (1 if r["side"]=="sell" else -1), axis=1)
    df["equity"] = df["pnl"].cumsum() + 10000
    plt.figure(figsize=(10,5))
    plt.plot(df["timestamp"], df["equity"], label="Equity Curve", linewidth=2)
    plt.title("QuantBot Live Performance (Paper Simulation)")
    plt.xlabel("Datum")
    plt.ylabel("Kontostand (USD)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    return output_file

def send_weekly_email():
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER", "webertimo802@gmail.com")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))

    api = get_alpaca_client()
    account = get_account(api)

    equity = getattr(account, "equity", "N/A")
    cash = getattr(account, "cash", "N/A")
    buying_power = getattr(account, "buying_power", "N/A")

    chart_file = generate_performance_chart()

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = f"QuantBot Live Wochenbericht – {datetime.utcnow().strftime('%Y-%m-%d')}"

    text = f"""Hallo,

Dies ist der wöchentliche Live-Bericht (Paper-safety mode recommended).

Equity: {equity}
Cash: {cash}
Buying Power: {buying_power}

Gruß,
QuantBot
"""
    msg.attach(MIMEText(text, "plain"))

    if chart_file and os.path.exists(chart_file):
        with open(chart_file, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(chart_file))
        part["Content-Disposition"] = f'attachment; filename="{os.path.basename(chart_file)}"'
        msg.attach(part)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        print("Weekly report sent.")
    except Exception as e:
        print("Error sending email:", e)
