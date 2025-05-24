import requests
import pandas as pd

BASE_URL = "https://api.bitget.com"

def get_bitget_klines(symbol='BTCUSDT', interval='1H', limit=200):
    url = f"{BASE_URL}/api/spot/v1/market/candles"
    params = {
        "symbol": symbol.lower(),
        "period": interval,
        "limit": str(limit)
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("code") != "00000":
            print(f"❌ Bitget trả lỗi: {data}")
            return pd.DataFrame()

        df = pd.DataFrame(data["data"], columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = df.astype(float)
        return df[['open', 'high', 'low', 'close', 'volume']]
    except Exception as e:
        print(f"❌ Lỗi gọi Bitget KLINE cho {symbol}: {e}")
        return pd.DataFrame()

def get_top_usdt_symbols(limit=100):
    url = f"{BASE_URL}/api/spot/v1/market/tickers"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if data.get("code") != "00000":
            print(f"❌ Bitget trả lỗi ticker: {data}")
            return []
        tickers = data.get("data", [])
        filtered = [t for t in tickers if t["symbol"].endswith("usdt")]
        sorted_pairs = sorted(filtered, key=lambda x: float(x["quoteVol"]), reverse=True)
        symbols = [t["symbol"].upper() for t in sorted_pairs[:limit]]
        return symbols
    except Exception as e:
        print(f"❌ Lỗi lấy danh sách coin từ Bitget: {e}")
        return []

def get_recent_closes(symbol='BTCUSDT', limit=30):
    df = get_bitget_klines(symbol=symbol, interval='1H', limit=limit)
    if df.empty:
        return []
    return df['close'].tolist()

def get_price_change(symbol):
    url = f"{BASE_URL}/api/spot/v1/market/tickers"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if data.get("code") != "00000":
            return 0
        for item in data["data"]:
            if item["symbol"].upper() == symbol.upper():
                return float(item["change"])
    except:
        return 0
    return 0

# Gắn hàm chính với tên tương thích Binance
get_binance_klines = get_bitget_klines