from flask import Flask, render_template, jsonify, request
from data_collector import get_bitget_klines as get_binance_klines, get_top_usdt_symbols, get_recent_closes, get_price_change
from spoiler_signals import analyze_signals, calculate_signal_score
import plotly.graph_objs as go
import plotly
import pandas as pd
import json
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/signals')
def all_signals_view():
    return render_template("signals.html")

@app.route('/ranking')
def ranking_page():
    return render_template("ranking.html")

@app.route('/stats')
def stats_page():
    return render_template("stats.html")

@app.route('/api/signal')
def get_signal():
    df = get_binance_klines(symbol='BTCUSDT')
    if df.empty or 'volume' not in df.columns:
        return jsonify({'signal': '❌ Không có dữ liệu', 'chart': {}})

    df_signals = analyze_signals(df)
    latest = df_signals.iloc[-1]
    signal = latest['signal_label'] if pd.notna(latest['signal_label']) else 'None'

    trace_candle = go.Candlestick(
        x=df_signals.index,
        open=df_signals['open'], high=df_signals['high'],
        low=df_signals['low'], close=df_signals['close'], name='Candles')
    markers = df_signals[df_signals['signal_label'].notna()]
    trace_signals = go.Scatter(
        x=markers.index, y=markers['close'], mode='markers+text',
        marker=dict(size=10, color='red'),
        text=markers['signal_label'], textposition='top center', name='Signals')
    layout = go.Layout(title='Spoiler Signals Chart')
    fig = go.Figure(data=[trace_candle, trace_signals], layout=layout)
    chart_json = json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

    return jsonify({'signal': signal, 'chart': chart_json})

@app.route('/api/all_signals')
def all_signals_api():
    if not os.path.exists("signals.log"):
        return jsonify([])
    with open("signals.log", encoding="utf-8") as f:
        lines = f.readlines()

    data = []
    for line in lines[-200:][::-1]:
        parts = line.strip().split(",")
        if len(parts) >= 8:
            symbol, signal, time, entry, tp1, tp2, sl, score = parts
            change = get_price_change(symbol)
            data.append({
                "symbol": symbol,
                "signal": signal,
                "time": time,
                "change": round(float(change), 2),
                "entry": float(entry),
                "tp1": float(tp1),
                "tp2": float(tp2),
                "sl": float(sl),
                "score": int(score)
            })
    return jsonify(data)

@app.route('/delete_log', methods=['POST'])
def delete_log():
    if os.path.exists("signals.log"):
        os.remove("signals.log")
    return jsonify({"success": True})

@app.route('/api/sparkline/<symbol>')
def get_sparkline(symbol):
    try:
        prices = get_recent_closes(symbol)
        return jsonify(prices)
    except:
        return jsonify([])

@app.route('/api/detail_chart/<symbol>')
def detail_chart(symbol):
    df = get_binance_klines(symbol)
    if df.empty or 'volume' not in df.columns:
        return jsonify({'error': 'Không có dữ liệu hoặc symbol không hợp lệ'})

    try:
        df_signals = analyze_signals(df)
        markers = df_signals[df_signals['signal_label'].notna()]
        candle = go.Candlestick(
            x=df.index,
            open=df['open'], high=df['high'],
            low=df['low'], close=df['close'], name="Candles")
        signal_marks = go.Scatter(
            x=markers.index, y=markers['close'], mode="markers+text",
            text=markers['signal_label'], textposition="top center",
            marker=dict(size=10, color='red'), name="Signals")
        layout = go.Layout(title=f"{symbol} Chart")
        fig = go.Figure(data=[candle, signal_marks], layout=layout)
        return jsonify(json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)))
    except Exception as e:
        return jsonify({'error': f'Xử lý lỗi: {str(e)}'})

@app.route('/api/ranking_data')
def get_ranking_data():
    symbols = get_top_usdt_symbols(limit=100)
    near_breakout = []
    top_gainers = []

    for symbol in symbols:
        try:
            df = get_binance_klines(symbol)
            if df.empty or 'volume' not in df.columns:
                continue
            df_signal = analyze_signals(df)
            latest = df_signal.iloc[-1]
            change = get_price_change(symbol)
            if latest.get('near_breakout', False):
                near_breakout.append({
                    "symbol": symbol,
                    "osc": round(latest['osc'], 2),
                    "time": latest.name.strftime('%Y-%m-%d %H:%M'),
                    "change": round(change, 2)
                })
            top_gainers.append({"symbol": symbol, "change": round(change, 2)})
        except:
            continue

    top_gainers_sorted = sorted(top_gainers, key=lambda x: x['change'], reverse=True)[:10]
    return jsonify({"breakouts": near_breakout, "gainers": top_gainers_sorted})

@app.route('/api/pnl_stats')
def pnl_stats():
    if not os.path.exists("pnl.log"):
        return jsonify({"win": 0, "loss": 0, "total": 0, "by_date": []})
    with open("pnl.log", encoding="utf-8") as f:
        lines = f.readlines()

    win, loss = 0, 0
    pnl_by_date = {}

    for line in lines:
        parts = line.strip().split(",")
        if len(parts) != 4:
            continue
        symbol, time_str, result, price = parts
        date = time_str.split()[0]
        if result.startswith("TP"):
            win += 1
            pnl_by_date[date] = pnl_by_date.get(date, 0) + 1
        elif result == "SL":
            loss += 1
            pnl_by_date[date] = pnl_by_date.get(date, 0) - 1

    data = [{"date": k, "pnl": v} for k, v in sorted(pnl_by_date.items())]
    return jsonify({"win": win, "loss": loss, "total": win + loss, "by_date": data})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
