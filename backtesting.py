import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
import numpy as np

np.seterr(divide='ignore', invalid='ignore')
from patterns import patterns
import talib

pd.options.mode.chained_assignment = None
import ta
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator, StochasticOscillator, AwesomeOscillatorIndicator
from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator
import time

import matplotlib
import matplotlib.pyplot as plt


# Strategy #1
# if 0 < df['ema200'] < df['close'][ind] < df['lw_band']: BUY
# if df['close'] >= init_price * (1 + tp) | df['close'] <= init_price * (1 - sl): SELL

def BolingerBands_Ema200(binance, take_profit, stop_loss):
    # tic = time.perf_counter()
    contracts = binance.get_contracts()

    result_df = pd.DataFrame()

    effectiveness = []

    timeframes = ["1m", "5m", "1h", "1d"]
    o_w = 0
    o_l = 0

    for timef in timeframes:
        wins = 0
        loses = 0
        for contract in contracts:
            candles = binance.get_historical_candles(contracts[contract], timef)
            bars = []

            for can in candles:
                bar = [can.timestamp, can.open, can.high, can.low, can.close, can.volume]
                bars.append(bar)

            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # BollingerBands

            indicator_bb = BollingerBands(df['close'])
            df['hg_band'] = indicator_bb.bollinger_hband()
            df['hg_band'] = df['hg_band'].fillna(0)
            df['lw_band'] = indicator_bb.bollinger_lband()
            df['lw_band'] = df['lw_band'].fillna(0)
            # EMA 200

            ema = EMAIndicator(df['close'], 200)
            df['ema200'] = ema.ema_indicator()
            df['ema200'] = df['ema200'].fillna(0)

            # Strategy

            buy = False
            #sl_values = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15]
            #tp_values = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1]

            tp = take_profit
            sl = stop_loss
            init_price = 0
            buy_time = 0
            fees = 0
            profit = 0
            result = []

            # Statistics

            symbol_profit = 0
            strategy_entries = 0

            # Patterns

            for i in range(len(df)):
                counter = 0
                input_values = []
                signal = ''
                current_values = [df.open.iloc[i], df.high.iloc[i], df.low.iloc[i], df.close.iloc[i]]
                input_values.append(current_values)
                if counter == 10:
                    counter = 0

                    input_df = pd.DataFrame(input_values, columns=['open', 'high', 'low', 'close'])

                    pattern_results = {}
                    for pattern in patterns:
                        pattern_func = getattr(talib, pattern)
                        pattern_result = pattern_func(input_df['open'], input_df['high'], input_df['low'],
                                                      input_df['close'])
                        last = pattern_result.tail(1).values[0]
                        if last != 0:
                            if last > 0:
                                pattern_results[pattern] = 'bullish'
                                # print(last)
                            else:
                                pattern_results[pattern] = 'bearish'
                                # print(last)
                    # print(pattern_results)
                    top6_patterns = ['CDL3BLACKCROWS', 'CDLDOJISTAR', 'CDLENGULFING', 'CDLEVENINGSTAR', 'CDLHAMMER',
                                     'CDLINVERTEDHAMMER']
                    bullish_score = 0
                    bearish_score = 0
                    for k, v in pattern_results.items():
                        if k in top6_patterns:
                            strength = 5
                        else:
                            strength = 1
                        if v == 'bullish':
                            bullish_score += strength
                        elif v == 'bearish':
                            bearish_score += strength

                    # print(bearish_score)
                    # print(bullish_score)
                    if bearish_score > 0 or bullish_score > 0:
                        signal = 'bearish' if bearish_score > bullish_score else 'bullish'
                    else:
                        signal = ''
                else:
                    counter += 1
                if df.lw_band.iloc[i] != 0 and buy == False:
                    if df.ema200.iloc[i] != 0 and df.ema200.iloc[i] < df.close.iloc[i] < df.lw_band.iloc[i]: #and (
                            #signal == 'bullish' or signal == '')
                        init_price = df.close.iloc[i]
                        fees = (init_price / 100) * 0.1
                        buy_time = df.timestamp.iloc[i]
                        buy = True
                elif df.lw_band.iloc[i] != 0 and buy == True:
                    if init_price > 0 and (
                            df.close.iloc[i] >= init_price * (1 + tp) or df.close.iloc[i] <= init_price * (1 - sl)):
                        temp_list = []
                        temp_list.append(contract)
                        temp_list.append(timef)
                        temp_list.append('Long')
                        date = pd.to_datetime(buy_time, unit='ms')
                        temp_list.append(date)
                        sell_date = pd.to_datetime(df.timestamp.iloc[i], unit='ms')
                        temp_list.append(sell_date)
                        temp_list.append(init_price)
                        temp_list.append(df.close.iloc[i])
                        fees = fees + (df.close.iloc[i] / 100) * 0.1
                        temp_list.append(fees)
                        profit = (((df.close.iloc[i] - fees) * 100) / init_price - 100) / 100
                        if profit > 0:
                            wins += 1
                        else:
                            loses += 1
                        symbol_profit += profit
                        strategy_entries += 1
                        # profit = e[4] - init_price / 100
                        effectiveness.append(profit)
                        temp_list.append(profit)
                        temp_list.append('')
                        # temp_list.append(df.lw_band.iloc[i])
                        result.append(temp_list)
                        buy = False
                else:
                    continue
            if strategy_entries > 0:
                effectiveness_per_timef = round(symbol_profit / strategy_entries, 4)
                result[-1][9] = effectiveness_per_timef
            result_df = result_df.append(
                pd.DataFrame(result,
                             columns=['Symbol', 'Timeframe', 'Signal', 'Buy Date', 'Sell Date', 'Original Value',
                                      'After value', 'Fees', 'Profit %', 'Effectiveness']),
                ignore_index=True)
        print(f'Wins on {timef}: ' + str(wins))
        print(f'Loses on {timef}: ' + str(loses))
        o_w += wins
        o_l += loses
        # print(result_df)
    eff = sum(effectiveness) / len(effectiveness)
    result_df['Overall_Effectiveness'] = ''
    result_df['Overall_Effectiveness'][0] = eff
    take_profit = str(take_profit)
    take_profit = take_profit.replace(".",",")
    stop_loss = str(stop_loss)
    stop_loss = stop_loss.replace(".", ",")
    file_name = f'backtest_results/without_patterns/BOLLINGERBANDS_EMA200_{take_profit}_{stop_loss}.xlsx'
    # print(file_name)
    result_df.to_excel(file_name)
    print('BoilingerBand done with take profit: ' + take_profit + ' stop loss: ' + stop_loss)
    print('Overall Wins : ' + str(o_w))
    print('Overall Losses : ' + str(o_l))

    # toc = time.perf_counter()
    # print(f'Done in {toc - tic:0.4f} seconds')


# Strategy #2
# close > 200 day MA
# Entry: 10 period RSI < 30
# Exit: 10 period RSI > 40 or 10 tf

def MA200_RSI(binance):
    # tic = time.perf_counter()
    contracts = binance.get_contracts()
    # contracts = ['BTCUSDT', 'ETHUSDT']

    result_df = pd.DataFrame()
    effectiveness = []

    timeframes = ["1m", "5m", "1h", "1d"]
    o_w = 0
    o_l = 0

    for timef in timeframes:
        wins = 0
        loses = 0
        for contract in contracts:

            candles = binance.get_historical_candles(contracts[contract], timef)
            bars = []

            for can in candles:
                bar = [can.timestamp, can.open, can.high, can.low, can.close, can.volume]
                bars.append(bar)

            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df = df.dropna()

            # MA200

            ma = SMAIndicator(df['close'], 200)
            df['ma200'] = ma.sma_indicator()
            # df['ma200'] = df['ma200'].fillna(0)

            # RSI

            indicator_rsi = RSIIndicator(df['close'], 10)
            df['rsi10'] = indicator_rsi.rsi()
            # df['rsi10'] = df['rsi10'].fillna(0)

            df = df.dropna()

            # Strategy

            buy = False
            count = 0
            buy_time = 0
            init_price = 0
            fees = 0
            result = []

            # Statistics

            symbol_profit = 0
            strategy_entries = 0

            for i in range(len(df)):
                if df.close.iloc[i] > df.ma200.iloc[i] and df.rsi10.iloc[i] < 30 and buy == False:
                        init_price = df.close.iloc[i]
                        fees = (init_price / 100) * 0.1
                        buy_time = df.timestamp.iloc[i]
                        buy = True
                elif init_price > 0 and df.rsi10.iloc[i] > 40 and buy == True:
                        temp_list = []
                        temp_list.append(contract)
                        temp_list.append(timef)
                        date = pd.to_datetime(buy_time, unit='ms')
                        temp_list.append(date)
                        sell_date = pd.to_datetime(df.timestamp.iloc[i], unit='ms')
                        temp_list.append(sell_date)
                        temp_list.append(init_price)
                        temp_list.append(df.close.iloc[i])
                        fees = fees + (df.close.iloc[i] / 100) * 0.1
                        temp_list.append(fees)
                        # profit = ((e[4] - fees) * 100) / init_price - 100
                        profit = (((df.close.iloc[i] - fees) * 100) / init_price - 100) / 100
                        if profit > 0:
                            wins += 1
                        else:
                            loses += 1
                        symbol_profit += profit
                        strategy_entries += 1
                        effectiveness.append(profit)
                        temp_list.append(profit)
                        temp_list.append('')
                        result.append(temp_list)
                        buy = False
                elif init_price > 0 and count == 10:
                        temp_list = []
                        temp_list.append(contract)
                        temp_list.append(timef)
                        date = pd.to_datetime(buy_time, unit='ms')
                        temp_list.append(date)
                        sell_date = pd.to_datetime(df.timestamp.iloc[i], unit='ms')
                        temp_list.append(sell_date)
                        temp_list.append(init_price)
                        temp_list.append(df.close.iloc[i])
                        fees = fees + (df.close.iloc[i] / 100) * 0.1
                        temp_list.append(fees)
                        profit = (((df.close.iloc[i] - fees) * 100) / init_price - 100) / 100
                        if profit > 0:
                            wins += 1
                        else:
                            loses += 1
                        symbol_profit += profit
                        strategy_entries += 1
                        effectiveness.append(profit)
                        temp_list.append(profit)
                        temp_list.append('')
                        result.append(temp_list)
                        buy = False
                else:
                    count += 1
            if strategy_entries > 0:
                effectiveness_per_timef = round(symbol_profit / strategy_entries, 4)
                result[-1][8] = effectiveness_per_timef
            result_df = result_df.append(
                pd.DataFrame(result, columns=['Symbol', 'Timeframe', 'Buy Date', 'Sell Date', 'Original Value',
                                              'After value', 'Fees', 'Profit %', 'Effectiveness']),
                ignore_index=True)
        print(f'Wins on {timef}: ' + str(wins))
        print(f'Loses on {timef}: ' + str(loses))
        o_w += wins
        o_l += loses
    eff = sum(effectiveness) / len(effectiveness)
    result_df['Overall_Effectiveness'] = ''
    result_df['Overall_Effectiveness'][0] = eff
    file_name = 'backtest_results/MA200_RSI10_3.xlsx'
    result_df.to_excel(file_name)
    print('MA200_RSI done')
    print('Overall Wins : ' + str(o_w))
    print('Overall Losses : ' + str(o_l))
    # toc = time.perf_counter()
    # print(f'Done in {toc - tic:0.4f} seconds')


# Strategy #3
# close > ema200
# Entry:
#  - short: MACD histogram > 0 && signal crosses MACD line
#  - long: MACD histogram under 0 line && signal crosses MACD line
# Exit: predefined tp / sl
def MACD_EMA200(binance, take_profit, stop_loss):
    # tic = time.perf_counter()
    contracts = binance.get_contracts()

    result_df = pd.DataFrame()

    effectiveness = []

    timeframes = ["1m", "5m", "1h", "1d"]
    o_w = 0
    o_l = 0

    for timef in timeframes:
        wins = 0
        loses = 0
        for contract in contracts:
            # if contract == 'BTCUSDT':
            candles = binance.get_historical_candles(contracts[contract], timef)
            bars = []

            for can in candles:
                bar = [can.timestamp, can.open, can.high, can.low, can.close, can.volume]
                bars.append(bar)

            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # MACD

            indicator_macd = MACD(df['close'])
            df['MACD'] = indicator_macd.macd()
            df['signal'] = indicator_macd.macd_signal()
            df['histogram'] = indicator_macd.macd_diff()

            # EMA200

            ema = EMAIndicator(df['close'], 200)
            df['ema200'] = ema.ema_indicator()

            df = df.dropna()

            # Strategy

            buy = False
            short = False
            long = False
            result = []
            init_price = 0
            buy_time = 0
            fees = 0
            tp = take_profit
            sl = stop_loss

            # Statistics

            symbol_profit = 0
            strategy_entries = 0

            for i in range(len(df)):
                diff = df.MACD.iloc[i] - df.signal.iloc[i]
                if df.close.iloc[i] < df.ema200.iloc[i] and df.histogram.iloc[i] > 0 and diff < 1 and buy == False:
                    init_price = df.close.iloc[i]
                    fees = (df.close.iloc[i] / 100) * 0.1
                    buy_time = df.timestamp.iloc[i]
                    short = True
                    buy = True
                elif df.close.iloc[i] > df.ema200.iloc[i] and df.histogram.iloc[i] < 0 and diff < 1 and buy == False:
                    init_price = df.close.iloc[i]
                    fees = (df.close.iloc[i] / 100) * 0.1
                    buy_time = df.timestamp.iloc[i]
                    long = True
                    buy = True
                elif short:
                    if init_price > 0 and (
                            df.close.iloc[i] <= init_price * (1 - tp) or df.close.iloc[i] >= init_price * (1 + sl)):
                        temp_list = []
                        temp_list.append(contract)
                        temp_list.append(timef)
                        temp_list.append('Short')
                        date = pd.to_datetime(buy_time, unit='ms')
                        temp_list.append(date)
                        sell_date = pd.to_datetime(df.timestamp.iloc[i], unit='ms')
                        temp_list.append(sell_date)
                        temp_list.append(init_price)
                        temp_list.append(df.close.iloc[i])
                        fees = fees + (df.close.iloc[i] / 100) * 0.1
                        temp_list.append(fees)
                        profit = (100 - (((df.close.iloc[i] + fees) * 100) / init_price)) / 100
                        # optimisation
                        if profit > 100:
                            profit = 0.001
                        elif profit < -100:
                            profit = -0.001

                        # wins
                        if profit > 0:
                            wins += 1
                        else:
                            loses += 1
                        symbol_profit += profit
                        strategy_entries += 1
                        # profit = e[4] - init_price / 100
                        effectiveness.append(profit)
                        temp_list.append(profit)
                        temp_list.append('')
                        result.append(temp_list)
                        short = False
                        buy = False
                elif long:
                    if init_price > 0 and (
                            df.close.iloc[i] >= init_price * (1 + tp) or df.close.iloc[i] <= init_price * (1 - sl)):
                        temp_list = []
                        temp_list.append(contract)
                        temp_list.append(timef)
                        temp_list.append('Long')
                        date = pd.to_datetime(buy_time, unit='ms')
                        temp_list.append(date)
                        sell_date = pd.to_datetime(df.timestamp.iloc[i], unit='ms')
                        temp_list.append(sell_date)
                        temp_list.append(init_price)
                        temp_list.append(df.close.iloc[i])
                        fees = fees + (df.close.iloc[i] / 100) * 0.1
                        temp_list.append(fees)
                        profit = (((df.close.iloc[i] - fees) * 100) / init_price - 100) / 100
                        # optimisation
                        if profit > 100:
                            profit = 0.001
                        elif profit < -100:
                            profit = -0.001

                        # wins
                        if profit > 0:
                            wins += 1
                        else:
                            loses += 1
                        symbol_profit += profit
                        strategy_entries += 1
                        # profit = e[4] - init_price / 100
                        effectiveness.append(profit)
                        temp_list.append(profit)
                        temp_list.append('')
                        result.append(temp_list)
                        long = False
                        buy = False
                else:
                    continue
            if strategy_entries > 0:
                effectiveness_per_timef = round(symbol_profit / strategy_entries, 4)
                result[-1][9] = effectiveness_per_timef
            result_df = result_df.append(
                pd.DataFrame(result,
                             columns=['Symbol', 'Timeframe', 'Signal', 'Buy Date', 'Sell Date', 'Original Value',
                                      'After value', 'Fees', 'Profit %', 'Effectiveness']),
                ignore_index=True)
        print(f'Wins on {timef}: ' + str(wins))
        print(f'Loses on {timef}: ' + str(loses))
        o_w += wins
        o_l += loses

    # print(result_df)
    eff = sum(effectiveness) / len(effectiveness)
    result_df['Overall_Effectiveness'] = ''
    result_df['Overall_Effectiveness'][0] = eff
    take_profit = str(take_profit)
    take_profit = take_profit.replace(".", ",")
    stop_loss = str(stop_loss)
    stop_loss = stop_loss.replace(".", ",")
    file_name = f'backtest_results/MACD_EMA200_{take_profit}_{stop_loss}.xlsx'
    result_df.to_excel(file_name)
    # toc = time.perf_counter()
    # print(f'Done in {toc - tic:0.4f} seconds')
    print('MACD_EMA200 done with take profit: ' + take_profit + ' stop loss: ' + stop_loss)
    print('Overall Wins : ' + str(o_w))
    print('Overall Losses : ' + str(o_l))

# BUY:

# Both K% and %D hit oversold -> < 20 ---> main entry
# after that K% and %D doesn't hit overbought < 80
# RSI > 50 --> means uptrend -> Buy signal
#     < 50 --> downtrend -> Sell signal
# MACD -> detecting momentum
#   if MACD line crosses above the signal line -> Buy signal
#   else Sell signal
#   Histogram <> 0 ===> Histogram = MACD line - Signal line

# SELL:


def STOCHASTIC_RSI_MACD(binance, take_profit, stop_loss):
    # tic = time.perf_counter()
    contracts = binance.get_contracts()

    result_df = pd.DataFrame()

    effectiveness = []

    timeframes = ["1m", "5m", "1h", "1d"]
    o_w = 0
    o_l = 0

    for timef in timeframes:
        wins = 0
        loses = 0
        for contract in contracts:
            # if contract == 'BTCUSDT':
            candles = binance.get_historical_candles(contracts[contract], timef)
            bars = []

            for can in candles:
                bar = [can.timestamp, can.open, can.high, can.low, can.close, can.volume]
                bars.append(bar)

            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # MACD

            indicator_macd = MACD(df['close'])
            # df['MACD'] = indicator_macd.macd()
            # df['signal'] = indicator_macd.macd_signal()
            df['histogram'] = indicator_macd.macd_diff()

            # RSI

            indicator_rsi = RSIIndicator(df['close'])
            df['rsi'] = indicator_rsi.rsi()

            # STOCHASTIC
            indicator_stochastic = StochasticOscillator(df['close'], df['high'], df['low'])
            df['K'] = indicator_stochastic.stoch()
            df['D'] = df['K'].rolling(3).mean()

            df = df.dropna()

            # Strategy

            buy = False
            short = False
            long = False
            exit_signal = False
            result = []
            init_price = 0
            buy_time = 0
            fees = 0
            tp = take_profit
            sl = stop_loss

            # Statistics

            symbol_profit = 0
            strategy_entries = 0

            for i in range(len(df)):
                if (df.K.iloc[i] > 80 and df.D.iloc[i] > 80) and buy == False and exit_signal == False:
                    init_price = df.close.iloc[i]
                    fees = (df.close.iloc[i] / 100) * 0.1
                    buy_time = df.timestamp.iloc[i]
                    short = True
                    buy = True
                elif (df.K.iloc[i] < 20 and df.D.iloc[i] < 20) and buy == False and exit_signal == False:
                    init_price = df.close.iloc[i]
                    fees = (df.close.iloc[i] / 100) * 0.1
                    buy_time = df.timestamp.iloc[i]
                    long = True
                    buy = True
                elif short:
                    if (df.rsi.iloc[i] < 50 and df.histogram.iloc[i] < 0 and df.K.iloc[i] > 20 and df.D.iloc[
                        i] > 20) or exit_signal == True:
                        exit_signal = True
                        if init_price > 0 and (
                                df.close.iloc[i] <= init_price * (1 - tp) or df.close.iloc[i] >= init_price * (
                                1 + sl)):
                            temp_list = []
                            temp_list.append(contract)
                            temp_list.append(timef)
                            temp_list.append('Short')
                            date = pd.to_datetime(buy_time, unit='ms')
                            temp_list.append(date)
                            sell_date = pd.to_datetime(df.timestamp.iloc[i], unit='ms')
                            temp_list.append(sell_date)
                            temp_list.append(init_price)
                            temp_list.append(df.close.iloc[i])
                            fees = fees + (df.close.iloc[i] / 100) * 0.1
                            temp_list.append(fees)
                            profit = (100 - (((df.close.iloc[i] + fees) * 100) / init_price)) / 100
                            #optimisation
                            if profit > 100:
                                profit = 0.001
                            elif profit < -100:
                                profit = -0.001

                            #wins
                            if profit > 0:
                                wins += 1
                            else:
                                loses += 1
                            symbol_profit += profit
                            effectiveness.append(profit)
                            strategy_entries += 1
                            # profit = e[4] - init_price / 100
                            temp_list.append(profit)
                            temp_list.append('')
                            result.append(temp_list)
                            short = False
                            buy = False
                            exit_signal = False
                        else:
                            continue
                    else:
                        short = False
                        buy = False

                elif long:
                    if (df.rsi.iloc[i] > 50 and df.histogram.iloc[i] > 0 and df.K.iloc[i] < 80 and df.D.iloc[
                        i] < 80) or exit_signal == True:
                        exit_signal = True
                        if init_price > 0 and (
                                df.close.iloc[i] >= init_price * (1 + tp) or df.close.iloc[i] <= init_price * (
                                1 - sl)):
                            temp_list = []
                            temp_list.append(contract)
                            temp_list.append(timef)
                            temp_list.append('Long')
                            date = pd.to_datetime(buy_time, unit='ms')
                            temp_list.append(date)
                            sell_date = pd.to_datetime(df.timestamp.iloc[i], unit='ms')
                            temp_list.append(sell_date)
                            temp_list.append(init_price)
                            temp_list.append(df.close.iloc[i])
                            fees = fees + (df.close.iloc[i] / 100) * 0.1
                            temp_list.append(fees)
                            profit = (((df.close.iloc[i] - fees) * 100) / init_price - 100) / 100
                            # optimisation
                            if profit > 100:
                                profit = 0.001
                            elif profit < -100:
                                profit = -0.001

                            # wins
                            if profit > 0:
                                wins += 1
                            else:
                                loses += 1
                            symbol_profit += profit
                            effectiveness.append(profit)
                            strategy_entries += 1
                            # profit = e[4] - init_price / 100
                            temp_list.append(profit)
                            temp_list.append('')
                            result.append(temp_list)
                            long = False
                            buy = False
                            exit_signal = False
                        else:
                            continue
                    else:
                        long = False
                        buy = False

                else:
                    continue
            if strategy_entries > 0:
                effectiveness_per_timef = round(symbol_profit / strategy_entries, 4)
                result[-1][9] = effectiveness_per_timef
            result_df = result_df.append(
                pd.DataFrame(result,
                             columns=['Symbol', 'Timeframe', 'Signal', 'Buy Date', 'Sell Date', 'Original Value',
                                      'After Value', 'Fees', 'Profit %', 'Effectiveness']),
                ignore_index=True)
        print(f'Wins on {timef}: ' + str(wins))
        print(f'Loses on {timef}: ' + str(loses))
        o_w += wins
        o_l += loses

    eff = sum(effectiveness) / len(effectiveness)
    result_df['Overall_Effectiveness'] = ''
    result_df['Overall_Effectiveness'][0] = eff
    take_profit = str(take_profit)
    take_profit = take_profit.replace(".", ",")
    stop_loss = str(stop_loss)
    stop_loss = stop_loss.replace(".", ",")
    file_name = f'backtest_results/STOCHASTIC_RSI_MACD_{take_profit}_{stop_loss}.xlsx'
    result_df.to_excel(file_name)
    # toc = time.perf_counter()
    # print(f'Done in {toc - tic:0.4f} seconds')
    print('STOCHASTIC_RSI_MACD done with take profit: ' + take_profit + ' stop loss: ' + stop_loss)
    print('Overall Wins : ' + str(o_w))
    print('Overall Losses : ' + str(o_l))


# LONG:

# EMA5 > EMA21 & EMA50 > EMA200
# AO > 2
# ADX > 15
# BB %B > 0.75 meaning overbought

# SHORT:
# EMA5 < EMA21 & EMA50 < EMA200
# AO < -2
# ADX > 15
# BB %B < 0.25 meaning oversold

# TP 1% SL 2%


def ADX_BBpB_AO_EMA(binance, take_profit, stop_loss):
    # tic = time.perf_counter()
    contracts = binance.get_contracts()

    result_df = pd.DataFrame()

    effectiveness = []

    timeframes = ["1d"]
    o_w = 0
    o_l = 0
    # start = False

    for timef in timeframes:
        wins = 0
        loses = 0
        # print(timef)
        # start = False
        for contract in contracts:
            # if contract == 'FTMBUSD':
            candles = binance.get_historical_candles(contracts[contract], timef, 250)
            bars = []

            for can in candles:
                bar = [can.timestamp, can.open, can.high, can.low, can.close, can.volume]
                bars.append(bar)

            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            df = df.dropna()
            # print(df.eq(0).any().any())

            # BollingerBands

            indicator_bb = BollingerBands(df['close'])
            df['hg_band'] = indicator_bb.bollinger_hband()
            df['lw_band'] = indicator_bb.bollinger_lband()

            # BollingerBands %B

            df['b'] = ''

            # EMA5 & EMA21 & EMA50 & EMA200

            ema5_indicator = EMAIndicator(df['close'], 5)
            df['ema5'] = ema5_indicator.ema_indicator()
            ema21_indicator = EMAIndicator(df['close'], 21)
            df['ema21'] = ema21_indicator.ema_indicator()
            ema50_indicator = EMAIndicator(df['close'], 50)
            df['ema50'] = ema50_indicator.ema_indicator()
            ema200_indicator = EMAIndicator(df['close'], 200)
            df['ema200'] = ema200_indicator.ema_indicator()

            # ADX
            # print("----------------------")
            # print(contract)
            # print(df)
            if df.empty or (contract == 'ANCUSDT' and timef == '1d') or (contract == 'GMTUSDT' and timef == '1d') or (
                    contract == 'APEUSDT' and timef == '1d') or (contract == 'BTCUSDT_220624' and timef == '1d') or (
                    contract == 'ETHUSDT_220624' and timef == '1d') or (contract == 'TRXBUSD' and timef == '1d') or (contract == 'GALABUSD' and timef == '1d')\
                    or (contract == 'FTMBUSD' and timef == '1d'):
                df['adx'] = 0
            elif contract in ['GALBUSD', 'DODOBUSD', 'ANCBUSD', '1000LUNCBUSD', 'LUNA2BUSD', 'OPUSDT', 'DOTBUSD', 'ICPBUSD', 'TLMBUSD']:
                df['adx'] = 0
            else:
                adx_indicator = ADXIndicator(df['high'], df['low'], df['close'])
                df['adx'] = adx_indicator.adx()
            # print("----------------------")
            # Awesome Oscillator
            # APEUSDT / BTCUSDT_220624
            ao_indicator = AwesomeOscillatorIndicator(df['high'], df['low'])
            df['ao'] = ao_indicator.awesome_oscillator()

            df = df.dropna()

            # Strategy

            buy = False
            short = False
            long = False
            result = []
            init_price = 0
            buy_time = 0
            fees = 0
            tp = take_profit
            sl = stop_loss

            # Statistics

            symbol_profit = 0
            strategy_entries = 0

            for i in range(len(df)):
                diff = df.hg_band.iloc[i] - df.lw_band.iloc[i]
                df.b.iloc[i] = (df.close.iloc[i] - df.lw_band.iloc[i]) / diff  # Calculating BB %B

                if df.ema5.iloc[i] < df.ema21.iloc[i] and df.ema50.iloc[i] < df.ema200.iloc[i] and df.ao.iloc[
                    i] < -2 and df.adx.iloc[i] > 15 and df.b.iloc[i] < 0.25 and buy == False:
                    init_price = df.close.iloc[i]
                    fees = (df.close.iloc[i] / 100) * 0.1
                    buy_time = df.timestamp.iloc[i]
                    short = True
                    buy = True
                elif df.ema5.iloc[i] > df.ema21.iloc[i] and df.ema50.iloc[i] > df.ema200.iloc[i] and df.ao.iloc[
                    i] > 2 and df.adx.iloc[i] > 15 and df.b.iloc[i] > 0.75 and buy == False:
                    init_price = df.close.iloc[i]
                    fees = (df.close.iloc[i] / 100) * 0.1
                    buy_time = df.timestamp.iloc[i]
                    long = True
                    buy = True
                elif short:
                    if init_price > 0 and (
                            df.close.iloc[i] <= init_price * (1 - tp) or df.close.iloc[i] >= init_price * (1 + sl)):
                        temp_list = []
                        temp_list.append(contract)
                        temp_list.append(timef)
                        temp_list.append('Short')
                        date = pd.to_datetime(buy_time, unit='ms')
                        temp_list.append(date)
                        sell_date = pd.to_datetime(df.timestamp.iloc[i], unit='ms')
                        temp_list.append(sell_date)
                        temp_list.append(init_price)
                        temp_list.append(df.close.iloc[i])
                        fees = fees + (df.close.iloc[i] / 100) * 0.1
                        temp_list.append(fees)
                        profit = (100 - (((df.close.iloc[i] + fees) * 100) / init_price)) / 100
                        if profit > 0:
                            wins += 1
                        else:
                            loses += 1
                        symbol_profit += profit
                        strategy_entries += 1
                        effectiveness.append(profit)
                        temp_list.append(profit)
                        temp_list.append('')
                        result.append(temp_list)
                        short = False
                        buy = False
                elif long:
                    if init_price > 0 and (
                            df.close.iloc[i] >= init_price * (1 + tp) or df.close.iloc[i] <= init_price * (1 - sl)):
                        temp_list = []
                        temp_list.append(contract)
                        temp_list.append(timef)
                        temp_list.append('Long')
                        date = pd.to_datetime(buy_time, unit='ms')
                        temp_list.append(date)
                        sell_date = pd.to_datetime(df.timestamp.iloc[i], unit='ms')
                        temp_list.append(sell_date)
                        temp_list.append(init_price)
                        temp_list.append(df.close.iloc[i])
                        fees = fees + (df.close.iloc[i] / 100) * 0.1
                        temp_list.append(fees)
                        profit = (((df.close.iloc[i] - fees) * 100) / init_price - 100) / 100
                        if profit > 0:
                            wins += 1
                        else:
                            loses += 1
                        symbol_profit += profit
                        strategy_entries += 1
                        effectiveness.append(profit)
                        temp_list.append(profit)
                        temp_list.append('')
                        result.append(temp_list)
                        long = False
                        buy = False
                else:
                    continue
            if strategy_entries > 0:
                effectiveness_per_timef = round(symbol_profit / strategy_entries, 4)
                result[-1][9] = effectiveness_per_timef
            result_df = result_df.append(
                pd.DataFrame(result,
                             columns=['Symbol', 'Timeframe', 'Signal', 'Buy Date', 'Sell Date', 'Original Value',
                                      'After value', 'Fees', 'Profit %', 'Effectiveness']),
                ignore_index=True)
        print(f'Wins on {timef}: ' + str(wins))
        print(f'Loses on {timef}: ' + str(loses))
        o_w += wins
        o_l += loses

    eff = sum(effectiveness) / len(effectiveness)
    result_df['Overall_Effectiveness'] = ''
    result_df['Overall_Effectiveness'][0] = eff
    take_profit = str(take_profit)
    take_profit = take_profit.replace(".", ",")
    stop_loss = str(stop_loss)
    stop_loss = stop_loss.replace(".", ",")
    file_name = f'backtest_results/ADX_BB%B_AO_EMA_{take_profit}_{stop_loss}.xlsx'
    result_df.to_excel(file_name)
    print('ADX_BB%B_AO_EMA done with take profit: ' + take_profit + ' stop loss: ' + stop_loss)
    print('Overall Wins : ' + str(o_w))
    print('Overall Losses : ' + str(o_l))
    # # toc = time.perf_counter()
    # # print(f'Done in {toc - tic:0.4f} seconds')


def processing(binance, symbol=''):
    if symbol == '':
        contracts = binance.get_contracts()
        # contracts = ['BTCUSDT','ETHUSDT']
        strategies_list = ['MACD_EMA200.xlsx', 'BOLLINGERBANDS_EMA200.xlsx', 'STOCHASTIC_RSI_MACD.xlsx',
                           'ADX_BB%B_AO_EMA.xlsx', 'MA200_RSI10_TEST.xlsx']
        result_df = pd.DataFrame()
        for strat in strategies_list:
            df = pd.read_excel(rf'backtest_results\{strat}', index_col=0)
            df['Effectiveness'] = df['Effectiveness'].fillna(0)
            for contract in contracts:
                df_symbol = df[df['Symbol'] == contract]
                df_symbol = df_symbol[df_symbol['Effectiveness'] != 0]
                # print(df_symbol)
                base = 0
                for e in range(len(df_symbol)):
                    if base < df_symbol.Effectiveness.iloc[e] < 1:
                        base = df_symbol.Effectiveness.iloc[e]

                if base != 0:
                    df_result = df_symbol[df_symbol['Effectiveness'] == base]
                    strategy = strat.replace('.xlsx', '')
                    df_result['Strategy'] = strategy
                    result_df = result_df.append(df_result)
                    # print(df_result)

        result_df.sort_values(by=['Effectiveness'], inplace=True, ascending=False)
        top10 = result_df.head(10)
        top10 = top10.drop('Buy Date', 1)
        top10 = top10.drop('Sell Date', 1)
        top10 = top10.drop('Original Value', 1)
        top10 = top10.drop('After value', 1)
        top10 = top10.drop('After Value', 1)
        top10 = top10.drop('Fees', 1)
        top10 = top10.drop('Profit %', 1)
        top10_result = top10.values.tolist()
        return top10_result
    else:
        contracts = binance.get_contracts()
        if symbol in contracts:
            strategies_list = ['MACD_EMA200.xlsx', 'BOLLINGERBANDS_EMA200.xlsx']
            result_df = pd.DataFrame()
            for strat in strategies_list:
                df = pd.read_excel(rf'backtest_results\{strat}', index_col=0)
                df['Effectiveness'] = df['Effectiveness'].fillna(0)
                for contract in contracts:
                    if contract == symbol:
                        df_symbol = df[df['Symbol'] == symbol]
                        df_symbol = df_symbol[df_symbol['Effectiveness'] != 0]
                        # print(df_symbol)
                        base = 0
                        for e in range(len(df_symbol)):
                            if df_symbol.Effectiveness.iloc[e] > base:
                                base = df_symbol.Effectiveness.iloc[e]

                        if base != 0:
                            df_result = df_symbol[df_symbol['Effectiveness'] == base]
                            strategy = strat.replace('.xlsx', '')
                            df_result['Strategy'] = strategy
                            result_df = result_df.append(df_result)
                            # print(df_result)

            result_df.sort_values(by=['Effectiveness'], inplace=True, ascending=False)
            top10 = result_df.head(10)
            top10 = top10.drop('Buy Date', 1)
            top10 = top10.drop('Sell Date', 1)
            top10 = top10.drop('Original Value', 1)
            top10 = top10.drop('After value', 1)
            top10 = top10.drop('Fees', 1)
            top10 = top10.drop('Profit %', 1)
            top10 = top10.drop('Volume', 1)
            top10_result = top10.values.tolist()
            return top10_result
        else:
            return


def average_volume(binance, symbol, timef):
    contracts = binance.get_contracts()
    candles = binance.get_historical_candles(contracts[symbol], timef)

    bars = []

    for can in candles:
        bar = [can.timestamp, can.open, can.high, can.low, can.close, can.volume]
        bars.append(bar)

    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_volumes = df['volume']
    file_name = 'backtest_results/AVERAGE.xlsx'
    df.to_excel(file_name)
    print('done')

    # df1 = df_volumes.head(50)
    df_avg = df['volume'].mean()
    print(df_avg)
    # print(df1)
    # print(df_volumes)


def averages(binance, symbol, timef):
    contracts = binance.get_contracts()
    candles = binance.get_historical_candles(contracts[symbol], timef, 730)

    bars = []

    for can in candles:
        bar = [can.timestamp, can.open, can.high, can.low, can.close, can.volume]
        bars.append(bar)

    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    # file_name = 'backtest_results/AVERAGE.xlsx'
    # df.to_excel(file_name)
    # print('done')

    # df1 = df_volumes.head(50)
    df2 = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    volume_avg = df['volume'].mean()
    volume_std = df['volume'].std()
    volume_min = df['volume'].min()
    volume_max = df['volume'].max()
    volume_min = "{0:.3f}".format(volume_min)
    volume_max = "{0:.3f}".format(volume_max)
    volume_avg = "{0:.3f}".format(volume_avg)
    volume_std = "{0:.3f}".format(volume_std)
    open_avg = df['open'].mean()
    open_std = df['open'].std()
    open_min = df['open'].min()
    open_max = df['open'].max()
    open_min = "{0:.3f}".format(open_min)
    open_max = "{0:.3f}".format(open_max)
    open_avg = "{0:.3f}".format(open_avg)
    open_std = "{0:.3f}".format(open_std)
    high_avg = df['high'].mean()
    high_std = df['high'].std()
    high_min = df['high'].min()
    high_max = df['high'].max()
    high_min = "{0:.3f}".format(high_min)
    high_max = "{0:.3f}".format(high_max)
    high_avg = "{0:.3f}".format(high_avg)
    high_std = "{0:.3f}".format(high_std)
    low_avg = df['low'].mean()
    low_std = df['low'].std()
    low_min = df['low'].min()
    low_max = df['low'].max()
    low_min = "{0:.3f}".format(low_min)
    low_max = "{0:.3f}".format(low_max)
    low_avg = "{0:.3f}".format(low_avg)
    low_std = "{0:.3f}".format(low_std)
    close_avg = df['close'].mean()
    close_std = df['close'].std()
    close_min = df['close'].min()
    close_max = df['close'].max()
    close_min = "{0:.3f}".format(close_min)
    close_max = "{0:.3f}".format(close_max)
    close_avg = "{0:.3f}".format(close_avg)
    close_std = "{0:.3f}".format(close_std)
    np_arr = np.array(['open', open_avg, 'high', high_avg, 'low', low_avg, 'close', close_avg, 'volume', volume_avg])
    np_arr2 = np.array(['open', open_std, 'high', high_std, 'low', low_std, 'close', close_std, 'volume', volume_std])
    np_arr3 = np.array(['open', open_min, 'high', high_min, 'low', low_min, 'close', close_min, 'volume', volume_min])
    np_arr4 = np.array(['open', open_max, 'high', high_max, 'low', low_max, 'close', close_max, 'volume', volume_max])
    lst = np_arr.tolist()
    lst2 = np_arr2.tolist()
    lst3 = np_arr3.tolist()
    lst4 = np_arr4.tolist()

    def Convert(lst):
        res_dct = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)}
        return res_dct

    dct = Convert(lst)
    dct2 = Convert(lst2)
    dct3 = Convert(lst3)
    dct4 = Convert(lst4)
    df2 = df2.append(dct, ignore_index=True)
    df2 = df2.append(dct2, ignore_index=True)
    df2 = df2.append(dct3, ignore_index=True)
    df2 = df2.append(dct4, ignore_index=True)
    df2.index = ['mean', 'std', 'min', 'max']
    df2.to_html('temp.html')
    print(df2.to_markdown())

def heatmap_4_symbol():
    sl_values = ["0,01", "0,02", "0,04", "0,08", "0,15"]
    tp_values = ["0,01", "0,02", "0,03", "0,04", "0,05"]
    list = []
    tmp_list = []
    for tp in tp_values:
        take_profit = tp
        if tmp_list:
            list.append(tmp_list)
            tmp_list = []
        for sl in sl_values:
            path = f'backtest_results/MACD_EMA200_{take_profit}_{sl}.xlsx'
            data = pd.read_excel(path)
            df = pd.DataFrame(data, columns=['Overall_Effectiveness'])
            df = df.dropna()
            # print("take profit: " + str(take_profit) + " stop loss: " + sl)
            # print(df)
            # tmp_list.append(round((round(df['Overall_Effectiveness'].iloc[0], 5))*10,4))
            tmp_list.append((round(df['Overall_Effectiveness'].iloc[0], 2)))
    list.append(tmp_list)
    print(list)

    take_profits = ["1% TP", "2% TP", "3% TP", "4% TP", "5% TP"]
    stop_losses = ["1% SL", "2% SL", "4% SL", "8% SL", "15% SL"]
    results = np.array(list)

    fig, ax = plt.subplots()
    im = ax.imshow(results)

    # Show all ticks and label them with the respective list entries
    ax.set_xticks(np.arange(len(take_profits)), labels=stop_losses)
    ax.set_yticks(np.arange(len(stop_losses)), labels=take_profits)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    for i in range(len(stop_losses)):
        for j in range(len(take_profits)):
            text = ax.text(j, i, results[i, j],
                           ha="center", va="center", color="w")

    ax.set_title("TP / SL efficiency for MACD_EMA200")
    fig.tight_layout()
    plt.show()

def stacked_bar_chart_4_symbol():
    # N = 5
    # symbolWins = (39, 168, 107, 90)
    # symbolLosses = (1, 12, 18, 56)
    # ind = np.arange(N)  # the x locations for the groups
    # width = 0.35
    # fig = plt.figure()
    # ax = fig.add_axes([0, 0, 1,1])
    # ax.bar(ind, symbolWins, width, color='r')
    # ax.bar(ind, symbolLosses, width, bottom=symbolWins, color='b')
    # ax.set_ylabel('Values')
    # ax.set_title('Win/losses by timeframes')
    # ax.set_xticks(ind, ('G1', 'G2', 'G3', 'G4'))
    # ax.set_yticks(np.arange(0, 81, 10))
    # ax.legend(labels=['Wins', 'Losses'])
    # plt.show()

    # width of the bars
    barWidth = 0.3

    # Choose the height of the blue bars
    bars1 = [1356, 3030, 5558, 3077]

    # Choose the height of the cyan bars
    bars2 = [240, 534, 1323, 1643]

    # Choose the height of the error bars (bars1)
    yer1 = [0.5, 0.4, 0.5]

    # Choose the height of the error bars (bars2)
    yer2 = [1, 0.7, 1]

    # The x position of bars
    r1 = np.arange(len(bars1))
    r2 = [x + barWidth for x in r1]

    # Create blue bars
    plt.bar(r1, bars1, width=barWidth, color='blue', edgecolor='black', capsize=7, label='wins')

    # Create cyan bars
    plt.bar(r2, bars2, width=barWidth, color='red', edgecolor='black', capsize=7, label='losses')

    # general layout
    plt.xticks([r + barWidth for r in range(len(bars1))], ['1m', '5m', '1h', '1d'])
    plt.ylabel('No.')
    plt.xlabel('Timeframes')
    plt.legend()
    plt.title("8 % SL - 1 % TP wins/losses MACD_EMA200")
    # Show graphic
    plt.show()
