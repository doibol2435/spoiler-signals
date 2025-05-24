import time
import subprocess
import os
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_alert(message):
    if BOT_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": CHAT_ID, "text": f"🚨 [Auto Run] {message}"})
        except Exception as e:
            print(f"❌ Lỗi gửi Telegram: {e}")

def log(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full = f"[{now}] {message}"
    print(full)
    with open("auto_run.log", "a", encoding="utf-8") as f:
        f.write(full + "\n")

def run_every(minutes=5):
    while True:
        try:
            log("🔄 Đang chạy scan_all.py ...")
            subprocess.check_call(["python", "scan_all.py"])
            log("✅ Hoàn thành scan_all.py\n")
        except Exception as e:
            log(f"❌ Lỗi: {e}")
            send_telegram_alert(f"Lỗi khi chạy scan_all.py: {e}")
        time.sleep(minutes * 60)

if __name__ == "__main__":
    run_every(5)
