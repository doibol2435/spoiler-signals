import time
import subprocess
from datetime import datetime

def run_every(minutes=5):
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"🟢 [{now}] Đang quét tín hiệu mới...")
        subprocess.call(["python", "scan_all.py"])
        time.sleep(minutes * 60)

if __name__ == "__main__":
    run_every(5)  # quét mỗi 5 phút
