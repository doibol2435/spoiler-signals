import requests
import pandas as pd

def get_binance_klines(symbol='BTCUSDT', interval='1h', limit=200):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if not isinstance(data, list):
            print(f"❌ Klines trả về lỗi cho {symbol}: {data}")
            return pd.DataFrame()
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'num_trades',
            'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = df.astype(float)
        return df[['open', 'high', 'low', 'close', 'volume']]
    except Exception as e:
        print(f"❌ Lỗi lấy dữ liệu KLINE cho {symbol}: {e}")
        return pd.DataFrame()

def get_top_usdt_symbols(limit=100):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        res = requests.get(url, timeout=10)
        all_tickers = res.json()

        if not isinstance(all_tickers, list):
            print("❌ Binance API trả về dữ liệu không hợp lệ:", all_tickers)
            return []

        usdt_pairs = [
            t for t in all_tickers
            if isinstance(t, dict)
            and t.get("symbol", "").endswith("USDT")
            and not t.get("symbol", "").endswith("BUSD")
        ]

        usdt_pairs = sorted(usdt_pairs, key=lambda x: float(x.get("quoteVolume", 0)), reverse=True)
        symbols = [item["symbol"] for item in usdt_pairs[:limit]]
        return symbols
    except Exception as e:
        print(f"❌ Lỗi lấy danh sách symbol: {e}")
        return []

def get_recent_closes(symbol='BTCUSDT', limit=30):
    df = get_binance_klines(symbol=symbol, interval='1h', limit=limit)
    if df.empty:
        return []
    return df['close'].tolist()
