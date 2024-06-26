import yfinance as yf
import pandas as pd
import requests
from dotenv import load_dotenv
import os
from concurrent.futures import ThreadPoolExecutor

def getIncome(ticker):
    return ticker.quarterly_income_stmt.transpose()
def getBalance(ticker):
    return ticker.quarterly_balance_sheet.transpose()   
def getInfo(ticker):
    return ticker.info
def getCashflow(ticker):
    return ticker.cash_flow.transpose()

def checkData(tickerData):
    for key in tickerData.keys(): #make sure the all numerical data is a number
        if (not key == 'lName' and not key == 'tickerSymbol' 
            and not key == 'ticker' and not key == 'reportDate' 
            and str(tickerData[key])[0] < 'z' and str(tickerData[key])[0] > 'A'):
            tickerData[key] = 0

class Ticker: #initialize ticker with at least the ticker symbol
    def __init__(self, tickerSymbol, revenue=0, ebitda=0, netIncome = 0, 
                 debt=0, cash=0, shares=0, CFO=0, TaxRate=0, PE = 0, 
                 marketCap = 0, enterpriseValue = 0, enterpriseToRevenue = 0, 
                 enterpriseToEbitda = 0, eps = 0, beta = 0, fPE = 0, lName = '',
                 targetMeanPrice = 0, previousClose=0):
        self.tickerSymbol = tickerSymbol.upper()
        self.ticker = yf.Ticker(self.tickerSymbol) 
        tickerInfo = self.ticker.info
        self.revenue = revenue
        self.ebitda = ebitda
        self.netIncome = netIncome
        self.debt = debt
        self.cash = cash
        self.shares = shares
        self.CFO = CFO
        self.TaxRate = TaxRate
        #grab data from yfinace that is updated frequently.
        try:
            self.reportDate = tickerInfo['mostRecentQuarter']
        except KeyError:
            self.reportDate = ''
            self.tickerSymbol = -1
        if 'trailingPE' in tickerInfo.keys():
            self.PE = tickerInfo['trailingPE']
        elif 'forwardPE' in tickerInfo.keys():
            self.PE = tickerInfo['forwardPE']
        else: 
            self.PE = PE 
        if 'marketCap' in tickerInfo.keys():
            self.marketCap = tickerInfo['marketCap']
        else:
            self.marketCap = marketCap
        if 'enterpriseValue' in tickerInfo.keys():
            self.enterpriseValue = tickerInfo['enterpriseValue']
        else: 
            self.enterpriseValue = enterpriseValue
        if 'enterpriseToRevenue' in tickerInfo.keys():
            self.enterpriseToRevenue = tickerInfo['enterpriseToRevenue']
        else: 
            self.enterpriseToRevenue = enterpriseToRevenue
        if 'enterpriseToEbitda' in tickerInfo.keys():
            self.enterpriseToEbitda = tickerInfo['enterpriseToEbitda']
        else: 
            self.enterpriseToEbitda = enterpriseToEbitda
        if 'trailingEps' in tickerInfo.keys():
            self.eps = tickerInfo['trailingEps']
        elif 'forwardEps' in tickerInfo.keys(): 
            self.eps = tickerInfo['forwardEps']
        else:
            self.eps = eps
        if 'beta' in tickerInfo.keys():
            self.beta = tickerInfo['beta']
        else:
            self.beta = beta
        if 'previousClose' in tickerInfo.keys():
            self.previousClose = tickerInfo['previousClose']
        else:
            self.previousClose = previousClose
        if 'forwardPE' in tickerInfo.keys():
            self.fPE = tickerInfo['forwardPE']
        else:
            self.fPE = fPE
        if 'longName' in tickerInfo.keys():
            self.lName = tickerInfo['longName']
        else:
            self.lName = lName
        if 'targetMeanPrice' in tickerInfo.keys():
            self.targetMeanPrice = tickerInfo['targetMeanPrice']
        else:
            self.targetMeanPrice = targetMeanPrice
        
    #fills out data from database    
    def updateFromDatabase(self, revenue, ebitda, netIncome, debt, cash, shares, 
                 CFO, TaxRate):
        self.revenue = revenue
        self.ebitda = ebitda
        self.netIncome = netIncome
        self.debt = debt
        self.cash = cash
        self.shares = shares
        self.CFO = CFO
        self.TaxRate = TaxRate
    #pulls new feed from alpha vantage api and do sentiment analysis
    def sentimentAnalysis(self):
        load_dotenv()
        alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY')
        symbol = self.ticker.info['symbol'].upper().strip()
        #get data from alpha vantage
        url = "https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={}&apikey={}".format(symbol, alpha_vantage_key)
        try:
            r = requests.get(url)
        except:
            return -1
        data = r.json() #store json 
        bearish = 0
        somewhatBearish = 0
        somewhatBullish = 0
        Bullish = 0
        #goes through every article and grabbs sentiment rating
        #based own rating construct score to determine sentiment
        for feed in data['feed']: 
            for sentiment in feed['ticker_sentiment']:
                if sentiment['ticker'] == symbol: 
                    if sentiment['ticker_sentiment_label'] == "Bearish":
                        bearish += 1
                    elif sentiment['ticker_sentiment_label'] == 'Somewhat-Bearish':
                        somewhatBearish += 1
                    elif sentiment['ticker_sentiment_label'] == 'Somewhat-Bullish':
                        somewhatBullish += 1
                    elif sentiment['ticker_sentiment_label'] == 'Bullish':
                        Bullish += 1
       
        return {'Bearish' : bearish, 'Somewhat Bearish': somewhatBearish,
                'Somewhat Bullish' : somewhatBullish, 'Bullish' : Bullish}
    
        
    def pullData(self): #grabs all necessary data from yfinance
        ticker = self.ticker
        with ThreadPoolExecutor(max_workers=5) as executor:
            f_tickerIncome = executor.submit(getIncome, ticker)
            f_tickerBalance = executor.submit(getBalance, ticker)                                                              
            f_tickerCashFlow = executor.submit(getCashflow, ticker)
            f_tickerInfo = executor.submit(getInfo, ticker)
            tickerIncome = f_tickerIncome.result()
            tickerBalance = f_tickerBalance.result()                                                              
            tickerCashFlow = f_tickerCashFlow.result() 
            tickerInfo = f_tickerInfo.result()
        
        self.marketCap = ticker.info['marketCap']
        revenue = 0
        ebitda = 0
        netIncome = 0 
        cfo = tickerCashFlow['Cash Flow From Continuing Operating Activities'].iloc[0]
        for i in range(4): 
            revenue += tickerIncome['Total Revenue'].iloc[i]
            ebitda += tickerIncome['EBITDA'].iloc[i]
            netIncome += tickerIncome['Net Income'].iloc[i] 
            
        self.revenue = revenue
        self.ebitda = ebitda
        self.netIncome = netIncome                                                                                                
        if 'totalCash' in tickerInfo.keys():
            self.cash = tickerInfo['totalCash']
        elif "Total Debt" in tickerBalance.keys():
            self.cash = tickerBalance['Cash Cash Equivalents And Short Term Investments'].iloc[0]
        else: 
            self.cash = 0
        if 'totalDebt' in tickerInfo.keys():
            self.debt = tickerInfo['totalDebt']
        elif "Total Debt" in tickerBalance.keys():
            self.debt = tickerBalance['Total Debt'].iloc[0]
        else: 
            self.debt = 0
        self.shares = tickerInfo['sharesOutstanding'] 
        self.CFO = cfo
        self.TaxRate = tickerIncome['Tax Rate For Calcs'].iloc[0]
      
    def getData(self): #return dictionary of data
        tickerData =  {'tickerSymbol': self.tickerSymbol, 'ticker' : self.ticker,
                       'revenue': self.revenue,'ebitda' : self.ebitda, 
                'netIncome' : self.netIncome,'debt' : self.debt,'cash' : self.cash,
                'shares' : self.shares,'CFO' : self.CFO,'TaxRate' : self.TaxRate,
                'PE' : self.PE, 'marketCap' : self.marketCap,
                'enterpriseValue' : self.enterpriseValue, 
                'enterpriseToRevenue' : self.enterpriseToRevenue, 
                'enterpriseToEbitda' : self.enterpriseToEbitda,'eps' : self.eps, 
                'beta' : self.beta, 'reportDate': self.reportDate, 
                'previousClose' : self.previousClose, 'fPE' : self.fPE, 'lName' : self.lName,
                'targetMeanPrice' : self.targetMeanPrice}
        checkData(tickerData)
        return tickerData
                                       

        

        
