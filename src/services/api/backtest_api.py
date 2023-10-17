import pandas as pd
import datetime

from collections import deque

from secrets import token_hex as token

class Backtest_API:

    def __init__(self, symbol_data):

        
        self.symbols = symbol_data
        self.log = dict
        self._order_queue = deque()
        self.orders = {}
        
        #self.historical_data = historical_data
        
    def __str__(self):
        return 'Backtest_API'
    
    @classmethod
    def current_price(self, symbol, index, column='close'):

        try:
            current_price = symbol[column][index]
        except:
            current_price = 0
        
        return [current_price, current_price]
    
    def open_buy(self, symbol:str, volume:int, index:int) -> list:
        
        open_price  = Backtest_API.current_price(self.symbols[symbol], index)[0]
        order_number = token(6)
        
        open_date = str(self.symbols[symbol]['date'][index])

        self.orders[order_number] = {'number':order_number,'symbol':symbol, 'price':open_price, 'type':'buy', 'volume':volume, 'index':index, 'status':'open'}

        return [open_price, order_number, open_date, volume]

    def open_sell(self, symbol:str, volume:int, index:int) -> list:
        
        open_price  = Backtest_API.current_price(self.symbols[symbol], index)[1]
        order_number = token(6)
        
        open_date = str(self.symbols[symbol]['date'][index])

        self.orders[order_number] = {'number':order_number, 'symbol':symbol, 'price':open_price, 'type':'sell', 'volume':volume, 'index':index, 'status':'open'}

        return [open_price, order_number, open_date, volume]
    	

    def close_position(self, order_number:str, index:int) -> dict:

        order_type = self.orders[order_number]['type']
        open_price = self.orders[order_number]['price']
        vol = self.orders[order_number]['volume']
        symbol = self.orders[order_number]['symbol']
        number = self.orders[order_number]['number'] 

        close_date = str(self.symbols[symbol]['date'][index])

        filled_price = Backtest_API.current_price(self.symbols[symbol], index)[0]


        profit = 0

        if order_type == 'buy':
            profit = filled_price - open_price

        if order_type == 'sell':
            profit = open_price - filled_price
        
        self.orders[order_number]['status'] = 'close'
        self.orders[order_number]['profit'] = profit
        self.orders[order_number]['close_profit'] = filled_price
        self.orders[order_number]['close_index'] = index

        return [open_price, close_date, filled_price, vol, profit, number]

    def buy(self, symbol, index):

        ticket = token(6)



        
    