import requests
import pandas as pd
import time
import os
import json
from datetime import datetime, timedelta

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
CACHE_FILE = "symbol_map.json"
symbol_to_id = {}

CACHE_EXPIRE_HOURS = 24

def is_cache_expired():
    if not os.path.exists(CACHE_FILE):
        return True
    modified = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
    return datetime.now() - modified > timedelta(hours=CACHE_EXPIRE_HOURS)

def update_symbol_map():
    global symbol_to_id
    if not is_cache_expired():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            symbol_to_id = json.load(f)
            print(f"✅ Tải symbol map từ cache ({len(symbol_to_id)} cặp)")
            return

    try:
        res = requests.get(f"{COINGECKO_BASE}/coins/list")
        coins = res.json()
        for coin in coins:
            symbol = coin['symbol'].upper() + 'USDT'
            symbol_to_id[symbol] = coin['id']
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(symbol_to_id, f)
        print(f"✅ Đã cập nhật {len(symbol_to_id)} symbol → id từ Coingecko")
    except Exception as e:
        print(f"❌ Lỗi cập nhật symbol map: {e}")

update_symbol_map()

def get_coingecko_klines(symbol, days=3):
    coin_id = symbol_to_id.get(symbol.upper())
    if not coin_id:
        print(f"⚠️ Không có ID cho symbol: {symbol}")
        return pd.DataFrame()

    url = f"{COINGECKO_BASE}/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": "hourly"}
    try:
        res = requests.get(url, params=params)
        data = res.json()
        prices = data.get("prices", [])
        volumes = data.get("total_volumes", [])

        if not prices or not volumes:
            return pd.DataFrame()

        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["volume"] = [v[1] for v in volumes]
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        df["close"] = df["price"]
        df["open"] = df["price"].shift(1).fillna(method="bfill")
        df["high"] = df[["open", "close"]].max(axis=1)
        df["low"] = df[["open", "close"]].min(axis=1)
        return df[["open", "high", "low", "close", "volume"]]

    except Exception as e:
        print(f"❌ Lỗi lấy dữ liệu từ Coingecko: {e}")
        return pd.DataFrame()

def get_price_change(symbol):
    df = get_coingecko_klines(symbol, days=1)
    if df.empty:
        return 0
    return (df.close.iloc[-1] - df.close.iloc[0]) / df.close.iloc[0] * 100

def get_recent_closes(symbol, n=20):
    df = get_coingecko_klines(symbol, days=1)
    if df.empty:
        return []
    return df["close"].tail(n).tolist()

def get_top_usdt_symbols(limit=20):
    return list(symbol_to_id.keys())[:limit]
