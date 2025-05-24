import requests
import pandas as pd

def get_binance_klines(symbol='BTCUSDT', interval='1h', limit=200):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'num_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df.astype(float)
    return df[['open', 'high', 'low', 'close', 'volume']]

def get_top_usdt_symbols(limit=100):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    all_tickers = requests.get(url).json()
    usdt_pairs = [t for t in all_tickers if t["symbol"].endswith("USDT") and not t["symbol"].endswith("BUSD")]
    usdt_pairs = sorted(usdt_pairs, key=lambda x: float(x["quoteVolume"]), reverse=True)
    symbols = [item["symbol"] for item in usdt_pairs[:limit]]
    return symbols

def get_recent_closes(symbol='BTCUSDT', limit=30):
    df = get_binance_klines(symbol=symbol, interval='1h', limit=limit)
    return df['close'].tolist()
