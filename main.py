import tkinter as tk
import logging

from subprocess import call

import ta
import pandas as pd

import numpy as np

import os

import models
from connectors.binance_futures import BinanceFuturesClient
from connectors.bitmex_futures import BitmexFuturesClient

from interface.root_component import Root

from backtesting import *

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler('info.log')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# logger.debug("this message is important only when debugging the program")
# logger.info("this message just shows basic information")
# logger.warning("this msg is about sg you should pay attention to")
# logger.error("this msg helps to debug an error that occured in your program")

if __name__ == '__main__':
    binance = BinanceFuturesClient("30e920298bb4ebe0b091a5229752673e6444219f2f3b22c8b064f4e44a800fd9",
                                   "e8184bc042c0a35afb2cfcb0fa90a039aff82ea6dac6a0e837cd270e59bbcecb", True)

    bitmex = BitmexFuturesClient("gqp4MnYzWhCdEMZP2KglfCQn", "HNdaJfg_K7xFFx8E7_XCv3Lyj_MXKHGctOQ-mL2MwE4bdeBm", True)

    # BolingerBands_Ema200(binance, 0.01, 0.15)
    # BolingerBands_Ema200(binance, 0.02, 0.15)
    # BolingerBands_Ema200(binance, 0.03, 0.15)
    # BolingerBands_Ema200(binance, 0.04, 0.15)
    # BolingerBands_Ema200(binance, 0.05, 0.15)
    # BolingerBands_Ema200(binance, 0.01, 0.02)
    # BolingerBands_Ema200(binance, 0.02, 0.02)
    # BolingerBands_Ema200(binance, 0.03, 0.02)
    # BolingerBands_Ema200(binance, 0.04, 0.02)
    # BolingerBands_Ema200(binance, 0.05, 0.02)
    # BolingerBands_Ema200(binance, 0.01, 0.01)
    # BolingerBands_Ema200(binance, 0.02, 0.01)
    # BolingerBands_Ema200(binance, 0.03, 0.01)
    # BolingerBands_Ema200(binance, 0.04, 0.01)
    # BolingerBands_Ema200(binance, 0.05, 0.01)

    # STOCHASTIC_RSI_MACD(binance, 0.01, 0.01)
    # STOCHASTIC_RSI_MACD(binance, 0.02, 0.01)
    # STOCHASTIC_RSI_MACD(binance, 0.03, 0.01)
    # STOCHASTIC_RSI_MACD(binance, 0.04, 0.01)
    # STOCHASTIC_RSI_MACD(binance, 0.05, 0.01)
    #
    # STOCHASTIC_RSI_MACD(binance, 0.01, 0.02)
    # STOCHASTIC_RSI_MACD(binance, 0.02, 0.02)
    # STOCHASTIC_RSI_MACD(binance, 0.03, 0.02)
    # STOCHASTIC_RSI_MACD(binance, 0.04, 0.02)
    # STOCHASTIC_RSI_MACD(binance, 0.05, 0.02)
    #
    # STOCHASTIC_RSI_MACD(binance, 0.01, 0.04)
    # STOCHASTIC_RSI_MACD(binance, 0.02, 0.04)
    # STOCHASTIC_RSI_MACD(binance, 0.03, 0.04)
    # STOCHASTIC_RSI_MACD(binance, 0.04, 0.04)
    # STOCHASTIC_RSI_MACD(binance, 0.05, 0.04)
    #
    # STOCHASTIC_RSI_MACD(binance, 0.01, 0.08)
    # STOCHASTIC_RSI_MACD(binance, 0.02, 0.08)
    # STOCHASTIC_RSI_MACD(binance, 0.03, 0.08)
    # STOCHASTIC_RSI_MACD(binance, 0.04, 0.08)
    # STOCHASTIC_RSI_MACD(binance, 0.05, 0.08)
    #
    # STOCHASTIC_RSI_MACD(binance, 0.01, 0.15)
    # STOCHASTIC_RSI_MACD(binance, 0.02, 0.15)
    # STOCHASTIC_RSI_MACD(binance, 0.03, 0.15)
    # STOCHASTIC_RSI_MACD(binance, 0.04, 0.15)
    # STOCHASTIC_RSI_MACD(binance, 0.05, 0.15)
    #
    # #MACD
    #
    # MACD_EMA200(binance, 0.01, 0.01)
    # MACD_EMA200(binance, 0.02, 0.01)
    # MACD_EMA200(binance, 0.03, 0.01)
    # MACD_EMA200(binance, 0.04, 0.01)
    # MACD_EMA200(binance, 0.05, 0.01)
    #
    # MACD_EMA200(binance, 0.01, 0.02)
    # MACD_EMA200(binance, 0.02, 0.02)
    # MACD_EMA200(binance, 0.03, 0.02)
    # MACD_EMA200(binance, 0.04, 0.02)
    # MACD_EMA200(binance, 0.05, 0.02)
    #
    # MACD_EMA200(binance, 0.01, 0.04)
    # MACD_EMA200(binance, 0.02, 0.04)
    # MACD_EMA200(binance, 0.03, 0.04)
    # MACD_EMA200(binance, 0.04, 0.04)
    # MACD_EMA200(binance, 0.05, 0.04)
    #
    # MACD_EMA200(binance, 0.01, 0.08)
    # MACD_EMA200(binance, 0.02, 0.08)
    # MACD_EMA200(binance, 0.03, 0.08)
    # MACD_EMA200(binance, 0.04, 0.08)
    # MACD_EMA200(binance, 0.05, 0.08)
    #
    # MACD_EMA200(binance, 0.01, 0.15)
    # MACD_EMA200(binance, 0.02, 0.15)
    # MACD_EMA200(binance, 0.03, 0.15)
    # MACD_EMA200(binance, 0.04, 0.15)
    # MACD_EMA200(binance, 0.05, 0.15)

    # MACD_EMA200(binance, 0.01, 0.01)
    # MA200_RSI(binance)


    # heatmap_4_symbol()
    stacked_bar_chart_4_symbol()

    # MA200_RSI(binance)
    # MACD_EMA200(binance)
    # top10 = processing(binance)
    # print(type(top10))
    # print(top10)
    # top = processing(binance,'BTCUSDT')
    # print(top)
    # average_volume(binance,'LINKUSDT', '1d')
    # STOCHASTIC_RSI_MACD(binance)
    # ADX_BBpB_AO_EMA(binance)
    # MA200_RSI(binance)

    # root = Root(binance, bitmex)
    # root.mainloop()

    # averages(binance,'BTCUSDT','1d')
























    # print(bitmex.get_contracts())

    # print(binance.contracts['XRPUSDT'].lot_size)
    # print(bitmex.contracts['ETHUSDT'].lot_size)
    # print(bitmex.contracts['SOLUSDT'].price_decimals)

    #
    # q = round(40.445)
    # print(q)

    # p = round(round(20000.492193935 / bitmex.contracts['XBTUSD'].tick_size) * bitmex.contracts['XBTUSD'].tick_size, 8)
    # print(p)

    # x = 2000
    # x_str = "{0:.8f}".format(x)
    # print(x)
    # print(x_str)
    #
    # while x_str[-1] =="0":
    #     x_str = x_str[:-1]
    #
    # print(x_str)
    # split_tick = x_str.split(".")
    # print(split_tick)
    #
    # if len(split_tick) > 1:
    #     print(len(split_tick[1]))
    #     print("ezt irja ki")
    # else:
    #     print(split_tick)

    # print(bitmex.get_balances())
    # print(bitmex.cancel_order('71c6a23'))

    # print(bitmex.balances['XBt'].__dict__)
    # bitmex.get_historical_candles(bitmex.contracts['XBTUSD'], "1h")
    # print(bitmex.contracts['XBTUSD'])
    # print(bitmex.place_order(bitmex.contracts['XBTUSD'], "Limit", 100.1, "Buy", price=42000.15445, tif="GoodTillCancel").order_id)
    # print(bitmex.get_order_status("f02833d2-b0f4-4844-b8d1-613c74d429b4",bitmex.contracts['XBTUSD']).status)
    # print(bitmex.get_order_status("98baced7-fac0-425c-913b-ac37368faefc", bitmex.contracts['XBTUSD']).status)
    # print (bitmex.cancel_order("f02833d2-b0f4-4844-b8d1-613c74d429b4").status)

    # print(binance.get_historical_candles("BTCUSDT","1h"))
    # print(binance.balances['USDT'].wallet_balance)
    # print(binance.contracts['BTCUSDT'].lot_size)
    # print(binance.contracts['BTCUSDT'].quantity_decimals)
    # print(binance.contracts['BTCUSDT'].symbol)

    # print(binance.place_order(binance.contracts['BTCUSDT'],"BUY",0.01,"LIMIT", 20000.1345134, "GTC").order_id)
    # print(binance.get_order_status("BTCUSDT",2875182666))
    # print(binance.cancel_oder("BTCUSDT",2875182666))
