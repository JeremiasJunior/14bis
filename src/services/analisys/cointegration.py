import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import coint

from datetime import datetime
from arch.unitroot import engle_granger

class cointegration_test:

    def __init__(self, hist_dict, threshold):

        symbols = hist_dict.keys()

        coint_list = []

        for s_1 in symbols:

            for s_2 in symbols:
            
                if s_1 != s_2:

                    pvalue = self.cointegration_test(hist_dict[s_1], hist_dict[s_2])

                    if pvalue < threshold:
                        
                        coint_list.append([s_1, s_2, pvalue])

        return coint_list


    def cointegration_test(self, dfx, dfy):
        
        pvalue = engle_granger(dfx['close'], dfy['close'], trend='n').pvalue

        return pvalue