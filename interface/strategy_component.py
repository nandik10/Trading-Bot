import json
import tkinter as tk
import typing

from interface.autocomplete_widget import Autocomplete
from interface.styling import *
from interface.scrollable_frame import ScrollableFrame

from connectors.binance_futures import BinanceFuturesClient
from connectors.bitmex_futures import BitmexFuturesClient

from strategies import TechnicalStrategy, BreakoutStrategy
from utils import *

from database import WorkspaceData

from backtesting import *

import webbrowser


class StrategyEditor(tk.Frame):
    def __init__(self, root, binance: BinanceFuturesClient, bitmex: BitmexFuturesClient, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.root = root

        self.db = WorkspaceData()

        self._valid_integer = self.register(check_integer_format)
        self._valid_float = self.register(check_float_format)

        self._exchanges = {"Binance": binance, "Bitmex": bitmex}

        self._all_contracts = []
        self._all_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h"]

        for exchange, client in self._exchanges.items():
            for symbol, contract in client.contracts.items():
                self._all_contracts.append(symbol + "_" + exchange.capitalize())

        self._commands_frame = tk.Frame(self, bg=BG_COLOR)
        self._commands_frame.pack(side=tk.TOP)

        self._table_frame = tk.Frame(self, bg=BG_COLOR)
        self._table_frame.pack(side=tk.TOP)

        self._show_patterns = tk.Button(self._commands_frame, text="Show Candle Patterns", font=GLOBAL_FONT,
                                        command=self._open_patterns, bg=BG_COLOR_2, fg=FG_COLOR)
        # self._add_buton.pack(in_=self._commands_frame, side=tk.TOP)
        self._show_patterns.grid(row=0, column=0, padx=5, pady=10)
        self._add_buton = tk.Button(self._commands_frame, text="Add Strategy", font=GLOBAL_FONT,
                                    command=self._add_strategy_row, bg=BG_COLOR_2, fg=FG_COLOR)
        # self._show_patterns.pack(in_=self._commands_frame, side=tk.TOP)
        self._add_buton.grid(row=0, column=1, padx=5, pady=10)
        self._show_top10_strategies = tk.Button(self._commands_frame, text="TOP10 Strategies", font=GLOBAL_FONT,
                                                command=self._show_top10, bg=BG_COLOR_2, fg=FG_COLOR)
        self._show_top10_strategies.grid(row=0, column=2, padx=5, pady=10)
        self._specific_symbol_strategy = tk.Button(self._commands_frame, text="Customize", font=GLOBAL_FONT,
                                                   command=self._select_ind_strategy, bg=BG_COLOR_2, fg=FG_COLOR)
        self._specific_symbol_strategy.grid(row=0, column=3, padx=5, pady=10)
        self.body_widgets = dict()

        # self._headers = ["Strategy", "Contract", "Timeframe", "Balance %", "TP %", "SL %"]

        self._headers_frame = tk.Frame(self._table_frame, bg=BG_COLOR)

        self.additional_parameters = dict()
        self._extra_input = dict()

        self._base_params = [
            {"code_name": "strategy_type", "widget": tk.OptionMenu, "data_type": str,
             "values": ["Technical", "Breakout", "MACD_EMA200", "BOLINGERBANDS_EMA200", "MA200_RSI"], "width": 10,
             "header": "Strategy"},
            {"code_name": "contract", "widget": tk.OptionMenu, "data_type": str,
             "values": self._all_contracts, "width": 15, "header": "Contract"},
            {"code_name": "timeframe", "widget": tk.OptionMenu, "data_type": str,
             "values": self._all_timeframes, "width": 10, "header": "Timeframe"},
            {"code_name": "balance_percentage", "widget": tk.Entry, "data_type": float, "width": 10,
             "header": "Balance %"},
            {"code_name": "take_profit", "widget": tk.Entry, "data_type": float, "width": 10, "header": "TP %"},
            {"code_name": "stop_loss", "widget": tk.Entry, "data_type": float, "width": 10, "header": "SL %"},
            {"code_name": "parameters", "widget": tk.Button, "data_type": float, "text": "Parameters",
             "bg": BG_COLOR_2, "command": self._show_popup, "header": "", "width": 10},
            {"code_name": "activation", "widget": tk.Button, "data_type": float, "text": "OFF",
             "bg": "darkred", "command": self._switch_strategy, "header": "", "width": 8},
            {"code_name": "delete", "widget": tk.Button, "data_type": float, "text": "X",
             "bg": "darkred", "command": self._delete_row, "header": "", "width": 6}

        ]

        self.extra_params = {
            "Technical": [
                {"code_name": "rsi_length", "name": "RSI Periods", "widget": tk.Entry, "data_type": int},
                {"code_name": "ema_fast", "name": "MACD Fast Length", "widget": tk.Entry, "data_type": int},
                {"code_name": "ema_slow", "name": "MACD Slow Length", "widget": tk.Entry, "data_type": int},
                {"code_name": "ema_signal", "name": "MACD Signal Length", "widget": tk.Entry, "data_type": int}
            ],
            "Breakout": [
                {"code_name": "min_volume", "name": "Minimum Volume", "widget": tk.Entry, "data_type": float}
            ]
        }

        for idx, h in enumerate(self._base_params):
            header = tk.Label(self._headers_frame, text=h['header'], bg=BG_COLOR, fg=FG_COLOR, font=GLOBAL_FONT,
                              width=h['width'], bd=1, relief=tk.FLAT)
            header.grid(row=0, column=idx, padx=1)

        header = tk.Label(self._headers_frame, text="", bg=BG_COLOR, fg=FG_COLOR, font=GLOBAL_FONT,
                          width=8, bd=1, relief=tk.FLAT)
        header.grid(row=0, column=len(self._base_params))

        self._headers_frame.pack(side=tk.TOP, anchor="nw")

        self._body_frame = ScrollableFrame(self._table_frame, bg=BG_COLOR, height=250)
        self._body_frame.pack(side=tk.TOP, fill=tk.X, anchor="nw")

        for h in self._base_params:
            self.body_widgets[h['code_name']] = dict()
            if h['code_name'] in ["strategy_type", "contract", "timeframe"]:
                self.body_widgets[h['code_name'] + "_var"] = dict()

        self._body_index = 0  # check this

        self._load_workspace()

    def _add_strategy_row(self):
        b_index = self._body_index

        for col, base_param in enumerate(self._base_params):
            code_name = base_param['code_name']
            if base_param['widget'] == tk.OptionMenu:
                self.body_widgets[code_name + "_var"][b_index] = tk.StringVar()
                self.body_widgets[code_name + "_var"][b_index].set(base_param['values'][0])
                self.body_widgets[code_name][b_index] = tk.OptionMenu(self._body_frame.sub_frame,
                                                                      self.body_widgets[code_name + "_var"][b_index],
                                                                      *base_param['values'])
                # *["BTCUSDT", "ETHUSDT", "XRPUSDT"] = "BTCUSDT", "ETHUSDT", "XRPUSDT"
                self.body_widgets[code_name][b_index].config(width=base_param['width'], bd=0, indicatoron=0)
            elif base_param['widget'] == tk.Entry:
                self.body_widgets[code_name][b_index] = tk.Entry(self._body_frame.sub_frame, justify=tk.CENTER,
                                                                 bd=1, font=GLOBAL_FONT, width=base_param['width'])

                if base_param['data_type'] == int:
                    self.body_widgets[code_name][b_index].config(validate='key',
                                                                 validatecommand=(self._valid_integer, "%P"))
                elif base_param['data_type'] == float:
                    self.body_widgets[code_name][b_index].config(validate='key',
                                                                 validatecommand=(self._valid_float, "%P"))

            elif base_param['widget'] == tk.Button:
                self.body_widgets[code_name][b_index] = tk.Button(self._body_frame.sub_frame, text=base_param['text'],
                                                                  bg=base_param['bg'], fg=FG_COLOR, font=GLOBAL_FONT,
                                                                  width=base_param['width'],
                                                                  command=lambda frozen_command=base_param[
                                                                      'command']: frozen_command(b_index))
            else:
                continue

            self.body_widgets[code_name][b_index].grid(row=b_index, column=col, padx=6)

        self.additional_parameters[b_index] = dict()

        for strat, params in self.extra_params.items():  # Technical, Breakout ..
            for param in params:  # "code_name": "ema_fast" "code_name": ema_slow"
                self.additional_parameters[b_index][param['code_name']] = None

        self._body_index += 1

    def _delete_row(self, b_index: int):

        for element in self._base_params:
            self.body_widgets[element['code_name']][b_index].grid_forget()

            del self.body_widgets[element['code_name']][b_index]

    def _show_popup(self, b_index: int):

        x = self.body_widgets["parameters"][b_index].winfo_rootx()
        y = self.body_widgets["parameters"][b_index].winfo_rooty()
        # print(x)
        # print(y)

        self._popup_window = tk.Toplevel(self)
        self._popup_window.wm_title("Parameters")
        self._popup_window.config(bg=BG_COLOR)

        self._popup_window.attributes("-topmost", "true")  # creates it in the top-left
        self._popup_window.grab_set()  # you can only click inside the popup window

        self._popup_window.geometry(f"+{x - 80}+{y + 30}")

        strat_selected = self.body_widgets['strategy_type_var'][b_index].get()

        row_nb = 0

        for param in self.extra_params[strat_selected]:
            code_name = param['code_name']

            temp_label = tk.Label(self._popup_window, bg=BG_COLOR, fg=FG_COLOR, text=param['name'], font=BOLD_FONT)
            temp_label.grid(row=row_nb, column=0)

            if param['widget'] == tk.Entry:
                self._extra_input[code_name] = tk.Entry(self._popup_window, bg=BG_COLOR_2, justify=tk.CENTER,
                                                        fg=FG_COLOR,
                                                        insertbackground=FG_COLOR)

                if param['data_type'] == int:
                    self._extra_input[code_name].config(validate='key', validatecommand=(self._valid_integer, "%P"))
                elif param['data_type'] == float:
                    self._extra_input[code_name].config(validate='key', validatecommand=(self._valid_float, "%P"))

                if self.additional_parameters[b_index][code_name] is not None:
                    self._extra_input[code_name].insert(tk.END, str(self.additional_parameters[b_index][code_name]))
            else:
                continue
            self._extra_input[code_name].grid(row=row_nb, column=1)

            row_nb += 1

        # Validation Button

        validation_button = tk.Button(self._popup_window, text="Validate", bg=BG_COLOR_2, fg=FG_COLOR,
                                      command=lambda: self._validate_parameters(b_index))
        validation_button.grid(row=row_nb, column=0, columnspan=2)

    def _validate_parameters(self, b_index: int):

        strat_selected = self.body_widgets['strategy_type_var'][b_index].get()

        for param in self.extra_params[strat_selected]:
            code_name = param['code_name']

            if self._extra_input[code_name].get() == "":
                self.additional_parameters[b_index][code_name] = None
            else:
                self.additional_parameters[b_index][code_name] = param['data_type'](self._extra_input[code_name].get())

        self._popup_window.destroy()

    def _switch_strategy(self, b_index: int):

        for param in ["balance_percentage", "take_profit", "stop_loss"]:
            if self.body_widgets[param][b_index].get() == "":
                self.root.logging_frame.add_log(f"Missing {param} parameter")
                return

        strat_selected = self.body_widgets['strategy_type_var'][b_index].get()

        for param in self.extra_params[strat_selected]:
            if self.additional_parameters[b_index][param['code_name']] is None:
                self.root.logging_frame.add_log(f"Missing {param['code_name']} parameter")
                return

        symbol = self.body_widgets["contract_var"][b_index].get().split("_")[0]
        timeframe = self.body_widgets["timeframe_var"][b_index].get()
        exchange = self.body_widgets["contract_var"][b_index].get().split("_")[1]

        contract = self._exchanges[exchange].contracts[symbol]

        balance_percentage = float(self.body_widgets["balance_percentage"][b_index].get())
        take_profit = float(self.body_widgets["take_profit"][b_index].get())
        stop_loss = float(self.body_widgets["stop_loss"][b_index].get())

        if self.body_widgets['activation'][b_index].cget("text") == "OFF":  # activating the strategy

            if strat_selected == "Technical":
                new_strategy = TechnicalStrategy(self._exchanges[exchange], contract, exchange, timeframe,
                                                 balance_percentage, take_profit,
                                                 stop_loss, self.additional_parameters[b_index])

            elif strat_selected == "Breakout":
                new_strategy = BreakoutStrategy(self._exchanges[exchange], contract, exchange, timeframe,
                                                balance_percentage, take_profit,
                                                stop_loss, self.additional_parameters[b_index])
            else:
                return

            new_strategy.candles = self._exchanges[exchange].get_historical_candles(contract, timeframe)

            if len(new_strategy.candles) == 0:
                self.root.logging_frame.add_log(f"No historical data retrieved for {contract.symbol}")
                return

            if exchange == "Binance":
                self._exchanges[exchange].subscribe_channel([contract], "aggTrade")

            # new_strategy._check_signal()

            self._exchanges[exchange].strategies[b_index] = new_strategy

            for param in self._base_params:
                code_name = param['code_name']

                if code_name != "activation" and "_var" not in code_name:
                    self.body_widgets[code_name][b_index].config(state=tk.DISABLED)

            self.body_widgets["activation"][b_index].config(bg="darkgreen", text="ON")
            self.root.logging_frame.add_log(f"{strat_selected} strategy on {symbol} / {timeframe} started")

        else:
            del self._exchanges[exchange].strategies[b_index]

            for param in self._base_params:
                code_name = param['code_name']

                if code_name != "activation" and "_var" not in code_name:
                    self.body_widgets[code_name][b_index].config(state=tk.NORMAL)

            self.body_widgets["activation"][b_index].config(bg="darkred", text="OFF")
            self.root.logging_frame.add_log(f"{strat_selected} strategy on {symbol} / {timeframe} stopped")

    def _show_top10(self):
        self._popup_window = tk.Toplevel(self)
        self._popup_window.wm_title("TOP 10 Strategies")
        self._popup_window.config(bg=BG_COLOR)

        self._popup_window.attributes("-topmost", "true")  # creates it in the top-left
        self._popup_window.grab_set()  # you can only click inside the popup window
        # self._popup_window.geometry("1000x500")

        self._popup_window.geometry("+{}+{}".format(360, 340))

        self._top10 = processing(self._exchanges["Binance"])
        for t in self._top10:
            if pd.isna(t[2]):
                t[2] = 'Long'

        self._headers = ["symbol", "timeframe", "signal", "effectiveness", "strategy"]
        self._col_width = 13

        for idx, h in enumerate(self._headers):
            if h == 'strategy':
                self._col_width = 25
            header = tk.Label(self._popup_window, text=h.capitalize(),
                              bg=BG_COLOR, fg=FG_COLOR, font=GLOBAL_FONT, width=self._col_width)
            header.grid(row=0, column=idx)
        y = 0
        for x in self._top10:
            y += 1
            for idx, s in enumerate(x):
                symbol = tk.Label(self._popup_window, text=s,
                                  bg=BG_COLOR, fg=FG_COLOR, font=GLOBAL_FONT, width=self._col_width)
                symbol.grid(row=y, column=idx)
            self._select_symbol = tk.Button(self._popup_window, text="Activate",
                                      bg="darkgreen", fg=FG_COLOR, font=GLOBAL_FONT, width=10)
            self._select_symbol.grid(row=y, column=5)

    def _open_patterns(self):

        url = 'http://127.0.0.1:5000/reverse'
        webbrowser.open(url, new=0, autoraise=True)

    def _select_ind_strategy(self):

        self._binance_symbols = list(self._exchanges["Binance"].contracts.keys())
        self._strategies = ['All', 'MACD_EMA200.xlsx', 'BOLLINGERBANDS_EMA200.xlsx', 'STOCHASTIC_RSI_MACD.xlsx',
                           'ADX_BB%B_AO_EMA.xlsx', 'MA200_RSI10_TEST.xlsx']
        self._timeframes = ["1m", "5m", "1h", "1d"]

        self._popup_window = tk.Toplevel(self)
        self._popup_window.wm_title("Select strategy for individual symbol")
        self._popup_window.config(bg=BG_COLOR)

        self._popup_window.attributes("-topmost", "true")  # creates it in the top-left
        self._popup_window.grab_set()  # you can only click inside the popup window
        self._popup_window.geometry("550x200")

        self._popup_window.geometry("+{}+{}".format(660, 440))

        self._binance_label = tk.Label(self._popup_window, text="Symbol", bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
        self._binance_label.grid(row=0, column=0, padx=45, pady=10)

        self._current_symbol = tk.StringVar()
        self._current_symbol.set(self._binance_symbols[0])
        self._symbols = tk.OptionMenu(self._popup_window,self._current_symbol, *self._binance_symbols)
        self._symbols.config(width=15, bd=0, indicatoron=0)
        self._symbols.grid(row=1, column=0, padx=0, pady=10)

        self._strategy_label = tk.Label(self._popup_window, text="Strategy", bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
        self._strategy_label.grid(row=0, column=1, padx=25, pady=10)

        self._current_strategy = tk.StringVar()
        self._current_strategy.set('All')
        self._strategies_om = tk.OptionMenu(self._popup_window,self._current_strategy, *self._strategies)
        self._strategies_om.config(width=15, bd=0, indicatoron=0)
        self._strategies_om.grid(row=1, column=1, padx=25, pady=10)

        self._timeframe_label = tk.Label(self._popup_window, text="Timeframe", bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
        self._timeframe_label.grid(row=0, column=2, padx=25, pady=10)

        self._current_timeframe = tk.StringVar()
        self._current_timeframe.set('All')
        self._tf = tk.OptionMenu(self._popup_window, self._current_timeframe, *self._timeframes)
        self._tf.config(width=15, bd=0, indicatoron=0)
        self._tf.grid(row=1, column=2, padx=0, pady=10)

        self._select_symbol = tk.Button(self._popup_window, text="Activate",
                                  bg="darkgreen", fg=FG_COLOR, font=GLOBAL_FONT, width=10,
                                  command=self._switch_button)
        self._select_symbol.grid(row=1, column=3, padx=10, pady=10)

    def _switch_button(self):
        # darkred
        if self._select_symbol['text'] == "Deactivate":
            self._select_symbol.config(bg="darkgreen", text="Activate")
            self._delete_row(self._body_index-1)
        else:
            self._select_symbol.config(bg="darkred", text="Deactivate")
            self._add_strategy_row()


    def _load_workspace(self):

        data = self.db.get("strategies")

        for row in data:
            self._add_strategy_row()

            b_index = self._body_index - 1

            for base_param in self._base_params:
                code_name = base_param['code_name']

                if base_param['widget'] == tk.OptionMenu and row[code_name] is not None:
                    self.body_widgets[code_name + "_var"][b_index].set(row[code_name])
                elif base_param['widget'] == tk.Entry and row[code_name] is not None:
                    self.body_widgets[code_name][b_index].insert(tk.END, row[code_name])

            extra_params = json.loads(row['extra_params'])

            for param, value in extra_params.items():
                if value is not None:
                    self.additional_parameters[b_index][param] = value
