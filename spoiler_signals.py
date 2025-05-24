import pandas as pd
import numpy as np

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def find_pivots(df, left=20, right=20):
    highs, lows = [], []
    for i in range(left, len(df) - right):
        high_pivot = df['high'][i-left:i+right+1].max() == df['high'][i]
        low_pivot = df['low'][i-left:i+right+1].min() == df['low'][i]
        highs.append(high_pivot)
        lows.append(low_pivot)
    return [False]*left + highs + [False]*right, [False]*left + lows + [False]*right

def analyze_signals(df):
    df = df.copy()
    df['ema5_vol'] = ema(df['volume'], 5)
    df['ema10_vol'] = ema(df['volume'], 10)
    df['osc'] = 100 * (df['ema5_vol'] - df['ema10_vol']) / df['ema10_vol']

    # RSI for scoring
    delta = df['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

    piv_highs, piv_lows = find_pivots(df)
    df['piv_high'] = piv_highs
    df['piv_low'] = piv_lows

    df['high_pivot_val'] = df['high'].where(df['piv_high']).ffill()
    df['low_pivot_val'] = df['low'].where(df['piv_low']).ffill()

    df['resistance_break'] = (df['close'] > df['high_pivot_val']) & (df['osc'] > 20)
    df['support_break'] = (df['close'] < df['low_pivot_val']) & (df['osc'] > 20)
    df['false_breakout_support'] = (df['close'] > df['low_pivot_val']) & (df['open'] < df['low_pivot_val']) & (df['osc'] <= 20)
    df['false_breakout_resistance'] = (df['close'] < df['high_pivot_val']) & (df['open'] > df['high_pivot_val']) & (df['osc'] <= 20)

    df['long_signal'] = df['piv_low'] & (df['close'] > df['low_pivot_val']) & (df['close'].shift(1) < df['low_pivot_val'])
    df['short_signal'] = df['piv_high'] & (df['close'] < df['high_pivot_val']) & (df['close'].shift(1) > df['high_pivot_val'])

    df['near_resistance'] = (df['high_pivot_val'] - df['close']) / df['high_pivot_val'] < 0.01
    df['near_support'] = (df['close'] - df['low_pivot_val']) / df['low_pivot_val'] < 0.01
    df['volume_surge'] = df['osc'] > 10
    df['near_breakout'] = (df['near_resistance'] | df['near_support']) & df['volume_surge']

    df['signal_label'] = np.nan
    df.loc[df['long_signal'], 'signal_label'] = 'Long'
    df.loc[df['short_signal'], 'signal_label'] = 'Short'
    df.loc[df['resistance_break'], 'signal_label'] = 'Buy Breakout'
    df.loc[df['support_break'], 'signal_label'] = 'Sell Breakout'
    df.loc[df['false_breakout_support'], 'signal_label'] = 'False Long'
    df.loc[df['false_breakout_resistance'], 'signal_label'] = 'False Short'

    return df

def calculate_signal_score(df):
    latest = df.iloc[-1]
    score = 0
    if latest['osc'] > 20: score += 2
    if latest['volume'] > df['volume'].rolling(20).mean().iloc[-1] * 1.5: score += 2
    if latest['close'] > df['close'].ewm(span=50).mean().iloc[-1]: score += 2  # EMA trend
    if 'rsi' in df.columns and 40 < latest['rsi'] < 70: score += 1
    if abs(latest['close'] - latest['open']) > (latest['high'] - latest['low']) * 0.6: score += 1  # thân nến mạnh
    return score
