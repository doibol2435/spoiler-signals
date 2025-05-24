import time
import subprocess

def run_every(minutes):
    while True:
        print("▶ Đang kiểm tra tín hiệu 400 coin...")
        subprocess.call(["python", "scan_all.py"])
        print(f"⏳ Đợi {minutes} phút...")
        time.sleep(minutes * 60)

if __name__ == "__main__":
    run_every(5)  # kiểm tra mỗi 5 phút
