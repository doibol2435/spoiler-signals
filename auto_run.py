import time
import subprocess
import os
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

LOG_FILE = "auto_run.log"
SIGNAL_FILE = "signals.log"
SENT_TRACK_FILE = "sent_signals.txt"


def send_telegram_alert(message):
    if BOT_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"❌ Lỗi gửi Telegram: {e}")


def log(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full = f"[{now}] {message}"
    print(full)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full + "\n")


def delete_old_logs():
    if os.path.exists(LOG_FILE):
        modified_time = datetime.fromtimestamp(os.path.getmtime(LOG_FILE))
        if datetime.now() - modified_time > timedelta(days=7):
            os.remove(LOG_FILE)
            log("🗑️ Đã xóa auto_run.log cũ hơn 7 ngày")


def send_new_signals():
    if not os.path.exists(SIGNAL_FILE):
        return
    if os.path.exists(SENT_TRACK_FILE):
        with open(SENT_TRACK_FILE, encoding="utf-8") as f:
            sent_lines = set(f.read().splitlines())
    else:
        sent_lines = set()

    with open(SIGNAL_FILE, encoding="utf-8") as f:
        lines = f.readlines()

    new_sent = []
    for line in lines:
        line = line.strip()
        if line in sent_lines:
            continue
        parts = line.split(",")
        if len(parts) >= 8:
            symbol, signal, time_str, entry, tp1, tp2, sl, score = parts
            msg = (
                f"🚨 *Tín hiệu mới: {symbol}*\n"
                f"Loại: {signal}\n"
                f"Thời gian: {time_str}\n"
                f"Entry: `{entry}`\nTP1: `{tp1}` | TP2: `{tp2}`\nSL: `{sl}`"
            )
            send_telegram_alert(msg)
            new_sent.append(line)

    if new_sent:
        with open(SENT_TRACK_FILE, "a", encoding="utf-8") as f:
            for line in new_sent:
                f.write(line + "\n")


def run_every(minutes=5):
    log("🚀 Bắt đầu worker auto_run.py")
    while True:
        try:
            delete_old_logs()
            log("🔄 Đang chạy scan_all.py ...")
            subprocess.check_call(["python", "scan_all.py"])
            log("✅ Hoàn thành scan_all.py")
            send_new_signals()
        except Exception as e:
            log(f"❌ Lỗi: {e}")
            send_telegram_alert(f"🚨 Lỗi khi chạy scan_all.py: {e}")
        time.sleep(minutes * 60)


if __name__ == "__main__":
    run_every(1)
