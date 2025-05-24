from data_collector import get_coingecko_klines as get_klines, get_top_usdt_symbols
from spoiler_signals import analyze_signals, calculate_signal_score
from datetime import datetime
import os
import requests
from dotenv import load_dotenv

load_dotenv()

LOG_FILE = "signals.log"
SENT_FILE = "sent_signals.txt"
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram: {e}")

def save_signal(symbol, signal_type, entry, tp1, tp2, sl, score):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{symbol},{signal_type},{time_str},{entry},{tp1},{tp2},{sl},{score}"
    print("🟢", line)

    # Lưu vào log chính
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    # Gửi Telegram nếu chưa gửi
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, encoding="utf-8") as f:
            sent_lines = set(f.read().splitlines())
    else:
        sent_lines = set()

    if line not in sent_lines:
        msg = (
            f"🚨 *Tín hiệu mới: {symbol}*\n"
            f"Loại: `{signal_type}`\n"
            f"Entry: `{entry}`\nTP1: `{tp1}` | TP2: `{tp2}`\nSL: `{sl}`"
        )
        send_telegram(msg)
        with open(SENT_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")

def scan_top_100_and_log():
    symbols = get_top_usdt_symbols(limit=100)
    for symbol in symbols:
        df = get_klines(symbol)
        if df.empty or 'volume' not in df.columns:
            continue

        df_signal = analyze_signals(df)
        latest = df_signal.iloc[-1]
        label = latest.get("signal_label")
        if not label or label == 'nan':
            continue

        entry = round(float(latest["close"]), 6)
        sl = round(float(latest["low"] if "Sell" in label else latest["high"]), 6)
        tp1 = round(entry * 1.01 if "Buy" in label or "Long" in label else entry * 0.99, 6)
        tp2 = round(entry * 1.02 if "Buy" in label or "Long" in label else entry * 0.98, 6)
        score = calculate_signal_score(df_signal)

        save_signal(symbol, label, entry, tp1, tp2, sl, score)

if __name__ == "__main__":
    scan_top_100_and_log()
