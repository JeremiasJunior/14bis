import pandas as pd
import numpy as np
import os



import math

from secrets import token_hex as token

#o objetivo tem que ser fazer de uma forma tal que fique 
#o mais semelhante possivel, do backtest para o live_trade
from api.backtest_api import Backtest_API


class Backtest:

    def __init__(self):
        #aqui definir as variaveis globais da classe
        self.log = {}

        #self.loop_series = {'price_x':[], 'price_y':[], 'spread':[], 'time':[]}
        #self.serie = {'return':[], 'expo':[]}
        #self.profit_serie = {'symbol_x':[], 'symbol_y':[], 'percentage':[]}
        #self.info = {'symbol_x':str, 'symbol_y':str}

        #self.profit = float()
        #self.positions = {}
        #self.positions_list = []

        
        
    #tô removendo por enquanto os paramentros de min_count, stop_number 

    def __call__(self, symbol_x:str, 
                       symbol_y:str,
                       df:pd.DataFrame,
                       column:str,
                       short_spread:float,
                       long_spread:float,
                       p_size:int,
                       period:int,
                       tp:float,
                       sl:float,
                       model:str,
                       ):
        
        position_open = False
        position_key = str()
        
        df_x = df[symbol_x]
        df_y = df[symbol_y]
        
        tp_short = 0
        tp_long = 0
        min_count = 1

        df_index = df_x.index
        df_iteration = 0

        loop_series = {'price_x':[], 'price_y':[], 'spread':[], 'time':[]}
        serie = {'return':[], 'expo':[]}
        profit_serie = {'symbol_x':[], 'symbol_y':[], 'percentage':[]}
        info = {'symbol_x':str, 'symbol_y':str}

        #self.profit = float()
        positions = {}
        positions_list = []

        ##

        self.info = {'symbol_x':symbol_x, 
                     'symbol_y':symbol_y, 
                     'short_spread':short_spread, 
                     'long_spread':long_spread,
                     'position_size':p_size,
                     'period':period,
                     'date':[str(df_x.index[0]), str(df_x.index[-1])]}

        df_size = len(df_x[column])


        index_list = []

        self.API = Backtest_API(df)
        count = 0

        for df_iteration in range(len(df_index)): ##loop

            

            index_list.append(df_iteration)
            date = df_index[df_iteration]

            can_trade = True

            current_x_price = df_x[column][df_iteration]
            current_y_price = df_y[column][df_iteration]

            loop_series['price_x'].append(current_x_price)
            loop_series['price_y'].append(current_y_price)
            loop_series['time'].append(date)

            returns = 0

            if len(loop_series['time']) >= period:

                if len(loop_series['spread']) == 0:

                    can_trade = False

                
                x_period = self.m_movel(period, loop_series['price_x'])
                y_period = self.m_movel(period, loop_series['price_y'])

                spread_today = self.spread(x_period, y_period)
                
                loop_series['spread'].append(spread_today)
                
                
                ratio = self.roundlot(current_x_price, current_y_price, p_size)
                
                if can_trade: 

                    ### SHORT-SPREAD ###

                    if(spread_today > short_spread) and (position_open == False):

                        short_data = self.short_spread(symbol_x, symbol_y, ratio, df_iteration)
                        
                        current_exposition = short_data['price_x']*short_data['volume_x'] + short_data['price_y']*short_data['volume_y']
                        position_key = short_data['key']
                        position_open = True

                        open_count = 0


                    ### LONG-SPREAD ###

                    if(spread_today < long_spread) and (position_open == False):
                        
                        long_data = self.long_spread(symbol_x, symbol_y, ratio, df_iteration)
                        
                        current_exposition = long_data['price_x']*long_data['volume_x'] + long_data['price_y']*long_data['volume_y']
                        position_key = long_data['key']
                        position_open = True

                        open_count = 0


                    force_close = False


                    ### CLOSE 

                    if position_open == True:
                        

                        
                        if self.log[position_key]['type'] == 'long_spread':
                           

                            if self.force_close(current_x_price, 
                                            self.log[position_key]['buy_price_y'],
                                            self.log[position_key]['sell_price_x'],
                                            current_y_price,
                                            self.log[position_key]['volume_x'],
                                            self.log[position_key]['volume_y'],
                                            self.log[position_key]['type'], tp=tp, sl=sl) == True:
                                
                                
                            
                                force_close = True
                            
                            if df_iteration >= len(df_index) - 10:
                                force_close = True
                            
                            if ((spread_today >= tp_long) and open_count >= min_count) or force_close == True:

                                returns = self.close_position(position_key, df_x, df_y, df_iteration)
                                position_open = False
                                
                                #position_key = 'empty'

                                serie['return'].append(returns)
                                
                                count = 0
                                if(model == 'c'):
                                    continue
                                if(model == 'once'):
                                    return positions_list
                                if(model == 'roi'):
                                    return self.log[position_key]['roi']
                                if(model == 'log'):
                                    return self.log[position_key]

                        if self.log[position_key]['type'] == 'short_spread':
                            
                            if self.force_close(self.log[position_key]['buy_price_x'],
                                                current_y_price,
                                                current_x_price,
                                                self.log[position_key]['sell_price_y'],
                                                self.log[position_key]['volume_x'],
                                                self.log[position_key]['volume_y'],
                                                self.log[position_key]['type'], tp=tp, sl=sl) == True:
                                
                                force_close = True
                                
                            if df_iteration >= len(df_index) - 10:
                                force_close = True
                                
                            if ((spread_today <= tp_short) and open_count >= min_count) or force_close == True:

                                returns = self.close_position(position_key, df_x, df_y, df_iteration)
                                position_open = False
                                #position_key = 'empty'

                                serie['return'].append(returns)

                                count = 0
                                if(model == 'c'):
                                    continue
                                if(model == 'once'):
                                    return positions_list
                                
                                if(model == 'roi'):
                                    return self.log[position_key]['roi']
                                if(model == 'log'):
                                    return self.log[position_key]
                        
                        count += 1
            

        return 0


    def short_spread(self, symbol_x:str, symbol_y:str, ratio:float, index:int):

        price_x, number_x, date_x, volume_x = self.API.open_buy(symbol_x, ratio[0], index)
        price_y, number_y, date_y, volume_y = self.API.open_sell(symbol_y, ratio[1], index)

        expo = price_y*volume_y + price_x*volume_x

        key = '{}'.format(token(8))

        self.log[key] = {'type':'short_spread',
                         'number_x':number_x,
                         'number_y':number_y, 
                         'type_x':'buy', 
                         'type_y':'sell', 
                         'symbol_x':symbol_x,
                         'symbol_y':symbol_y,
                         'buy_price_x':price_x,
                         'sell_price_x':None,
                         'sell_price_y':price_y,
                         'buy_price_y':None,
                         'volume_x':volume_x,
                         'volume_y':volume_y,
                         'open_date':date_x,
                         'close_date':None,
                         'profit_x':None,
                         'profit_y':None,
                         'profit':None,
                         'expo':expo,
                         'open_index':index}
        return {'key':key,
                'price_x':price_x,
                'price_y':price_y,
                'volume_x':volume_x,
                'volume_y':volume_y}
    
    def long_spread(self, symbol_x:int, symbol_y:int, ratio:float, index:int):

        price_x, number_x, date_x, volume_x = self.API.open_sell(symbol_x, ratio[0], index)
        price_y, number_y, date_y, volume_y = self.API.open_buy(symbol_y, ratio[1], index)

        expo = price_y*volume_y + price_x*volume_x

        key = '{}'.format(token(8))

        self.log[key] = {'type':'long_spread', 
                         'number_x':number_x,
                         'number_y':number_y, 
                         'type_x':'buy', 
                         'type_y':'sell', 
                         'symbol_x':symbol_x,
                         'symbol_y':symbol_y,
                         'buy_price_x':None,
                         'sell_price_x':price_x,
                         'sell_price_y':None,
                         'buy_price_y':price_y,
                         'volume_x':volume_x,
                         'volume_y':volume_y,
                         'open_date':date_x,
                         'close_date':None,
                         'profit_x':None,
                         'profit_y':None,
                         'profit':None,
                         'expo':expo,
                         'open_index':index}
        
        return {'key':key,
                'price_x':price_x,
                'price_y':price_y,
                'volume_x':volume_x,
                'volume_y':volume_y}
    
    def close_position(self, key:str, df_x:pd.DataFrame, df_y:pd.DataFrame, index:int):

        number_x = self.log[key]['number_x']
        number_y = self.log[key]['number_y']

        close_data_x = self.API.close_position(number_x, index)
        close_data_y = self.API.close_position(number_y, index)

        exposition = 0
        profit = 0

        close_date = close_data_x[1]

        volume_x = close_data_x[3]
        volume_y = close_data_y[3]

        current_price_x = self.API.current_price(df_x, index)[0]
        current_price_y = self.API.current_price(df_y, index)[0]

        self.log[key]['close_index'] = index

        #short_spread => X_BUY, Y_SELL
        #long_spread  => X_SELL, Y_BUY
        
        if self.log[key]['type'] == 'long_spread':
            
            self.log[key]['buy_price_x'] = current_price_x
            self.log[key]['sell_price_y'] = current_price_y
            
            open_price_x = self.log[key]['sell_price_x']
            open_price_y = self.log[key]['buy_price_y']
            close_price_x = self.log[key]['buy_price_x'] 
            close_price_y = self.log[key]['sell_price_y']


            profit_x = (open_price_x - close_price_x)*volume_x
            profit_y = (open_price_y - close_price_y)*volume_y

            profit = profit_x + profit_y

            self.log[key]['profit_x'] = profit_x
            self.log[key]['profit_y'] = profit_y
            self.log[key]['profit'] = profit
            self.log[key]['close_date'] = close_date

            self.log[key]['roi'] = profit/(open_price_x*volume_x + open_price_y*volume_y)

        if self.log[key]['type'] == 'short_spread':

            self.log[key]['sell_price_x'] = current_price_x
            self.log[key]['buy_price_y'] = current_price_y

            open_price_x = self.log[key]['buy_price_x']
            open_price_y = self.log[key]['sell_price_y']
            close_price_x = self.log[key]['sell_price_x']
            close_price_y = self.log[key]['buy_price_y']

            profit_x = (open_price_x - close_price_x)*volume_x
            profit_y = (open_price_y - close_price_y)*volume_y

            profit = profit_x + profit_y

            self.log[key]['profit_x'] = profit_x
            self.log[key]['profit_y'] = profit_y
            self.log[key]['profit'] = profit
            self.log[key]['close_date'] = close_date

            self.log[key]['roi'] = profit/(open_price_x*volume_x + open_price_y*volume_y)
        
        #self.positions_list.append(self.log[key])

        return profit


    def force_close(self, buy_price_x:float, buy_price_y:float, sell_price_x:float, sell_price_y:float, volume_x:int, volume_y:int, type:str, tp=0.06, sl=-0.03):
        
        if(type == 'long_spread'):
            current_profit = 0
            current_profit_x = (sell_price_x - buy_price_x)*volume_x #short
            current_profit_y = (buy_price_y - sell_price_y)*volume_y #long
            current_profit = current_profit_x + current_profit_y
            expo = buy_price_y*volume_y + buy_price_x*volume_x
            percentage = current_profit/expo

            #self.profit_serie['symbol_x'].append(current_profit_x)
            #self.profit_serie['symbol_y'].append(current_profit_y)
            #self.profit_serie['percentage'].append(percentage)
            

            if(percentage >= tp and percentage != 0):
                return True
            if(percentage <= sl and percentage != 0):
                return True
            
            return False

        if(type == 'short_spread'):
            current_profit = 0
            current_profit_x = (buy_price_x - sell_price_x)*volume_x
            current_profit_y = (sell_price_y - buy_price_y)*volume_y
            current_profit = current_profit_x + current_profit_y
            expo = buy_price_y*volume_y + buy_price_x*volume_x
            percentage = current_profit/expo

            #self.profit_serie['symbol_x'].append(current_profit_x)
            #self.profit_serie['symbol_y'].append(current_profit_y)
            #self.profit_serie['percentage'].append(percentage)



            if(percentage >= tp and percentage != 0):   
                return True
            if(percentage <= sl and percentage != 0):
                return True
            
            return False


    def roundlot(self, x_price:float, y_price:float, lot_size = 100000):
        
        alpha = lot_size/(2*x_price)
        beta = lot_size/(2*y_price)

        return alpha, beta
            
    def m_movel(self, period, data):

        #data_r = bkt_godhand._reverse(data)
        data_r = list(data).copy()

        data_r.reverse()
        data_r = data_r[0:int(period)]

        return np.array(data_r)
    
    def spread(self, x_period, y_period):

        spread = x_period/y_period
        spread = np.nan_to_num(spread)

        spread_z = (spread - spread.mean()) / np.std(spread)
        spread_today = spread_z[-1]
        
        return spread_today
