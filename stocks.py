import yfinance as yahoo_finance
from config import API_KEY, API_SECRET
import requests
import json
from datetime import datetime, timedelta
import holidays
import pandas as pd

us_holidays = holidays.UnitedStates()
def get_last_market_day():
    c = 1
    date = datetime.today()
    while (not date.isoweekday() in range(1, 6)) or date in us_holidays:
        date = datetime.today() - timedelta(days=c)
        c += 1
    return str(date)[:10]

def today():
    return str(datetime.now())[:10]
    #.strftime("%Y-%m-%d")

class YahooFinance(object):

    def __init__(self, source='yahoo_finance'):

        self.source = yahoo_finance

    def latest_price(self, symbol):
        try:
            ticker = self.source.Ticker(symbol)
        except:
            return False
        return ticker.info['ask']

    def open_price(self, symbol):
        try:
            ticker = self.source.Ticker(symbol)
        except:
            return False
        return ticker.info['open']

class PolygonRest(object):

    def __init__(self):

        self.base = 'https://api.polygon.io'
        self.key = API_KEY

    def latest_price(self, symbol):
        req_url = f'{self.base}/v1/last/stocks/{symbol}?apiKey={self.key}'
        data = requests.get(req_url).json()
        return float(data['last']['price'])

    def open_price(self, symbol):
        try:
            req_url = f'{self.base}/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}?apiKey={self.key}'
            data = requests.get(req_url).json()
            return data['ticker']['day']['o']
        except:
            req_url = f'{self.base}/v2/aggs/ticker/{symbol}/prev?apiKey={self.key}'
            data = requests.get(req_url).json()
            return data['results'][0]['o']

    def get_stats(self, symbol):
        if today() == get_last_market_day():
            req_url = f'{self.base}/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}?apiKey={self.key}'
            data = requests.get(req_url).json()
            day = data['ticker']['day']
        else:
            req_url = f'{self.base}/v2/aggs/ticker/{symbol}/prev?apiKey={self.key}'
            data = requests.get(req_url).json()
            day = data['results'][0]
        return day['o'], day['h'], day['l']


    def get_aggregate(self, symbol):
        date = get_last_market_day()
        req_url = f'{self.base}/v2/aggs/ticker/{symbol}/range/1/minute/{date}/{date}?apiKey={self.key}'
        data = requests.get(req_url).json()['results']
        o, h, l, c = [], [], [], []
        for b in data:
            o.append(b['o'])
            h.append(b['h'])
            l.append(b['l'])
            c.append(b['c'])
        return o, h, l, c


    def lookup(self, query):
        req_url = f'https://api.polygon.io/v2/reference/tickers?sort=ticker&locale=US&search={query}&perpage=5&page=1&apiKey={self.key}'
        data = requests.get(req_url).json()
        for t in data['tickers']:
            if t['currency'] == 'USD':
                return t['ticker']

    def get_info(self, symbol):
        req_url = f'https://api.polygon.io/v1/meta/symbols/{symbol}/company?apiKey={self.key}'
        data = requests.get(req_url).json()
        if 'error' in data:
            return False
        return data
