# -*- coding: utf-8 -*-
"""
    sender.py
    @author: Darwinex Labs (www.darwinex.com), 2021-*
    
    Class for sending FIX messages
    
"""

import logging, random
import quickfix as fix
import quickfix44 as fix44
    
from dwxquickfix.helpers import read_FIX_message, extract_message_field_value


class sender():  # fix.Application

    def __init__(self, app):
        self.app = app
        self.sessionID_Quote = None
        self.sessionID_Trade = None
        self.account = None
    
    ##########################################################################

    def set_sessionID_Quote(self, sessionID):
        self.sessionID_Quote = sessionID
    
    def set_sessionID_Trade(self, sessionID):
        self.sessionID_Trade = sessionID
    
    def set_account(self, account):
        self.account = account
    
    ##########################################################################

    """
    # Create Market Data Request (35=V)
    """
    def send_MarketDataRequest(self, symbol='EURUSD'):
        
        # If no symbols provided, exit with error.
        if len(symbol) is 0:
            raise RuntimeError('No symbol specified for MarketDataRequest')
            
        reqid = self.app.check_new_symbol(symbol)  # fffff: ok to reference it here?
        self.app.add_symbol_to_positions(symbol)
        
        # Create new message of type MarketDataRequest
        message = fix.Message()
        header = message.getHeader()
                
        # Set message type to MarketDataRequest (35=V)
        header.setField(fix.MsgType(fix.MsgType_MarketDataRequest))
        
        # Assign request ID (262)
        header.setField(fix.MDReqID(str(reqid)))
        
        # Set Subscription Request Type (263) to SNAPSHOT + UPDATES (1)
        header.setField(fix.SubscriptionRequestType(fix.SubscriptionRequestType_SNAPSHOT_PLUS_UPDATES))
        
        # Set MDUpdateType (required when SubscribtionRequestType is S+U)
        header.setField(fix.MDUpdateType(fix.MDUpdateType_INCREMENTAL_REFRESH))
        
        # Set market depth (264)
        header.setField(fix.MarketDepth(0)) # 0 = full book, 1 = top of book
        
        # Create NoRelatedSym group (to place 146=1 before Symbol)
        group = fix44.MarketDataRequest.NoRelatedSym()
                
        group.setField(fix.Symbol(symbol))
        message.addGroup(group)
        
        # Set Currency (15). not really needed?
        # message.setField(fix.Currency(_currency))
        
        # Send message to Counter-Party and await response.
        if self.sessionID_Quote is not None:
            
            fix.Session.sendToTarget(message, self.sessionID_Quote)
        else:
            print('[ERROR] send_MassQuoteAcknowledgement() failed. sessionID_Quote is None!')

    ##########################################################################
    """
    # Create Mass Quote Acknowledgement Message (35=b) to (35=i)
    """
    def send_MassQuoteAcknowledgement(self, msg):
        
        # QuoteID in response should be the QuoteID from the MassQuote 
        # received from the server (tag 117)
        _QuoteID = extract_message_field_value(fix.QuoteID(), msg)
        
        message = fix.Message()
        header = message.getHeader()
        
        # Set MsgType to MassQuoteAcknowledgement
        header.setField(fix.MsgType(fix.MsgType_MassQuoteAcknowledgement))
        
        # Set QuoteID to MassQuote QuoteID
        message.setField(fix.QuoteID(_QuoteID))
        
        if self.sessionID_Quote is not None:
            fix.Session.sendToTarget(message, self.sessionID_Quote)
        else:
            print('[ERROR] send_MassQuoteAcknowledgement() failed. sessionID_Quote is None!')

    ##########################################################################
    """
    # Create Test Request
    """
    def send_TestRequest(self, sessionID):
            
        # Create new message of type MarketDataRequest
        message = fix.Message()
        header = message.getHeader()
        
        _testReqID = str(random.randint(0,1e6))
        
        header.setField(fix.MsgType(fix.MsgType_TestRequest))
        header.setField(fix.TestReqID(_testReqID))
        
        # Send message to Counter-Party and await response.
        fix.Session.sendToTarget(message, sessionID)
        
    ##########################################################################
    # Create New Order Single
    # Need to emulate the following message:
    #
    # 8=FIX.4.4 9=197 35=D 49=T01 56=XCxxx 34=22989 52=20151105-06:40:48.723 115=32155137
    # 11=12345W 1=5629910 55=EUR/USD 54=1 38=250000 44=1.08666 40=2 10000=300
    # 60=20151105-06:40:48.723 10=128
    def send_NewOrderSingle(self, order):

        if order.error:
            print('[ERROR] The order cannot be sent because it contains errors.')
            return
        
        if order.ClOrdID is None:
            order.ClOrdID = self.app.next_ClOrdID()
        elif order.ClOrdID in self.Open_Orders.keys():
            print('[ERROR] Order not sent. There is already an open order with the same ID. Please use a different one or just leave it empty.')
            return

        message = fix.Message()
        header = message.getHeader()

        # Set message type to NewOrderSingle (35=D)
        header.setField(fix.MsgType(fix.MsgType_NewOrderSingle))

        # Tag 11 - Unique ID to assign to this trade.
        message.setField(fix.ClOrdID(str(order.ClOrdID)))
        
        # Tag 1 - Account ID as provided by FIX administrator
        message.setField(fix.Account(self.account))
        
        # Tag 55
        message.setField(fix.Symbol(str(order.symbol)))
        
        # Tag 54 (1 == buy, 2 == sell)
        message.setField(fix.Side(str(order.side)))
        
        # Tag 38
        message.setField(fix.OrderQty(int(order.quantity)))
        
        # Tag 40 (1 == market, 2 == limit)
        message.setField(fix.OrdType(str(order.type)))

        # Tag 44: not needed for market orders.
        if order.price is not None:
            message.setField(fix.Price(order.price))
         
        # Tag 10000 - TTL in milliseconds for open trade expiration. 
        message.setField(fix.IntField(10000, order.ttl))

        # Tag 10001 (deviation: maximum allowed slippage)
        # Double value. Accepted deviation from the price submitted in tag 44. Only applicable if 40=2. 
        # Defaults to 0.0. Setting this value to 0.00002 for a sell EURUSD limit order would allow for 
        # execution on prices as low as 0.2 pips below the specified price. The preferred mode of operation 
        # for limit orders is to set tag 44 at current market price and use tag 10001 to define a specific
        # slippage acceptance. 
        if str(order.type) == '2':
            message.setField(fix.DoubleField(10001, order.deviation))
        
        # Tag 60 (current time in UTC). 3 means 3 digits (milliseconds)
        message.setField(fix.TransactTime(3))
        
        if self.sessionID_Trade is not None:
        
            # Add trade to local open orders:
            self.app.add_order(order)
            
            fix.Session.sendToTarget(message, self.sessionID_Trade)
        else:
            print('[ERROR] send_NewOrderSingle() failed. sessionID_Trade is None!')

    ##########################################################################
    
    """
    Order Status Request
    
    Current order states:        
    0 = New
    1 = Partially filled
    2 = Filled
    4 = Canceled
    8 = Rejected
    """
    def send_OrderStatusRequest(self, ClOrdID):
        
        message = fix.Message()
        header = message.getHeader()
        
        # Set message type to OrderStatusRequest (35=H)
        header.setField(fix.MsgType(fix.MsgType_OrderStatusRequest))

        # Tag 11 - ClOrdID of the order.
        message.setField(fix.ClOrdID(str(ClOrdID)))
        
        if self.sessionID_Trade is not None:
            fix.Session.sendToTarget(message, self.sessionID_Trade)
        else:
            print('[ERROR] send_OrderStatusRequest() failed. sessionID_Trade is None!')
        
    ##########################################################################
    
    # Order Cancel Request
    def send_OrderCancelRequest(self, ClOrdID):
        
        message = fix.Message()
        header = message.getHeader()

        # Set message type to OrderCancelRequest (35=F)
        header.setField(fix.MsgType(fix.MsgType_OrderCancelRequest))

        # Tag 11 - ClOrdID of the order that should be canceled.
        message.setField(fix.ClOrdID(str(ClOrdID)))
        
        if self.sessionID_Trade is not None:
            fix.Session.sendToTarget(message, self.sessionID_Trade)
        else:
            print('[ERROR] send_OrderCancelRequest() failed. sessionID_Trade is None!')
        
    ##########################################################################
