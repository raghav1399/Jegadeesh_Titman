# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 00:19:19 2020

@author: Raghav
"""

import pandas as pd
import datetime as dt
import pandas_datareader as pdr
import copy
import numpy as np
import pickle

#########PULLING DATA#########

url = "https://www.samco.in/knowledge-center/articles/nifty-50-companies/"
dfs = pd.read_html(url)

nifty_old = dfs[0]
string = '.NS'
tickers = list(map(lambda orig_string: orig_string + string, nifty_old["Symbol"]))

#with open('nifty_2019.pickle', 'wb') as input:
#    pickle.dump(tickers, input)

########PULLING MONTHLY DATA###########

#with open('nifty_2019.pickle', 'rb') as output:
#    tickers = pickle.load(output)
#
ohlc_dict = {}
attempt = 0
drop = []
start_date =  dt.date(2019, 1, 1)
end_date =  dt.date.today()
#
while len(tickers) != 0 and attempt <= 5:
    tickers = [j for j in tickers if j not in drop]
    for i in range(len(tickers)):
        try:
            print("Getting data for", tickers[i])
            ohlc_dict[tickers[i]] = pdr.get_data_yahoo(tickers[i], start_date, end_date, interval='d' )
            ohlc_dict[tickers[i]].dropna(inplace = True)
            drop.append(tickers[i])
           
        except:
           print(tickers[i], ":Failed to get data, retrying..")
            
        attempt += 1   
#        
#with open('dataset2.pickle', 'wb') as input:
#    pickle.dump(ohlc_dict, input)
#        

######Massaging the data to get monthly returns#########
#with open('dataset2.pickle', 'rb') as output:
#    ohlc_dict = pickle.load(output)


ohlc = copy.deepcopy(ohlc_dict)
returns = pd.DataFrame()
stock_list = []
lb_start = dt.date(2019, 1, 1)
lb_end = dt.date(2019, 11, 29)

for ticker in tickers:
    ohlc[ticker]["ret"] = ohlc[ticker]["Adj Close"].pct_change()
    returns[ticker] = (1+ohlc[ticker]["ret"].loc[lb_end:lb_end]).cumprod()
    
stock_list = returns.tail(1)
stock_list = stock_list.transpose()
stock_list = stock_list.reset_index()
stock_list.columns = ["ticker", "Return"]
stock_list.sort_values(by = "Return", ascending = False, inplace = True)

long_tickers = stock_list["ticker"].head(5).values.tolist()
short_tickers = stock_list["ticker"].tail(5).values.tolist()

##########Loading test data, taking position######

new_tickers = long_tickers + short_tickers
state = {}
strategy_return = {}
test = {}
st = dt.date(2020, 1, 1)
en = dt.date(2020, 3, 31)

for ticker in new_tickers:
    test[ticker]= ohlc[ticker].loc[st:en]
    strategy_return[ticker] = []
    state[ticker] = ""
    #test_df[ticker]["actual return"] = test_df[ticker]["Adj Close"].pct_change()
    
test_df = copy.deepcopy(test)

for ticker in new_tickers:
    for i in range(1,len(test_df[ticker])):
        if state[ticker] == "":
            strategy_return[ticker].append(0)
            if ticker in long_tickers:
                state[ticker] = "Buy"
            elif ticker in short_tickers:
                state[ticker] = "Sell"
      
        if state[ticker] == "Buy":
            strategy_return[ticker].append((test_df[ticker]["Adj Close"][i]/test_df[ticker]["Adj Close"][i-1])-1)
        
        if state[ticker] == "Sell":
            strategy_return[ticker].append(1-(test_df[ticker]["Adj Close"][i]/test_df[ticker]["Adj Close"][i-1]))
            
            
    test_df[ticker]["actual_return"] = np.array(strategy_return[ticker])
    
    
####DEFINING KPI ############# 252 days used as we have daily data only ##########
def CAGR(DF):
    "function to calculate the Cumulative Annual Growth Rate of a trading strategy"
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()
    n = len(df)/(252)
    CAGR = (df["cum_return"].tolist()[-1])**(1/n) - 1
    return CAGR

def volatility(DF):
    "function to calculate annualized volatility of a trading strategy"
    df = DF.copy()
    vol = df["ret"].std() * np.sqrt(252)
    return vol

def sharpe(DF,rf):
    "function to calculate sharpe ratio ; rf is the risk free rate"
    df = DF.copy()
    sr = (CAGR(df) - rf)/volatility(df)
    return sr
    

def max_dd(DF):
    "function to calculate max drawdown"
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()
    df["cum_roll_max"] = df["cum_return"].cummax()
    df["drawdown"] = df["cum_roll_max"] - df["cum_return"]
    df["drawdown_pct"] = df["drawdown"]/df["cum_roll_max"]
    max_dd = df["drawdown_pct"].max()
    return max_dd    


# calculating overall strategy's KPIs
strategy_df = pd.DataFrame()
for ticker in new_tickers:
    strategy_df[ticker] = test_df[ticker]["actual_return"]
strategy_df["ret"] = strategy_df.mean(axis=1)
print("CAGR", CAGR(strategy_df))
print("SHARPE", sharpe(strategy_df,0.075))
print("DD", max_dd(strategy_df))


###

# vizualization of strategy return
(1+strategy_df["ret"]).cumprod().plot()

#####Comparison with Nifty#####

#calculating KPIs for Index buy and hold strategy over the same period
Index = pdr.get_data_yahoo("^NSEI",st,en,interval='d')
Index["ret"] = Index["Adj Close"].pct_change()
print(CAGR(Index))
print(sharpe(Index,0.075))
print(max_dd(Index))

(1+Index["ret"]).cumprod().plot()


            

                 
    
     



  
    


    















