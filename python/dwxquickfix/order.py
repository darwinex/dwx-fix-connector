# -*- coding: utf-8 -*-
"""
    order.py
    @author: Darwinex Labs (www.darwinex.com), 2021-*
    
    order - A data structure to hold open orders
"""

class order():
    
    # Side: 1=buy, 2=sell
    def __init__(self, ClOrdID=None, order_type='buy_market', symbol='EURUSD', 
                 price=None, quantity=1000, min_quantity=0, deviation=0, ttl=300, 
                 openTime='', _dict=None):
    
        if _dict is None:
            self.ClOrdID = None
            if ClOrdID is not None:
                self.ClOrdID = ClOrdID
            self.openTime = openTime
            self.symbol = symbol
            
            self.price = price
            self.deviation = deviation        # maximum slippage (only applicable for limit orders)
            self.quantity = quantity
            self.leaves_quantity = quantity
            self.min_quantity = min_quantity  # set min_quantity=quantity to not allow partial fills. 
            self.order_type = order_type
            self.ttl = ttl                    # ttl: time to live, in milliseconds
            self.error = False
            self.status = None

            if order_type == 'buy_market':
                self.side = '1'
                self.type = '1'
            elif order_type == 'buy_limit':
                self.side = '1'
                self.type = '2'
            elif order_type == 'buy_stop':
                self.side = '1'
                self.type = '3'
            elif order_type == 'sell_market':
                self.side = '2'
                self.type = '1'
            elif order_type == 'sell_limit':
                self.side = '2'
                self.type = '1'
            elif order_type == 'sell_stop':
                self.side = '2'
                self.type = '1'
            else:
                self.side = '0'
                self.type = '0'
                self.error = True
                print(f'[ERROR] Order type could not be determined! order_type: {order_type}')
            if self.type != '1' and price is None:
                self.error = True
                print(f'[ERROR] Price must be given for limit and stop orders! order_type: {order_type} | price: {price}')
        else:
            self.__dict__.update(_dict)
    
    # def to_JSON(self):
        # return json.dumps(self, default=lambda o: o.__dict__)
    
    def __str__(self):
        return (f'ClOrdID: {self.ClOrdID}, symbol: {self.symbol}, order_type: {self.order_type}, '
                f'type: {self.type}, side: {self.side}, quantity: {self.quantity}, '
                f'min_quantity: {self.min_quantity}, leaves_quantity: {self.leaves_quantity}, '
                f'price: {self.price}, ttl: {self.ttl}, status: {self.status}')
        