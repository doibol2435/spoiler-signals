import time
import subprocess

def run_every(minutes=5):
    while True:
        print("🔄 Đang kiểm tra TP/SL...")
        subprocess.call(["python", "check_targets.py"])
        time.sleep(minutes * 60)

if __name__ == "__main__":
    run_every(1)
# Chạy kiểm tra TP/SL mỗi 1 phút