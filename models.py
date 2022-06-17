import dateutil.parser
import datetime

BITMEX_MULTIPLIER = 0.00000001
BITMEX_TF_MINTUES = {"1m": 1, "5m": 5, "1h": 60, "1d": 1440}


class Balance:
    def __init__(self, info, exchange):
        if exchange == "binance":
            self.initial_margin = float(info['initialMargin'])
            self.maintenance_margin = float(info['maintMargin'])
            self.margin_balance = float(info['marginBalance'])
            self.wallet_balance = float(info['walletBalance'])
            self.unrealized_pnl = float(info['unrealizedProfit'])
        elif exchange == "bitmex":
            # it returns satoshi values
            self.initial_margin = float(info['initMargin']) * BITMEX_MULTIPLIER
            self.maintenance_margin = float(info['maintMargin']) * BITMEX_MULTIPLIER
            self.margin_balance = float(info['marginBalance']) * BITMEX_MULTIPLIER
            self.wallet_balance = float(info['walletBalance']) * BITMEX_MULTIPLIER
            self.unrealized_pnl = float(info['unrealisedPnl']) * BITMEX_MULTIPLIER


class Candle:
    def __init__(self, candle_info, timeframe, exchange):
        if exchange == "binance":
            self.timestamp = candle_info[0]
            self.open = float(candle_info[1])
            self.high = float(candle_info[2])
            self.low = float(candle_info[3])
            self.close = float(candle_info[4])
            self.volume = float(candle_info[5])
        elif exchange == "bitmex":
            self.timestamp = dateutil.parser.isoparse(
                candle_info['timestamp'])  # originally returns a standard string called ISO 8601 -> datetime object
            self.timestamp = self.timestamp - datetime.timedelta(minutes=BITMEX_TF_MINTUES[timeframe])
            # print(self.timestamp)
            self.timestamp = int(self.timestamp.timestamp() * 1000)  # -> convert to Unix timestamp in seconds
            self.open = candle_info['open']
            self.high = candle_info['high']
            self.low = candle_info['low']
            self.close = candle_info['close']
            self.volume = candle_info['volume']

        elif exchange =="parse_trades":
            self.timestamp = candle_info['ts']
            self.open = candle_info['open']
            self.high = candle_info['high']
            self.low = candle_info['low']
            self.close = candle_info['close']
            self.volume = candle_info['volume']


def tick_to_decimals(tick_size: float) -> int:
    tick_size_str = "{0:.8f}".format(tick_size)

    while tick_size_str[-1] == "0":
        tick_size_str = tick_size_str[:-1]

    split_tick = tick_size_str.split(".")

    if len(split_tick) > 1:
        return len(split_tick[1])
    else:
        return 0


class Contract:
    def __init__(self, contract_info, exchange):
        if exchange == "binance":
            self.symbol = contract_info['symbol']
            self.base_asset = contract_info['baseAsset']
            self.quote_asset = contract_info['quoteAsset']
            self.price_decimals = contract_info['pricePrecision']
            # round the price of an order to a decimal accepted by Binance
            self.quantity_decimals = contract_info['quantityPrecision']
            # round the quantity of an order to a decimal accepted by Binance
            self.tick_size = 1 / pow(10, contract_info['pricePrecision'])
            self.lot_size = 1 / pow(10, contract_info['quantityPrecision'])
        elif exchange == "bitmex":
            self.symbol = contract_info['symbol']
            self.base_asset = contract_info['rootSymbol']
            self.quote_asset = contract_info['quoteCurrency']
            self.price_decimals = tick_to_decimals(contract_info['tickSize'])
            self.quantity_decimals = tick_to_decimals(contract_info['lotSize'])
            self.tick_size = contract_info['tickSize']
            self.lot_size = contract_info['lotSize']

            self.quanto = contract_info['isQuanto']
            self.inverse = contract_info['isInverse']

            self.multiplier = contract_info['multiplier'] * BITMEX_MULTIPLIER

            if self.inverse:
                self.multiplier *= -1

        self.exchange = exchange


class OrderStatus:
    def __init__(self, order_info, exchange):
        if exchange == "binance":
            self.order_id = order_info['orderId']
            self.status = order_info['status'].lower()
            self.avg_price = float(order_info['avgPrice'])
        elif exchange == "bitmex":
            self.order_id = order_info['orderID']
            self.status = order_info['ordStatus'].lower()
            self.avg_price = order_info['avgPx']

class Trade:
    def __init__(self, trade_info):
        self.time: int = trade_info['time'] #entry time
        self.contract: Contract = trade_info['contract']
        self.strategy: str = trade_info['strategy']
        self.side: str = trade_info['side']
        self.entry_price: float = trade_info['entry_price']
        self.status: str = trade_info['status']
        self.pnl: float = trade_info['pnl']
        self.quantity = trade_info['quantity']
        self.entry_id = trade_info['entry_id']
