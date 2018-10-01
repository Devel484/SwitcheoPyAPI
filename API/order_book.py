from API.trade import Trade


class OrderBook(object):


    def __init__(self, pair, offers=None):
        self.book = {}
        self.book[Trade.WAY_BUY] = []
        self.book[Trade.WAY_SELL] = []
        self.pair = pair
        self.timestamp = 0

        if offers:
            for offer in offers:
                self.add(offer)

    def get_timestamp(self):
        return self.timestamp

    def add(self, offer):

        self.book[offer.get_way()].append(offer)
        self.book[offer.get_way()] = sorted(self.book[offer.get_way()], key=lambda entry: entry.get_price(),
                                            reverse=(offer.get_way() == Trade.WAY_BUY))

    def reset(self):
        self.book = {}
        self.book[Trade.WAY_BUY] = []
        self.book[Trade.WAY_SELL] = []

    def print(self):
        print(self.timestamp)
        for i in range(len(self.book[Trade.WAY_SELL])-1,-1,-1):
            print("%.10f\t\t%.8f" % (self.book[Trade.WAY_SELL][i].get_price(),
                                     self.book[Trade.WAY_SELL][i].get_quote_amount()))
        print("-----------------------------------")
        for i in range(len(self.book[Trade.WAY_BUY])):
            print("%.10f\t\t%.8f" % (self.book[Trade.WAY_BUY][i].get_price(),
                                     self.book[Trade.WAY_BUY][i].get_quote_amount()))

    def sum_up(self):
        sum_base = 0
        sum_quote = 0
        for i in range(len(self.book[Trade.WAY_BUY])):
            offer = self.book[Trade.WAY_BUY][i]
            sum_base = sum_base + offer.get_base_amount()
            sum_quote = sum_quote + offer.get_quote_amount()
            offer.set_sum_base(sum_base)
            offer.set_sum_quote(sum_quote)

        sum_base = 0
        sum_quote = 0
        for i in range(len(self.book[Trade.WAY_SELL])):
            offer = self.book[Trade.WAY_SELL][i]
            sum_base = sum_base + offer.get_base_amount()
            sum_quote = sum_quote + offer.get_quote_amount()
            offer.set_sum_base(sum_base)
            offer.set_sum_quote(sum_quote)

    def taker(self, amount, token):

        '''
        Pair:MAN-BTC
        Currency:BTC
        => Buy
        Price(i.e. 0.00003560): For each MAN is an amount BTC needed
        '''
        if self.pair.get_base_token() == token:
            return self.buy(amount)

        '''
        Pair:MAN-BTC
        Currency:MAN
        => SELL
        Price(i.e. 0.00003560): For each MAN you get an amount BTC
        '''
        if self.pair.get_quote_token() == token:
            return self.sell(amount)

    def buy(self, amount):
        trades = []
        for i in range(len(self.book[Trade.WAY_SELL])):
            offer = self.book[Trade.WAY_SELL][i]
            amount_quote = offer.get_quote_amount() # GAS
            amount_base = offer.get_base_amount() # NEO
            price = offer.get_price()

            if amount_base >= amount:
                buy_amount = amount / price
                trade = Trade(self.pair, Trade.WAY_BUY, price, amount, buy_amount, None)
                trades.append(trade)
                return trades

            '''
            Is the offered amount less than needed, you can only buy the offered amount and continue
            '''
            trade = Trade(self.pair, Trade.WAY_BUY, price, amount_base, amount_quote, None)
            amount = amount - amount_base
            trades = trades + [trade]

        '''
        Not enough volume or amount to high
        '''
        raise KeyError("Not enough offers in orderbook. Low volume or amount to high.")

    def sell(self, amount): # GAS
        trades = []
        for i in range(len(self.book[Trade.WAY_BUY])):
            offer = self.book[Trade.WAY_BUY][i]
            amount_quote = offer.get_quote_amount() # GAS
            amount_base = offer.get_base_amount() # NEO
            price = offer.get_price()

            if amount_quote >= amount:
                sell_amount = amount * price
                trade = Trade(self.pair, Trade.WAY_SELL, price, sell_amount, amount, None)
                trades.append(trade)
                return trades

            '''
            Is the offered amount less than needed, you can only buy the offered amount and continue
            '''
            trade = Trade(self.pair, Trade.WAY_SELL, price, amount_base, amount_quote, None)
            amount = amount - amount_quote
            trades = trades + [trade]

        '''
        Not enough volume or amount to high
        '''
        raise KeyError("Not enough offers in orderbook. Low volume or amount to high.")

    def reverse_taker(self, amount, token):

        if self.pair.get_base_token() == token:
            return self.reverse_buy(amount)

        if self.pair.get_quote_token() == token:
            return self.reverse_sell(amount)

    def reverse_buy(self, amount):
        trades = []
        trade_amount = 0
        for i in range(len(self.book[Trade.WAY_SELL])):
            offer = self.book[Trade.WAY_SELL][i]
            amount_quote = offer.get_quote_amount() # GAS
            amount_base = offer.get_base_amount() # NEO
            price = offer.get_price()

            if amount_base >= amount:
                buy_amount = amount / price
                trade = Trade(self.pair, Trade.WAY_BUY, price, amount, buy_amount, None)
                trades.append(trade)
                return trades

            '''
            Is the offered amount less than needed, you can only buy the offered amount and continue
            '''
            trade = Trade(self.pair, Trade.WAY_BUY, price, amount_base, amount_quote, None)
            amount = amount - amount_base
            trades = trades + [trade]

        '''
        Not enough volume or amount to high
        '''
        raise KeyError("Not enough offers in orderbook. Low volume or amount to high.")

    def is_updated(self):
        return self.timestamp > 0

    def get_trade_way(self, token):
        if self.pair.get_base_token() == token:
            return Trade.WAY_BUY

        if self.pair.get_quote_token() == token:
            return Trade.WAY_SELL

    def get_sum(self, index, token):
        way = self.get_trade_way(token)
        if way == Trade.WAY_BUY:
            return self.book[way][index].get_sum_quote()
        else:
            return self.book[way][index].get_sum_base()

    def get_sum_after_fees(self, index, token):
        return self.get_sum(index, token) * (1-self.pair.get_exchange().get_fees())

