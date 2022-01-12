# -*- coding: utf-8 -*-
"""
    application.py
    @author: Darwinex Labs (www.darwinex.com), 2021-*
    
    Class for a QuickFIX application
    
"""

import json
import logging
import datetime
from threading import Lock
import quickfix as fix
import quickfix44 as fix44
    
from dwxquickfix.helpers import log, setup_logger, read_FIX_message, extract_message_field_value, datetime_to_str

from dwxquickfix.order import order
from dwxquickfix.sender import sender
from dwxquickfix.history import history
from dwxquickfix.execution_report import execution_report


class application(fix.Application):

    def __init__(self, settings, tick_processor, 
                 read_positions_from_file=False,  # to load positions after restart
                 store_all_ticks=True, 
                 save_history_to_files=True,
                 verbose=True,
                 message_log_file='messages.log',
                 execution_history_file='execution_history.log', 
                 client_str='[CLIENT (FIX API v4.4)] ',
                 server_str='[SERVER (FIX API v4.4)] '):
        
        super().__init__()
        self.store_all_ticks = store_all_ticks
        self.save_history_to_files = save_history_to_files
        self.verbose = verbose
        self._position_file = 'positions.json'
        self._order_file = 'orders.json'
        self.execution_history_file = execution_history_file
        self.connected = False
        self._ID_Incrementor = 0
        self.ClOrdID_Incrementor = 0
        self.settings = settings
        self.tick_processor = tick_processor
        self.lock = Lock()
        self.sender = sender(self)  # passing self here so that we can call app functions from there. 

        self.logger = None
        if len(message_log_file) > 0:
            self.logger = setup_logger('message_logger', message_log_file, 
                                       '%(asctime)s %(levelname)s %(message)s', 
                                       level=logging.INFO)
        
        self.execution_logger = None
        if len(execution_history_file) > 0:
            self.execution_logger = setup_logger('execution_logger', 
                                                 execution_history_file, 
                                                 '%(message)s', 
                                                 level=logging.INFO)
            log(self.execution_logger, 'transactTime,ClOrdID,Symbol,Side,Price,OrdType,OrdStatus,OrderQty,MinQty,CumQty,LeavesQty')
        
        self._client_str = client_str
        self._server_str = server_str
        
        # Unique identifier for Market Data Request <V>
        self._id_to_symbol = {}  # format: '0': 'EURUSD'

        # Dictionary to hold Asset Histories
        self.history_dict = {}  # format: 'EURUSD': History

        # Dictionary to hold open orders
        self.open_orders = {}  # format: ClOrdID: Order
        
        self.open_net_positions = {}     # format: 'EURUSD': 0.0
        self.canceled_net_quantity = {}  # format: 'EURUSD': 0.0

        self.execution_history = []

        self.read_positions_from_file = read_positions_from_file
        
        if self.read_positions_from_file:
            self.load_positions_from_file()
    
    ##########################################################################

    # QuickFIX Application Methods.

    def onCreate(self, sessionID):
        
        if self.settings.get(sessionID).getString('SessionQualifier') == 'Quote':
            print('SessionQualifier=Quote, sessionID='+sessionID.toString())
            self.sender.set_sessionID_Quote(sessionID)
        
        elif self.settings.get(sessionID).getString('SessionQualifier') == 'Trade':
            print('SessionQualifier=Trade, sessionID='+sessionID.toString())
            self.sender.set_sessionID_Trade(sessionID)
            self.sender.set_account(self.settings.get(sessionID).getString('Account'))

        log(self.logger, f'Session created with sessionID = {sessionID.toString()}.')


    def onLogon(self, sessionID):
        
        self.connected = True
        log(self.logger, 'Logon.')
        print(self._client_str + ' ' + sessionID.toString() + ' | Login Successful')


    def onLogout(self, sessionID):
        
        self.connected = False
        log(self.logger, 'Logout.')
        print(self._client_str + ' ' + sessionID.toString() + ' | Logout Successful')


    def onMessage(self, message, sessionID):
        
        if self.verbose:
            print('[onMessage] {}'.format(read_FIX_message(message)))
        
        log(self.logger, f'Message = {read_FIX_message(message)}.')


    def toAdmin(self, message, sessionID):
        
        if self.verbose:
            print(f'[toAdmin] {sessionID} | {read_FIX_message(message)}')
        
        log(self.logger, f'[toAdmin] {sessionID} | {read_FIX_message(message)}')
        
        msgType = fix.MsgType()
        message.getHeader().getField(msgType)

        base_str = self._client_str + ' ' + sessionID.toString() + ' | '
        
        if msgType.getValue() == fix.MsgType_Logon:
            
            print(self._client_str + 'Sending LOGON Request')
            
            # set login credentials
            username = self.settings.get(sessionID).getString('Username')
            password = self.settings.get(sessionID).getString('Password')
            message.setField(fix.Username(username))
            message.setField(fix.Password(password))
        
        elif msgType.getValue() == fix.MsgType_Logout:
            
            print(self._client_str + 'Sending LOGOUT Request')
        
        elif (msgType.getValue() == fix.MsgType_Heartbeat):
           
            if self.verbose:
                print(self._client_str + 'Heartbeat!')
            
        else:
            print(f'[toAdmin] {sessionID} | {read_FIX_message(message)}')

    
    def toApp(self, message, sessionID):
        
        if self.verbose:
            print(f'[toApp] {sessionID} | {read_FIX_message(message)}')
        
        log(self.logger, f'[toApp] {sessionID} | {read_FIX_message(message)}')
    

    def fromAdmin(self, message, sessionID):

        if self.verbose:
            print(f'[fromAdmin] {sessionID} | {read_FIX_message(message)}')
        
        log(self.logger, f'[fromAdmin] {sessionID} | {read_FIX_message(message)}')
        
        msgType = fix.MsgType()
        message.getHeader().getField(msgType)

        base_str = self._server_str + ' ' + sessionID.toString() + ' | '
        
        if msgType.getValue() == fix.MsgType_Heartbeat:
            
            if self.verbose:
                print(base_str + 'Heartbeat, right back at ya!')
            
        elif msgType.getValue() == fix.MsgType_Logon:
            
            print(base_str + 'Hello there, good to have you back!')
            
        elif msgType.getValue() == fix.MsgType_Logout:
            
            print(base_str + 'Logout. See you later!')
            
        elif self.verbose:
            print(f'[fromAdmin] {sessionID} | {read_FIX_message(message)}')
            
            if msgType.getValue() != fix.MsgType_SequenceReset:
                print('unknown message type: ', msgType)
                # exit()


    def fromApp(self, message, sessionID):

        if self.verbose:
            print(f'[fromApp] {sessionID} | {read_FIX_message(message)}')
        
        log(self.logger, f'[fromApp] {sessionID} | {read_FIX_message(message)}')
        
        # Get incoming message Type
        msgType = fix.MsgType()
        message.getHeader().getField(msgType)
        msgType = msgType.getValue()
        
        # Get timestamp (tag 52)
        sending_time = extract_message_field_value(fix.SendingTime(), message, 'datetime')
        # print('sending_time:', sending_time)

        ########## Quote messages ##########
        
        if msgType == fix.MsgType_MassQuote:
            
            self.parse_MassQuote(message, sending_time)
        
        elif msgType == fix.MsgType_MarketDataSnapshotFullRefresh:
            
            self.parse_MarketDataSnapshotFullRefresh(message, sending_time)
        
        # 3) Process MarketDataSnapshot_IncrementalRefresh message
        elif msgType == fix.MsgType_MarketDataIncrementalRefresh:
            
            print(self._server_str + ' {MD} INCREMENTAL REFRESH!')
        
        ########## Trade messages ##########

        elif msgType == fix.MsgType_ExecutionReport:

            self.parse_ExecutionReport(message, sending_time)

        elif msgType == fix.MsgType_OrderCancelReject:
            
            # An OrderCancelReject will be sent as an answer to an  OrderCancelRequest, which cannot be executed. 
            # Not much to do here as our order dict would stay the same. 
            # If it was canceled successfully, we should get an execution report. 

            ClOrdID = extract_message_field_value(fix.ClOrdID(), message, 'int')

            print(f'[fromApp] Order Cancel Request Rejected for order: {ClOrdID}')
        
        elif msgType == fix.MsgType_MarketDataRequestReject:
        
            text = extract_message_field_value(fix.Text(), message, 'str')
            print(f'[fromApp] Market Data Request Reject with message: {text}')
        
        elif self.verbose:
            print(f'[fromApp] {sessionID} | {read_FIX_message(message)}')
            print('unknown message type: ', msgType)
            # exit()
        
    ##########################################################################

    # message parsing methods
    """
    # parse MassQuote

    # example message:
    # 8=FIX.4.4|9=160|35=i|34=327|49=XC116|52=20171208-12:43:57.593|56=Q024|117=14|296=2|302=0|295=1|
    # 299=0|134=501000|135=251000|190=1.17429|302=2|295=1|299=0|134=2251000|135=501000|10=202|
    
    """
    def parse_MassQuote(self, message, sending_time):

        if self.verbose:
            print(self._server_str + ' MassQuote!')
        
        #################################
        # Enter Tick Storage Logic here.

        # we could have multiple QuoteSets for multiple symbols
        num_sets = extract_message_field_value(fix.NoQuoteSets(), message, 'int')  # 296
        # print('num_sets:', num_sets)
        
        for i in range(num_sets):

            NoQuoteSets_Group = fix44.MassQuote.NoQuoteSets()
            
            # Groups have indexes in FIX messages starting at 1
            message.getGroup(i+1, NoQuoteSets_Group)
            reqid = extract_message_field_value(fix.QuoteSetID(), NoQuoteSets_Group)
            # print(self._id_to_symbol)
            _symbol = self._id_to_symbol[reqid]
                        
            # Bid/Offer data is inside NoQuoteEntries group, inside _NoQuoteSets group.
            # num_sets = extract_message_field_value(fix.NoQuoteEntries(), message, 'int')  # 295, should always be 1.
            NoQuoteEntries_Group = fix44.MassQuote.NoQuoteSets.NoQuoteEntries()          
            NoQuoteSets_Group.getGroup(1, NoQuoteEntries_Group)

            depth = extract_message_field_value(fix.QuoteEntryID(), NoQuoteEntries_Group, 'int')  # 299
            bid = extract_message_field_value(fix.BidSpotRate(), NoQuoteEntries_Group, 'float')  # 188
            ask = extract_message_field_value(fix.OfferSpotRate(), NoQuoteEntries_Group, 'float')  # 190
            bid_size = extract_message_field_value(fix.BidSize(), NoQuoteEntries_Group, 'int')  # 134
            ask_size = extract_message_field_value(fix.OfferSize(), NoQuoteEntries_Group, 'int')  # 135

            self.update_asset(sending_time, _symbol, depth, bid, ask, bid_size, ask_size)
        
        #################################
        
        # If QuoteID is set the client has to respond immediately with a MassQuoteAcknowledgement.
        if message.isSetField(fix.QuoteID()):
            self.sender.send_MassQuoteAcknowledgement(message)

    ##########################################################################

    """
    # parse MarketDataSnapshotFullRefresh
    
    # example message:
    # 8=FIX.4.4 9=276 35=W 34=1708 49=XCT 152=20171201-11:35:11.086 56=Q001 55=XAG/USD 262=10
    # 268=6 269=0 270=16.404 271=20000 299=0 269=0 270=16.403 271=20000 299=1 269=0 270=16.402
    # 271=10000 299=2 269=1 270=16.411 271=49000 299=2 269=1 270=16.412 271=35000 299=1 269=1
    # 270=16.413 271=25000 299=0 106=1 10=115

    """

    def parse_MarketDataSnapshotFullRefresh(self, message, sending_time):
        
        if self.verbose:
            print(self._server_str + ' {MD} Full refresh!')

        symbol = extract_message_field_value(fix.Symbol(), message)
        
        if symbol in self.history_dict:

            num_entries = extract_message_field_value(fix.NoMDEntries(), message, 'int')  # 268

            # MarketDataSnapshotFullRefresh message contains multiple NoQuoteSets group
            # Groups have indexes in FIX messages starting at 1
            NoMDEntries_Group = fix44.MarketDataSnapshotFullRefresh.NoMDEntries()
            # NoMDEntries_Group = fix44.MarketDataIncrementalRefresh.NoMDEntries()

            for i in range(num_entries):
                message.getGroup(i+1, NoMDEntries_Group)
                
                bid, ask, bid_size, ask_size = None, None, None, None 

                _type = extract_message_field_value(fix.MDEntryType(), NoMDEntries_Group, 'str')  # 269 (0: bid, 1: ask)
                price = extract_message_field_value(fix.MDEntryPx(), NoMDEntries_Group, 'float')  # 270
                size = extract_message_field_value(fix.MDEntrySize(), NoMDEntries_Group, 'float')  # 271
                depth = extract_message_field_value(fix.QuoteEntryID(), NoMDEntries_Group, 'int')  # 299
                
                if _type == '0':
                    bid = price
                    bid_size = size
                elif _type == '1':
                    ask = price
                    ask_size = size
            
                if self.verbose:
                    print(f'symbol: {symbol} | bid: {bid} | ask: {ask} | bid_size: {bid_size} | ask_size: {ask_size}')

                self.update_asset(sending_time, symbol, depth, bid, ask, bid_size, ask_size)

    ##########################################################################

    """
    # parse execution report

    # example message:
    # 8=FIX.4.4, 9=226, 35=8, 34=15, 49=XCD17, 52=20200817-07:29:25.121, 56=T008, 6=1.18561, 11=0, 
    # 14=1000, 15=EUR, 17=923228_0_0, 31=1.18561, 32=1000, 37=923228, 38=1000, 39=2, 40=1, 44=1.18561, 
    # 54=2, 55=EUR/USD, 60=20200817-07:29:25.120, 64=20200819, 110=0, 150=F, 151=0, 10=056

    reject:
    # 8=FIX.4.4, 9=164, 35=8, 34=33, 49=XCD17, 52=20201020-10:04:25.518, 56=T008, 11=51515, 14=0.0, 
    # 17=0, 37=0, 38=1000, 39=8, 40=2, 44=1.17, 54=1, 55=EUR/USD, 58=reject: duplicate clOrdID, 150=8, 151=0.0, 10=073

    """

    def parse_ExecutionReport(self, message, sending_time):
        # Extract fields from the message here and pass to an upper layer
        if self.verbose:
            print('[fromApp] Execution Report received!')
            print(f'[fromApp] {read_FIX_message(message)}')

        # Tag 11 (client order ID, the one we sent)
        # must be the same type (int) as in open_orders. 
        ClOrdID = extract_message_field_value(fix.ClOrdID(), message, 'int')
        # print('ClOrdID:', ClOrdID)

        # Tag 15
        # _Currency = extract_message_field_value(fix.Currency(), message)
        # print('_Currency:', _Currency)

        # Tag 17
        # _ExecID = extract_message_field_value(fix.ExecID(), message)
        # print('_ExecID:', _ExecID)

        # Tag 37
        # _OrderID = extract_message_field_value(fix.OrderID(), message)
        # print('_OrderID:', _OrderID)
        
        # Tag 39 OrderStatus: 0 = New, 1 = Partially filled, 2 = Filled, 3 = Done for day, 4 = Canceled, 
        # 6 = Pending Cancel (e.g. result of Order Cancel Request <F>), 7 = Stopped, 
        # 8 = Rejected, 9 = Suspended, A = Pending New, B = Calculated, C = Expired, 
        # D = Accepted for bidding, E = Pending Replace (e.g. result of Order Cancel/Replace Request <G>)
        # maybe also check 3=Done for day, 7=Stopped, 9=Suspended, B=Calculated and C=Expired, but it seems that Stopped means it can still be filled? 
        # https://www.onixs.biz/fix-dictionary/4.4/tagNum_39.html
        ordStatus = extract_message_field_value(fix.OrdStatus(), message, 'str')
        # print('ordStatus:', ordStatus)

        # Tag 150 Execution type
        # 0 = New, 4 = Canceled, F = Trade (partial fill or fill), I = Order Status, ...
        _ExecType = extract_message_field_value(fix.ExecType(), message)
        # print('_ExecType:', _ExecType)

        # if the exection report is a response to an OrderStatusRequest, 
        # fields other than OrdStatus might not be set.
        if _ExecType == 'I':
            if ClOrdID in self.open_orders.keys():
                self.open_orders[ClOrdID].status = ordStatus
            else:
                print(f'Order {ClOrdID} not found! Order status: {ordStatus}')
            return

        # Tag 40 OrderType: 1 = Market, 2 = Limit, 3 = Stop
        ordType = extract_message_field_value(fix.OrdType(), message, 'str')
        # print('ordType:', ordType)

        # Tag 44
        price = extract_message_field_value(fix.Price(), message, 'float')
        # print('price:', price)

        # Tag 54
        side = extract_message_field_value(fix.Side(), message, 'str')
        # print('side:', side)

        # Tag 55
        symbol = extract_message_field_value(fix.Symbol(), message, 'str')
        # print('symbol:', symbol)

        # canceled or rejected: here a few fields are not defined, which would 
        # prevent further parsing of the message. therefore, exiting earlier. 
        # https://www.onixs.biz/fix-dictionary/4.4/tagNum_39.html
        # tags not defined: 60, 18, 100
        # [fromApp] 8=FIX.4.4, 9=164, 35=8, 34=33, 49=XCD17, 52=20201020-10:04:25.518, 
        # 56=T008, 11=51515, 14=0.0, 17=0, 37=0, 38=1000, 39=8, 40=2, 44=1.17, 54=1, 
        # 55=EUR/USD, 58=reject: duplicate clOrdID, 150=8, 151=0.0, 10=073

        if ordStatus == '4' or ordStatus == '6' or ordStatus == '8':

            action = 'canceled'
            if ordStatus == '8':
                action = 'rejected'
            
            if ClOrdID in self.open_orders.keys():  # the report might be sent after restarting the FIX algo. 
                if ordStatus == '4' or ordStatus == '6':
                    if self.verbose:
                        print(f'Order {action}: {self.open_orders[ClOrdID]}')
                if ordStatus == '8':
                    
                    if self.verbose:print(f'Order {action}: {self.open_orders[ClOrdID]}')
                del self.open_orders[ClOrdID]
            elif self.verbose:
                print(f'Order {action}, but not found in open_orders.')

            report = execution_report(ClOrdID, symbol, side, price, ordType, ordStatus, 0, 0, 0, 0)
            self.execution_history.append(report)

            if self.verbose:
                print(report)
            
            
            
            transactTime = datetime_to_str(datetime.datetime.utcnow())
            log(self.execution_logger, '{},{},{},{},{},{},{},{},{},{},{}'.format(transactTime, ClOrdID, symbol, 
                                                                                 side, price, ordType, ordStatus, 
                                                                                 0, 0, 0, 0))

            if self.read_positions_from_file:
                self.save_positions_to_file()

            self.lock.acquire()
            self.tick_processor.on_execution_report(report, self)
            self.lock.release()
            return

        # Tag 60 (how to make it a datetime object?)
        # here without extract_message_field_value() because we want to call getString() and not getValue(). 
        transactTime = fix.TransactTime()
        message.getField(transactTime)
        transactTime = transactTime.getString()
        # print('transactTime:', transactTime)

        # Tag 18
        orderQty = extract_message_field_value(fix.OrderQty(), message, 'int')
        # print('orderQty:', orderQty)

        # Tag 110
        minQty = extract_message_field_value(fix.MinQty(), message, 'int')
        # print('minQty:', minQty)

        # Tag 14 CumQty: Total quantity filled.
        cumQty = extract_message_field_value(fix.CumQty(), message, 'int')
        # print('cumQty:', cumQty)

        # Tag 151 LeavesQty: Quantity open for further execution. 0 if 'Canceled', 'DoneForTheDay', 
        # 'Expired', 'Calculated', or' Rejected', else LeavesQty <151> = OrderQty <38> - CumQty <14>. 
        leavesQty = extract_message_field_value(fix.LeavesQty(), message, 'int')
        # print('leavesQty:', leavesQty)

        if not ClOrdID in self.open_orders.keys():
            log(self.execution_logger, f'[ERROR] ClOrdID {ClOrdID} not found in open_orders:', True)
            for o in self.open_orders:
                log(self.execution_logger, o)
            report = execution_report(ClOrdID, symbol, side, price, ordType, ordStatus, orderQty, minQty, cumQty, leavesQty)
            self.execution_history.append(report)
            print(report)
            # maybe better exit if the ID was not found? 
            # but it could happen on the start of a session with PersistMessages=Y. 
            return
        
        self.open_orders[ClOrdID].status = ordStatus

        if ordStatus == '0':  # new
            self.open_orders[ClOrdID].openTime = transactTime

        elif ordStatus == '1' and leavesQty > 0:  # partially filled
            if leavesQty == 0:
                if ClOrdID in self.open_orders.keys():
                    del self.open_orders[ClOrdID]
            else:
                self.open_orders[ClOrdID].leaves_quantity = leavesQty
            # orderQty is the ordered quantity, cumQty the one filled. 
            self.add_position(symbol, side, cumQty)
            # for consistency check. canceled quantity is orderQty-cumQty. 
            self.add_canceled_quantity(symbol, side, orderQty-cumQty)

        elif ordStatus == '2':  # filled
            if ClOrdID in self.open_orders.keys():
                del self.open_orders[ClOrdID]
            self.add_position(symbol, side, cumQty)
        
        # if there was a partial fill before, a following canceled order can have a non-zero cumQty. 
        elif ordStatus == '3':
            if ClOrdID in self.open_orders.keys():
                del self.open_orders[ClOrdID]
        
        report = execution_report(ClOrdID, symbol, side, price, ordType, ordStatus, orderQty, minQty, cumQty, leavesQty)
        self.execution_history.append(report)

        if self.verbose:
            print(report)

        log(self.execution_logger, '{},{},{},{},{},{},{},{},{},{},{}'.format(transactTime, ClOrdID, symbol, side, 
                                                                             price, ordType, ordStatus, orderQty, 
                                                                             minQty, cumQty, leavesQty))
        
        if self.read_positions_from_file:
            self.save_positions_to_file()

        self.lock.acquire()
        self.tick_processor.on_execution_report(report, self)
        self.lock.release()

    ##########################################################################

    # History methods

    """
    # update the historic data dict
    """
    def update_asset(self, sending_time, symbol, depth, bid, ask, bid_size, ask_size):

        if symbol not in self.history_dict or (bid is None and ask is None and bid_size is None and ask_size is None):
            return

        if self.verbose:
            print(self._client_str + 'Updating ' + symbol + ' Asset History')

        self.history_dict[symbol]._update_asset(sending_time, symbol, depth, bid, ask, bid_size, ask_size)

        self.lock.acquire()
        self.tick_processor.on_tick(symbol, self)
        self.lock.release()

    def add_order(self, order):
        self.open_orders[order.ClOrdID] = order

    """
    # check if a symbol is already in the _id_to_symbol dict. 
    # add the symbol if it is not the case. 
    """
    def check_new_symbol(self, symbol):
        # Create asset in self.history_dict if it doesn't exist.
        
        reqid = None
        
        if symbol not in self._id_to_symbol.values():
            reqid = self._ID_Incrementor
            print(f'{self._client_str}Symbol {symbol} not found. Adding {symbol} with MDReqID {reqid}.')
            self._id_to_symbol[str(reqid)] = symbol
            self._ID_Incrementor += 1
        else:
            for key, val in self._id_to_symbol.items(): 
                if symbol == val:
                    reqid = key

        if symbol not in self.history_dict.keys():
            print(f'{self._client_str}Creating Asset History for {symbol}')
            self.history_dict[symbol] = history(symbol, self.store_all_ticks, self.save_history_to_files)
        
        return reqid

    ##########################################################################

    # Position methods
    """
    # add symbol to open_net_positions
    """
    def add_symbol_to_positions(self, symbol):
        if symbol not in self.open_net_positions.keys():
            self.open_net_positions[symbol] = 0.
            self.canceled_net_quantity[symbol] = 0.

    """
    # add position
    """
    def add_position(self, symbol, side, orderQty):
        if side == '1':
            quantity = orderQty
        elif side == '2':
            quantity = -orderQty
        else:
            return
        
        # print(symbol, side, quantity, side == '1', side == '2')
        if symbol in self.open_net_positions.keys():
            self.open_net_positions[symbol] += quantity
        else:
            self.open_net_positions[symbol] = orderQty
    """
    # add canceled position
    """
    def add_canceled_quantity(self, symbol, side, orderQty):
        if side == '1':
            quantity = orderQty
        elif side == '2':
            quantity = -orderQty
        else:
            return
        
        if symbol in self.canceled_net_quantity.keys():
            self.canceled_net_quantity[symbol] += quantity
        else:
            self.canceled_net_quantity[symbol] = orderQty
    
    """
    # save positions to file
    """
    def save_positions_to_file(self):

        with open(self._order_file, 'w') as f:

            orders_as_dict = {}
            for key in self.open_orders.keys():
                orders_as_dict[key] = self.open_orders[key].__dict__
            
            json.dump(orders_as_dict, f)
        
        with open(self._position_file, 'w') as f:
            json.dump(self.open_net_positions, f)
    
    """
    # load positions from file
    """
    def load_positions_from_file(self):
        with open(self._order_file) as f:

            orders_as_dict = json.load(f)

            for key in orders_as_dict.keys():
                self.open_orders[key] = order(_dict=orders_as_dict[key])
            
            ids = [int(_id) for _id in self.open_orders.keys()]
            if len(ids) > 0:
                self.ClOrdID_Incrementor = max(ids)
            
        with open(self._position_file) as f:
            self.open_net_positions = json.load(f)
    
    """
    # count open positions for one symbol
    """
    def num_orders(self, symbol):
        n = 0
        for key in self.open_orders.keys():
            if self.open_orders[key].symbol == symbol:
                n += 1
        return n

    """
    # count open positions for all symbols
    """
    def num_orders_all_symbols(self):
        return len(self.open_orders)

    """
    # count open positions for one symbol
    """
    def net_position(self, symbol):
        try:
            return self.open_net_positions[symbol]
        except:
            print(f'[ERROR] symbol {symbol} not found in open_net_positions. Symbols: {self.open_net_positions.keys()}')
            return 0.
    
    ##########################################################################

    """
    # get the ClOrdID for the next order. 
    """
    def next_ClOrdID(self):
        
        self.ClOrdID_Incrementor += 1

        # to make sure we don't have duplicates. 
        while self.ClOrdID_Incrementor in self.open_orders.keys():
            self.ClOrdID_Incrementor += 1

        return self.ClOrdID_Incrementor
    
    ##########################################################################