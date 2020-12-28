import json
import os
from datetime import datetime

def read_json(f):
    with open(f, 'r') as df:
        return json.loads(df.read())

def dump_json(f, d):
    with open(f, 'w') as df:
        json.dump(d, df, indent=4)

def sdate():
    return str(datetime.now())[:19]

class Ledger(object):

    def __init__(self, file=None, init_balance=10e3):

        if file == None:
            os.system(f'touch data.json')
            file = 'data.json'
            dump_json(file, {})
        self.file = file
        self.init_balance = init_balance

    def get_data(self):
        return read_json(self.file)

    def dump_data(self, data):
        return dump_json(self.file, data)

    def add_user(self, id, name):
        data = self.get_data()
        data[id] = {
            'name': name,
            'time': sdate(),
            'balance': self.init_balance,
            'holdings': {},
        }
        self.dump_data(data)

    def enter_position(self, id, position, symbol, price, qty=None):

        data = self.get_data()
        balance = data[id]['balance']
        qty = balance/price if qty == None else qty
        cost = price * qty
        if cost > balance:
            return False
        data[id]['balance'] = balance - cost
        holdings = data[id]['holdings']
        if symbol not in holdings:
            holdings[symbol] = {
                'position': position,
                'entry_price': price,
                'qty': qty,
                'entry_time': sdate(),
            }
        else:
            hqty, ptype, eprice = (
                holdings[symbol]['qty'],
                holdings[symbol]['position'],
                holdings[symbol]['entry_price'],
            )
            if position != ptype:
                return False
            avg_entry_price = ((qty * price) + (hqty * eprice))/(qty + hqty)
            holdings[symbol]['entry_price'] = avg_entry_price
            holdings[symbol]['qty'] = qty + hqty

        self.dump_data(data)
        return qty

    def exit_position(self, id, position, symbol, price, qty=None):

        data = self.get_data()
        balance, holdings = (
            data[id]['balance'],
            data[id]['holdings'],
        )
        hqty, ptype, eprice = (
            holdings[symbol]['qty'],
            holdings[symbol]['position'],
            holdings[symbol]['entry_price'],
        )
        qty = hqty if qty == None else qty

        if (
            symbol not in holdings or
            qty > hqty or
            position == ptype
        ):
            return False
        if position == 'sell':
            data[id]['balance'] = balance + qty * price
        else:
            data[id]['balance'] = balance + qty * (2 * eprice - price)
        if hqty == qty:
            del holdings[symbol]
        else:
            holdings[symbol]['qty'] = hqty - qty
        self.dump_data(data)
        return qty

    def liquidate(self, id):
        data = self.get_data()
        holdings = data[id]['holdings']
        stocklist = []
        for symbol in holdings:
            stocklist.append((symbol, holdings[symbol]['qty']))
        data[id]['holdings'] = {}
        return stocklist
        #[('AAPL', 23), ('MST', 3)]

    def portfolio(self, id):
        data = self.get_data()
        holdings = data[id]['holdings']
        porf = []
        for symbol in holdings:
            hqty, ptype, eprice = (
                holdings[symbol]['qty'],
                holdings[symbol]['position'],
                holdings[symbol]['entry_price'],
            )
            porf.append((symbol, hqty, ptype, eprice))
        return porf


    def get_balance(self, id):
        data = self.get_data()
        if id not in data:
            return False
        return data[id]['balance']

    def get_all_owned(self):
        data = self.get_data()
        owned = {}
        for id in data:
            owned[id] = []
            holdings = data[id]['holdings']
            for sym in holdings:
                owned[id].append((sym, holdings[sym]['qty']))
        return owned

    def contains(self, id):
        return str(id) in self.get_data().keys()


#myid = '315929059353821194'
#ledger = Ledger(file='data.json')
#ledger.add_user(id='12312312', name='PC')
#status = ledger.enter_position(myid, 'buy', 'AAPL', 440, 2)
#print(ledger.leaderboard())
#ledger.exit_position(myid, 'sell', 'AAPL', 420, 1)
