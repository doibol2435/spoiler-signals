import time
import subprocess
from datetime import datetime

def run_every(minutes=5):
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"🟠 [{now}] Đang kiểm tra TP/SL...")
        subprocess.call(["python", "check_targets.py"])
        time.sleep(minutes * 60)

if __name__ == "__main__":
    run_every(5)  # kiểm tra mỗi 5 phút
