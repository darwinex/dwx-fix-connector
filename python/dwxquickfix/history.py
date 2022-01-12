# -*- coding: utf-8 -*-
"""
    2021.py    
    @author: Darwinex Labs (www.darwinex.com), 2021-*
    
    History - A data structure to hold incoming prices from the FIX Server
"""

from os.path import join
import logging
from pathlib import Path

import quickfix as fix

from dwxquickfix.helpers import log, setup_logger, extract_message_field_value


class history():
    
    def __init__(self, _symbol, store_all_ticks=True, save_history_to_files=True):
        
        self.symbol = _symbol
        self.save_history_to_files = save_history_to_files
        self.store_all_ticks = store_all_ticks

        # current bid/ask values depending on depth. top of book is self.BID[0]. 
        self.BID = {}
        self.ASK = {}
        self.BID_SIZE = {}
        self.ASK_SIZE = {}
        self.BID_TOB = 0
        self.ASK_TOB = 0
        self._lowest_bid_depth = -1
        self._lowest_ask_depth = -1
        
        self.HISTORY_DIR = 'history'
        Path(self.HISTORY_DIR).mkdir(parents=True, exist_ok=True)

        self.HISTORY_FILE = f"{self.symbol.replace('/', '')}.log"
        self.HISTORY_FILE_TOB = f"{self.symbol.replace('/', '')}_TOB.log"

        self.history_logger = setup_logger('history_logger', 
                                           join(self.HISTORY_DIR, self.HISTORY_FILE), 
                                           '%(message)s', 
                                           level=logging.INFO)
        self.history_tob_logger = setup_logger('history_tob_logger', 
                                               join(self.HISTORY_DIR, self.HISTORY_FILE_TOB), 
                                               '%(message)s', 
                                               level=logging.INFO)

        log(self.history_logger, 'date_time,depth,bid,ask,bid_size,ask_size')
        log(self.history_tob_logger, 'date_time,bid,ask')

        self.HISTORY = []
        self.HISTORY_TOB = []
                    
    ##########################################################################
    
    # Update Asset History depending on set fields in the message
    def _update_asset(self, date_time, _symbol, depth, bid, ask, bid_size, ask_size):
        
        """
        Check all fields and update data accordingly. Not all will
        be present in every message.
        """
        
        if depth is None or _symbol != self.symbol:
            return
        
        new_tob_bid, new_tob_ask = False, False

        # replace with current value if there is no update
        if bid is not None:
            if depth < self._lowest_bid_depth or self._lowest_bid_depth == -1:
                self._lowest_bid_depth = depth
            self.BID[depth] = bid
            if depth == self._lowest_bid_depth:
                self.BID_TOB = bid
                new_tob_bid = True
        if ask is not None:
            if depth < self._lowest_ask_depth or self._lowest_ask_depth == -1:
                self._lowest_ask_depth = depth
            self.ASK[depth] = ask
            if depth == self._lowest_bid_depth:
                self.ASK_TOB = ask
                new_tob_ask = True
        if bid_size is not None:
            self.BID_SIZE[depth] = bid_size
        if ask_size is not None:
            self.ASK_SIZE[depth] = ask_size
        
        # only save complete ticks
        if self.BID[depth] is None or self.ASK[depth] is None or self.BID_SIZE[depth] is None or self.ASK_SIZE[depth] is None:
            return
        

        if self.store_all_ticks:

            try:
                self.HISTORY.append({'date_time': date_time, 'depth': depth, 'bid': 
                                     self.BID[depth], 'ask': self.ASK[depth], 
                                    'bid_size': self.BID_SIZE[depth], 
                                    'ask_size': self.ASK_SIZE[depth]})
                log(self.history_logger, '{},{},{},{},{},{}'.format(date_time, depth, 
                                                                    self.BID[depth], self.ASK[depth], 
                                                                    self.BID_SIZE[depth], 
                                                                    self.ASK_SIZE[depth]))
                
                if new_tob_bid or new_tob_ask:
                    self.HISTORY_TOB.append({'date_time': date_time, 
                                             'bid': self.BID_TOB, 
                                             'ask': self.ASK_TOB})
                    log(self.history_tob_logger, '{},{},{}'.format(date_time, self.BID_TOB, self.ASK_TOB))

            except KeyError:
                pass
            
    ##########################################################################

    """
    # Resample the M1 data to a higher time frame
    """
    def resampled_history(self, rate_type='', time_frame=''):
        from pandas import DataFrame
        
        df = DataFrame.from_dict(self.HISTORY)
        df.index = df.date_time
        
        return df[rate_type].resample(time_frame).ohlc()
    
    ##########################################################################
