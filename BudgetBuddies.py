import yfinance as yf
from fredapi import Fred
import equations as eq
from tickerData import Ticker
fred = Fred(api_key='a02d5cbed56418e2d72837659e22b8ca')
ten_year_treasury_rate = fred.get_series_latest_release('GS10') / 100

'''
Performs the Trade Comps calculation. 
Takes in the tickers being compared to along with the cash, debt, number of shares, and EPS of the target ticker.
Returns a dictionary with the three calculated shares prices on revenue, EBITDA, and net income/Price to Earnings
'''
def TradeComps(toComp, tickerData):
    AVG_rev_multi = 0 
    AVG_EBITDA_multi = 0
    AVG_PE_ratio = 0
    revNum = 0
    ebitdaNum = 0
    netIncNum = 0
    for tick in toComp: 
        tick.pullData()
        tickData = tick.getData()
        if tickData['enterpriseValue'] == 0:
            EV = eq.enterprise_value(tickData['marketCap'],tickData['debt'],tickData['cash'])
        else: 
            EV = tickData['enterpriseValue']
        if tickData['enterpriseToRevenue'] == 0:
            AVG_rev_multi += eq.revenue_multiple(EV, tickData['revenue'])
            revNum+=1
        elif tickData['revenue'] > 0: 
            AVG_rev_multi += tickData['enterpriseToRevenue']
            revNum+=1
        if tickData['enterpriseToEbitda'] <= 0:
            AVG_EBITDA_multi += eq.ebitda_multiple(EV, tickData['ebitda'])
            ebitdaNum+=1
        else: 
            AVG_EBITDA_multi += tickData['enterpriseToEbitda']
            ebitdaNum+=1
        if tickData['PE'] > 0: 
            AVG_PE_ratio += tickData['PE']
            netIncNum+=1
    AVG_rev_multi /= revNum
    AVG_EBITDA_multi /= ebitdaNum
    AVG_PE_ratio /= netIncNum
    revenue_SharePrice = eq.impliedSharePriceRevenue(eq.impliedValueRevenue(eq.implied_ev_from_revenue(AVG_rev_multi,tickerData['revenue']),tickerData['cash'],tickerData['debt']),tickerData['shares'])
    ebitda_SharePrice = eq.impliedSharePriceEBITDA(eq.impliedValueEBITDA(eq.implied_ev_from_ebitda(AVG_EBITDA_multi,tickerData['ebitda']),tickerData['cash'],tickerData['debt']),tickerData['shares'])
    NetIncome_SharePrice = eq.impliedSharePriceNetIncome(eq.impliedValueNetIncome(tickerData['eps'], tickerData['shares'], AVG_PE_ratio),tickerData['shares'])
    AVG_SharePrice = (revenue_SharePrice + ebitda_SharePrice + NetIncome_SharePrice) / 3
    
    return {"revenue_SharePrice" : revenue_SharePrice, "ebitda_SharePrice" : ebitda_SharePrice, "netIncome_SharePrice" : NetIncome_SharePrice, "average_SharePrice" : AVG_SharePrice}

'''
Performs the Discounted Cash Flow calculation.
Takes in the ticker, an averages estimated per year growth, the cashflow sheet, cash, debt, market cap, and number of shares of a given ticker.
It returns a dictionary with the calculated shares price with the first and last year cash flow.
'''

def DiscountedCashFlow(tickerData,PerYGrowth):
    cash = tickerData['cash']
    debt = tickerData['debt']
    shares = tickerData['shares']
    marketCap = tickerData['marketCap']
    risk_free_rate = ten_year_treasury_rate.iloc[-1]
    TargetGrowthRate = .03
    ExpectedReturn = .08
    CostofDebt = .03
    EquityCost = eq.equityCost(tickerData['beta'], ExpectedReturn, risk_free_rate)
    EquityPercent = eq.equityPercent(marketCap + debt, debt)
    DebtPercent = eq.debtPercent(debt,marketCap+debt)
    wacc = eq.WACC(EquityPercent,EquityCost,DebtPercent,CostofDebt,tickerData['TaxRate'])
    presentValueSum = eq.presentValue(tickerData['CFO'],wacc,1)
    futureCFO = []
    temp = tickerData['CFO']
    for i in range(4):
        temp *= (1 + PerYGrowth)
        futureCFO.append(temp)
        presentValueSum += eq.presentValue(temp,wacc,i+2)
    terminalValue = eq.tVal(futureCFO[3],TargetGrowthRate,wacc)
    PresentOfTerminal = eq.presentTerminalValue(terminalValue,wacc,5)
    EnterpriseValue = eq.enVal(presentValueSum,PresentOfTerminal)
    EquityValue = eq.eVal(EnterpriseValue,cash,debt)
    ImpliedSharePrice = eq.sharePriceImpl(EquityValue, shares)
    return {"ImpliedSharePrice" : ImpliedSharePrice, "FreeCashFlow" : tickerData['CFO'], "LastYearCashFlow" : futureCFO[3]}

def main():
    print("Enter the ticker you would like to evaluate: ")
    tickerSymbols = ['GOOG','AMZN','AVGO','META','AAPL']
    for tickerSymbol in tickerSymbols:
        ticker = Ticker(tickerSymbol)
        ticker.pullData()
        tickerData = ticker.getData()
        print("CurrentReportDate -", tickerData['reportDate'])
        print("Ticker -", tickerSymbol)
        print("Revenue -", tickerData['revenue'])
        print("EBITDA -", tickerData['ebitda'])
        print("Debt -", tickerData['debt'])
        print("Cash -", tickerData['cash'])
        print("Shares -", tickerData['shares'])
        print("CFO -", tickerData['CFO'])
        print("TaxRate -", tickerData['TaxRate'])
    '''print("Enter five similiar companies to compare to:")
    toComp = [Ticker('MTSI'),Ticker('POWI'),
              Ticker('QRVO'),Ticker('RMBS'),Ticker('SLAB')]
    PerYGrowth = .25
    TradeCompPrices = TradeComps(toComp, tickerData)
    print("--Trading Comps--")
    print("Implied Share Price from Revenue: ", TradeCompPrices['revenue_SharePrice'])
    print("Implied Share Price from EBITDA: ", TradeCompPrices['ebitda_SharePrice'])
    print("Implied Share Price from P/E: ", TradeCompPrices['netIncome_SharePrice'])
    print("Average Share Price: ", TradeCompPrices['average_SharePrice'])
    print()
    print("--Discounted Cash Flow--")
    print("Discounted Cash Flow Implied Share Price: ", DiscountedCashFlow(tickerData,PerYGrowth))
    print("Real Share Price:", tickerData['ticker'].info['regularMarketPreviousClose'])'''

if __name__ == "__main__":
    main()