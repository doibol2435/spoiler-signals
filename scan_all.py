from data_collector import get_binance_klines, get_top_usdt_symbols
from spoiler_signals import analyze_signals, calculate_signal_score
import time
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import pytz

# Load .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
LOG_FILE = "signals.log"
TIMEZONE = pytz.timezone("Asia/Ho_Chi_Minh")  # UTC+7

def send_telegram_message(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Thiếu BOT_TOKEN hoặc CHAT_ID trong .env")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def scan_top_100_and_log():
    symbols = get_top_usdt_symbols(limit=400)
    results = []
    seen = set()

    for symbol in symbols:
        try:
            df = get_binance_klines(symbol=symbol)
            df_signal = analyze_signals(df)
            latest = df_signal.iloc[-1]
            signal = latest['signal_label']
            if signal and signal != 'None' and str(signal) != 'nan':
                now = datetime.now(TIMEZONE)
                timestamp = now.strftime('%Y-%m-%d %H:%M')
                day_key = f"{symbol}_{signal}_{now.date()}"
                if day_key in seen:
                    continue

                entry = round(latest['close'], 4)
                if 'Long' in signal or 'Buy' in signal:
                    tp1 = round(entry * 1.02, 4)
                    tp2 = round(entry * 1.04, 4)
                    sl = round(entry * 0.985, 4)
                else:
                    tp1 = round(entry * 0.98, 4)
                    tp2 = round(entry * 0.96, 4)
                    sl = round(entry * 1.015, 4)

                score = calculate_signal_score(df_signal)
                if score < 6:
                    continue

                results.append((symbol, signal, timestamp, entry, tp1, tp2, sl, score))

                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{symbol},{signal},{timestamp},{entry},{tp1},{tp2},{sl},{score}\n")

                print(f"✅ {symbol} ➜ {signal} ({timestamp}) | Entry: {entry} | TP1: {tp1} | SL: {sl} | Score: {score}")
                seen.add(day_key)

        except Exception as e:
            print(f"❌ {symbol} lỗi: {e}")
        time.sleep(0.1)

    if results:
        message = "📊 Tổng hợp tín hiệu Spoiler Signals:\n\n"
        for s, sig, t, entry, tp1, tp2, sl, score in results:
            message += (
                f"🟢 {s} ➜ {sig} ({t})\n"
                f"Entry: {entry}\n"
                f"TP1: {tp1} | TP2: {tp2} | SL: {sl}\n"
                f"🎯 Score: {score}/10\n\n"
            )
        send_telegram_message(message)

if __name__ == '__main__':
    scan_top_100_and_log()
