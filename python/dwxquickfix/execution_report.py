# -*- coding: utf-8 -*-
"""
    execution_report.py
    @author: Darwinex Labs (www.darwinex.com), 2021-*
    
    execution_report - A data structure to hold execution reports
"""

class execution_report():
    
    # Side: 1=buy, 2=sell
    def __init__(self, ClOrdID, Symbol, Side, Price, OrdType, 
                 OrdStatus, OrderQty, MinQty, CumQty, LeavesQty):

        self.ClOrdID = ClOrdID
        self.Symbol = Symbol
        self.Side = Side
        self.Price = Price
        self.OrdType = OrdType
        self.OrdStatus = OrdStatus
        self.OrderQty = OrderQty
        self.MinQty = MinQty
        self.CumQty = CumQty
        self.LeavesQty = LeavesQty

    def __str__(self):
        return (f'ClOrdID: {self.ClOrdID}, symbol: {self.Symbol}, Side: {self.Side}, Price: {self.Price}, '
                f'OrdType: {self.OrdType}, OrdStatus: {self.OrdStatus}, OrderQty: {self.OrderQty}, '
                f'MinQty: {self.MinQty}, CumQty: {self.CumQty}, LeavesQty: {self.LeavesQty}')
