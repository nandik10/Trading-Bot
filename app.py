import os, csv
import plotly.graph_objects as go
from flask import Flask, render_template, request
from patterns import patterns
from symbols import symbols
from connectors.binance_futures import BinanceFuturesClient
import talib
import pandas as pd

app = Flask(__name__)
app.debug = True


@app.route("/", methods=['GET', 'POST'])
def index():
    current_pattern = request.args.get('pattern', None)
    symbols = {}

    with open('datasets/symbols.csv') as f:
        for row in csv.reader(f):
            symbols[row[0]] = {'name': row[1]}

    # print(symbols)

    if current_pattern:
        datafiles = os.listdir('datasets/daily')
        for filename in datafiles:
            df = pd.read_csv('datasets/daily/{}'.format(filename))
            # print(df)
            pattern_func = getattr(talib, current_pattern)

            symbol = filename.split('.')[0]

            try:
                result = pattern_func(df['open'], df['high'], df['low'], df['close'])
                last = result.tail(1).values[0]
                # print(last)
                if last > 0:
                    symbols[symbol][current_pattern] = 'bullish'
                    fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                                                         open=df['open'],
                                                         high=df['high'],
                                                         low=df['low'],
                                                         close=df['close'])])
                    fig.update_layout(xaxis_rangeslider_visible=False)
                    fig.write_image("static/{}.png".format(symbol))
                elif last < 0:
                    symbols[symbol][current_pattern] = 'bearish'
                    fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                                    open=df['open'],
                                    high=df['high'],
                                    low=df['low'],
                                    close=df['close'])])
                    fig.update_layout(xaxis_rangeslider_visible=False)
                    fig.write_image("static/{}.png".format(symbol))

                else:
                    symbols[symbol][current_pattern] = None
                    # print("{} triggered {}".format(filename,pattern))
            except:
                pass
    return render_template('index.html', patterns=patterns, symbols=symbols, current_pattern=current_pattern)


@app.route("/snapshot")
def snapshot():
    binance = BinanceFuturesClient("30e920298bb4ebe0b091a5229752673e6444219f2f3b22c8b064f4e44a800fd9",
                                   "e8184bc042c0a35afb2cfcb0fa90a039aff82ea6dac6a0e837cd270e59bbcecb", True)
    contracts = binance.get_contracts()
    # list = []
    # for contract in contracts:
    #     format = "{fst},{sec}".format(fst=contract, sec=contract)
    #     # print(format)
    #     list.append(format)
    #
    # smp = pd.DataFrame(list)
    # smp.to_csv('datasets/symbols.csv', index=False)

    with open('datasets/symbols.csv') as f:
        symbols = f.read().splitlines()
        for symbol in symbols:
            sym = symbol.split(',')[0]
            candles = binance.get_historical_candles(contracts[sym], '1d')
            bars = []

            for can in candles:
                ts = int(can.timestamp)
                date = pd.to_datetime(ts, unit='ms')
                bar = [date, can.open, can.high, can.low, can.close, can.volume]
                bars.append(bar)

            df = pd.DataFrame(bars, columns=['Date', 'open', 'high', 'low', 'close', 'volume'])
            df.to_csv('datasets/daily/{}.csv'.format(sym), index=False)
    return {
        'code': 'success'
    }

@app.route("/reverse")
def reverse():
    current_symbol = request.args.get('pattern', None)
    results = {}
    if current_symbol:
        df = pd.read_csv('datasets/daily/{}.csv'.format(current_symbol))
        for pattern in patterns:
            pattern_func = getattr(talib, pattern)
            result = pattern_func(df['open'], df['high'], df['low'], df['close'])
            last = result.tail(1).values[0]
            if last != 0:
                if last > 0:
                    results[pattern] = 'bullish'
                    fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                                                         open=df['open'],
                                                         high=df['high'],
                                                         low=df['low'],
                                                         close=df['close'])])
                    fig.update_layout(xaxis_rangeslider_visible=False)
                    fig.write_image("static/{}.png".format(current_symbol))
                else:
                    results[pattern] = 'bearish'
                    fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                                                         open=df['open'],
                                                         high=df['high'],
                                                         low=df['low'],
                                                         close=df['close'])])
                    fig.update_layout(xaxis_rangeslider_visible=False)
                    fig.write_image("static/{}.png".format(current_symbol))

    return render_template('symbols.html', symbols=symbols, results=results, patterns=patterns, current_symbol=current_symbol)

if __name__ == '__main__':
    app.run()