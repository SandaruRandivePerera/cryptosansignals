import ccxt
import time
import pandas as pd
import requests

# --- CONFIGURATION ---
binance_api_key = '1e3LDKUNOu7zHzkNKskLS1zBfEMWESTqylhmkQuV97fsp47CIPGljDmFM8b8Hn1X'  # replace with your key
binance_api_secret = 'yHRFo3GJo0dRtZEqCL3KuIAE3HbVDwxlAaG8jD2iWmJzkETlIV6PMxXTFFPfKfPx'  # replace with your secret
telegram_bot_token = '7288688451:AAGP53RhtHzLR4J3tJL-E8fjAGjrq5wrtI4'  # replace with your bot token
telegram_chat_id = '6684685749'  # replace with your chat id

symbols = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT',
    'XRPUSDT', 'DOGEUSDT', 'MATICUSDT', 'LTCUSDT', 'LINKUSDT'
]

rsi_period = 14
rsi_overbought = 70
rsi_oversold = 30
timeframe = '5m'
higher_timeframe = '15m'  # added for better accuracy

# --- CONNECT BINANCE ---
exchange = ccxt.binance({
    'apiKey': binance_api_key,
    'secret': binance_api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

# --- FUNCTIONS ---

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    payload = {
        'chat_id': telegram_chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def ta_rsi(series, period):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_signal(symbol):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=rsi_period+2)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['rsi'] = ta_rsi(df['close'], rsi_period)
        last_rsi = df['rsi'].iloc[-1]
        return last_rsi
    except Exception as e:
        print(f"Signal Error {symbol}: {e}")
        return None

def get_higher_tf_rsi(symbol):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=higher_timeframe, limit=rsi_period+2)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['rsi'] = ta_rsi(df['close'], rsi_period)
        last_rsi = df['rsi'].iloc[-1]
        return last_rsi
    except Exception as e:
        print(f"Higher TF Error {symbol}: {e}")
        return None

def calculate_entry_targets(price, signal_type):
    if signal_type == "BUY":
        entry = price
        stop_loss = price * 0.99
        tp1 = price * 1.003
        tp2 = price * 1.006
        tp3 = price * 1.01
    else:  # SELL
        entry = price
        stop_loss = price * 1.01
        tp1 = price * 0.997
        tp2 = price * 0.994
        tp3 = price * 0.99
    return entry, stop_loss, [tp1, tp2, tp3]

# --- START BOT ---

print("✅ Bot Started OK! Listening for 100% filtered sniper signals...")

while True:
    for symbol in symbols:
        rsi = get_signal(symbol)
        higher_tf_rsi = get_higher_tf_rsi(symbol)

        if rsi is None or higher_tf_rsi is None:
            continue

        if rsi < rsi_oversold and higher_tf_rsi < rsi_oversold:
            signal = "BUY"
        elif rsi > rsi_overbought and higher_tf_rsi > rsi_overbought:
            signal = "SELL"
        else:
            continue

        price = exchange.fetch_ticker(symbol)['last']
        entry, stop_loss, targets = calculate_entry_targets(price, signal)

        message = (
            f"🚀 <b>Signal:</b> {signal}\n"
            f"<b>Pair:</b> {symbol}\n"
            f"<b>Entry:</b> {entry:.2f}\n"
            f"<b>Stop Loss:</b> {stop_loss:.2f}\n"
            f"🎯 <b>Targets:</b>\n"
            f"- TP1: {targets[0]:.2f}\n"
            f"- TP2: {targets[1]:.2f}\n"
            f"- TP3: {targets[2]:.2f}\n"
            f"<b>Timeframe:</b> {timeframe}\n"
            f"<b>Strategy:</b> RSI"
        )

        print(message)
        send_telegram_message(message)

    time.sleep(60)  # wait 1 minute and check again
