import pandas as pd
import requests
import os
import json
from dotenv import load_dotenv
from data_collector import get_recent_closes

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
LOG_FILE = "signals.log"
STATUS_FILE = "status.log"
PNL_FILE = "pnl.log"

def send_telegram_message(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ BOT_TOKEN hoặc CHAT_ID thiếu")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def get_current_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        data = requests.get(url).json()
        return float(data["price"])
    except:
        return None

def load_status():
    if not os.path.exists(STATUS_FILE):
        return set()
    with open(STATUS_FILE, encoding="utf-8") as f:
        return set(f.read().splitlines())

def save_status(status_set):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(status_set))

def log_pnl(symbol, time, result, price):
    with open(PNL_FILE, "a", encoding="utf-8") as f:
        f.write(f"{symbol},{time},{result},{price:.4f}\n")

def get_chart_image_url(symbol):
    prices = get_recent_closes(symbol)
    labels = list(range(len(prices)))
    chart_url = (
        "https://quickchart.io/chart?c="
        + json.dumps({
            "type": "line",
            "data": {"labels": labels, "datasets": [{"label": symbol, "data": prices}]}
        })
    )
    return chart_url

def check_targets():
    if not os.path.exists(LOG_FILE):
        print("Không tìm thấy signals.log")
        return

    df = pd.read_csv(LOG_FILE, header=None, names=["symbol", "signal", "time", "entry", "tp1", "tp2", "sl"])
    status_set = load_status()

    for _, row in df.iterrows():
        key = f"{row['symbol']}|{row['time']}"
        if key in status_set:
            continue

        price = get_current_price(row['symbol'])
        if price is None:
            continue

        if row['signal'] in ['Long', 'Buy Breakout', 'False Long']:
            if price >= row['tp2']:
                send_telegram_message(f"🎯 {row['symbol']} đạt TP2 ({price:.4f})\n{get_chart_image_url(row['symbol'])}")
                log_pnl(row['symbol'], row['time'], "TP2", price)
                status_set.add(key)
            elif price >= row['tp1']:
                send_telegram_message(f"✅ {row['symbol']} đạt TP1 ({price:.4f})")
                log_pnl(row['symbol'], row['time'], "TP1", price)
                status_set.add(key)
            elif price <= row['sl']:
                send_telegram_message(f"🛑 {row['symbol']} dừng lỗ SL ({price:.4f})")
                log_pnl(row['symbol'], row['time'], "SL", price)
                status_set.add(key)

        elif row['signal'] in ['Short', 'Sell Breakout', 'False Short']:
            if price <= row['tp2']:
                send_telegram_message(f"🎯 {row['symbol']} (SHORT) đạt TP2 ({price:.4f})\n{get_chart_image_url(row['symbol'])}")
                log_pnl(row['symbol'], row['time'], "TP2", price)
                status_set.add(key)
            elif price <= row['tp1']:
                send_telegram_message(f"✅ {row['symbol']} (SHORT) đạt TP1 ({price:.4f})")
                log_pnl(row['symbol'], row['time'], "TP1", price)
                status_set.add(key)
            elif price >= row['sl']:
                send_telegram_message(f"🛑 {row['symbol']} (SHORT) bị SL ({price:.4f})")
                log_pnl(row['symbol'], row['time'], "SL", price)
                status_set.add(key)

    save_status(status_set)

if __name__ == '__main__':
    check_targets()
