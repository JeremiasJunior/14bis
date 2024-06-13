import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime 
import numpy as np

from collections import deque

class MetaTrader_API:


    def __init__(self, _login: int, _password = str, _server = str):
        self.login = _login
        self.password = _password
        self.server = _server

        self._order_queue = deque()
        self.orders = {}

        try:
            mt5.initialize(login = self.login, password = self.password, server = self.server)
        except:
            print('error')
            quit()
    
    def __str__(self):
        return 'MetaTraderAPI'
        
    
    def current_price(self, symbol:str) -> tuple[float, float]:
    
        data = mt5.symbol_info(symbol)
    
        data = data._asdict()
        
        data_bid = float(data['bid'])
        data_ask = float(data['ask'])

        return [data_bid, data_ask]
    

    @classmethod
    def TIMEFRAME(self, timeframe:str) -> int:

        if(timeframe == 'M1'): return mt5.TIMEFRAME_M1
        if(timeframe == 'M5'): return mt5.TIMEFRAME_M5
        if(timeframe == 'M10'): return mt5.TIMEFRAME_M10
        if(timeframe == 'M30'): return mt5.TIMEFRAME_M30
        if(timeframe == 'H1'): return mt5.TIMEFRAME_H1
        if(timeframe == 'M12'): return mt5.TIMEFRAME_H12
        if(timeframe == 'D1'): return mt5.TIMEFRAME_D1


    def historical_data(self, symbol:str, from_date:str, to_date:str, timeframe:str) -> pd.DataFrame():

        utc_from = datetime.fromisoformat(from_date)
        utc_to = datetime.fromisoformat(to_date)



        rates = mt5.copy_rates_range(symbol, self.TIMEFRAME(timeframe), utc_from, utc_to)
        
        df = pd.DataFrame(rates)
        df['date'] = df['time']
        df['date'] = df['date'].apply(lambda time: datetime.fromtimestamp(time))

        historical_data = df.set_index('date')
    
        return historical_data
    
    def historical_data_cluster(self, symbols:list, from_date:str, to_date:str, timeframe:str) -> dict():
        
        historical_data_dict = {}

        for symbol in symbols:
            
            try:
                historical_data = self.historical_data(symbol, from_date, to_date, timeframe)
            except:
                historical_data = []

            historical_data_dict[symbol] = historical_data

        
        return historical_data_dict



    def current_book(self, symbol:str, len:int) -> pd.DataFrame():
        
        try:
            book = mt5.market_book_get(symbol)
        except:
            print("symbol doesn't exist!")

        book = mt5.market_book_get(symbol)
        book_ask = {'price':[], 'volume':[]}
        book_bid = {'price':[], 'volume':[]}

        for data in book:

            if(data[0] == 1): 
                book_ask['price'].append(data[1])
                book_ask['volume'].append(data[2])
            if(data[0] == 2):
                book_bid['price'].append(data[1])
                book_bid['volume'].append(data[2])

        book_ask = pd.DataFrame(book_ask)[1:]
        book_bid = pd.DataFrame(book_bid)[1:]
        
        book_ask['deep'] = book_ask.index[::-1]
        book_ask.set_index('deep')
        
        book_bid['deep'] = -(book_bid.index[::-1])
        book_bid.set_index('deep')

        result = pd.concat([book_bid, book_ask], axis=0)
        result = result.set_index('deep')
        result = result.sort_index(ascending=False)

        
        return result

    def open_buy(self, symbol:str, vol:float) -> tuple[float, int]:

        price = mt5.symbol_info_tick(symbol).ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": vol,
            "type": mt5.ORDER_TYPE_BUY,
            "sl": 0.0,
            "tp": 0.0,
            "deviation": 20,
            "price": price,
            "magic": 100,
            "comment": "python script open",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC, 
        }


        send = mt5.order_send(request)
        order_number = send[2]

        self.volume = vol
        ask_filled = send[4]

        self.orders[order_number] = {'number':order_number, 'price':ask_filled,'type':'buy', 'volume':vol, 'symbol':symbol, 'status':'open'}

        #self._order_queue.append({'number':order_number, 'price':ask_filled,'type':'buy', 'volume':vol, 'symbol':symbol})

        return [ask_filled, order_number]

    def open_sell(self, symbol:str, vol:float) -> tuple[float, int]:

        price = mt5.symbol_info_tick(symbol).bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": vol,
            "type": mt5.ORDER_TYPE_SELL,
            "price": price,
            "deviation": 20,
            "sl": 0.0,
            "tp": 0.0,
            "magic": 100,
            "comment": "python script open",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        send = mt5.order_send(request)
        
        order_number = send[2]
    	
        bid_filled = send[5]
        
        self.orders[order_number] = {'number':order_number, 'price':bid_filled,'type':'sell', 'volume':vol, 'symbol':symbol, 'status':'open'}
        #self._order_queue.append({'number':order_number, 'price':bid_filled,'type':'sell', 'volume':vol, 'symbol':symbol})

        return [bid_filled, order_number]


    def close_position(self, order_number:int) -> dict:

            #type = 0 : BUY
            #type = 1 : SELL

            try:
                
                order_type = self.orders[order_number]['type']
                open_price = self.orders[order_number]['price']
                vol = self.orders[order_number]['volume']
                symbol = self.orders[order_number]['symbol']
                number = self.orders[order_number]['number']

            except:
                return -1
            
            print(self.orders[order_number])

            #o problema tem que ta no request
            request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "position":number,
                    "volume": vol,
                    "type": mt5.ORDER_TYPE_SELL if order_type=='buy' else mt5.ORDER_TYPE_BUY,
                    "price": mt5.symbol_info_tick(symbol).bid if order_type=='buy' else mt5.symbol_info_tick(symbol).ask,
                    "sl": 0.0,
                    "tp": 0.0,
                    "magic": 234000,
                    "deviation":20,
                    "magic":100, 
                    "comment": "close position",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC, 
                    }
            
            send = mt5.order_send(request)

            self.orders[order_number]['status'] = 'close'

            #order_number = send[2]

            filled_price = send[4]

            profit = 0

            if order_type=='buy':
                profit = filled_price - open_price
            if order_type=='sell':
                profit = open_price - filled_price
            else:
                return 'profit error'

            return [open_price, filled_price, profit, order_number]

   
