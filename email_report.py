import os, pandas as pd, matplotlib.pyplot as plt
from datetime import datetime
from alpaca_client import get_alpaca_client, get_account

def generate_chart(trade_log='rebalance_trades_v3.json', out='performance_v3.png'):
    try:
        df = pd.read_json(trade_log)
    except Exception:
        return None
    if df.empty:
        return None
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    df['sign'] = df['side'].apply(lambda x: 1 if x=='sell' else -1)
    df['value'] = df['qty']*df['price']*df['sign']
    df['equity'] = df['value'].cumsum() + 10000
    plt.figure(figsize=(8,4))
    plt.plot(df['timestamp'], df['equity'], label='Equity')
    plt.title('QuantBot Equity (simplified)')
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return out

def send_weekly_report():
    sender = os.getenv('EMAIL_SENDER')
    pwd = os.getenv('EMAIL_PASSWORD')
    recv = os.getenv('EMAIL_RECEIVER', 'webertimo802@gmail.com')
    smtp = os.getenv('SMTP_SERVER','smtp.gmail.com')
    port = int(os.getenv('SMTP_PORT','465'))

    api = get_alpaca_client()
    acc = get_account(api)

    chart = generate_chart()

    import smtplib, ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.application import MIMEApplication

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recv
    msg['Subject'] = f"QuantBot v3 Weekly Report - {datetime.utcnow().date()}"
    body = f"Equity: {getattr(acc,'equity', 'N/A')}\nCash: {getattr(acc,'cash','N/A')}\nBuying Power: {getattr(acc,'buying_power','N/A')}"
    msg.attach(MIMEText(body,'plain'))

    if chart and os.path.exists(chart):
        with open(chart,'rb') as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(chart))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(chart)}"'
        msg.attach(part)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp, port, context=context) as server:
            server.login(sender, pwd)
            server.sendmail(sender, recv, msg.as_string())
        print('Email sent')
    except Exception as e:
        print('Email error', e)
