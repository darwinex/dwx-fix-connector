# -*- coding: utf-8 -*-
"""
    client.py
    @author: Darwinex Labs (www.darwinex.com), 2021-*
    
    Class for initializing the connection and application
    
"""

from time import sleep
import quickfix as fix

from dwxquickfix.application import application


class client():

    def __init__(self, tick_processor,
                 config_file='config/client_sample.conf',
                 read_positions_from_file=False,  # to load positions after restart
                 store_all_ticks=True,
                 save_history_to_files=True,
                 verbose=True,
                 message_log_file = 'messages.log',
                 execution_history_file='execution_history.log'):

        # Load FIX v4.4 DEFAULT & SESSION Configuration Settings
        self.settings = fix.SessionSettings(config_file)
        self.storeFactory = fix.FileStoreFactory(self.settings)
        # FileLogFactory to write log to file. ScreenLogFactory to write to console.  
        self.logFactory = fix.FileLogFactory(self.settings)

        self.tick_processor = tick_processor

        # Create instance of main application 
        self.app = application(self.settings, self.tick_processor, 
                               read_positions_from_file, store_all_ticks, 
                               save_history_to_files, verbose, 
                               message_log_file, execution_history_file)

        self.initiator = fix.SocketInitiator(self.app, 
                                             self.storeFactory, 
                                             self.settings, 
                                             self.logFactory)
        self.initiator.start()


        for i in range(10):
            if self.isLoggedOn():
                break
            sleep(1)

        
        if not self.isLoggedOn():
            print('[ERROR] Could not initialize session.')


    def isLoggedOn(self):
        
        # this returns true if either one is connected. 
        # return self.initiator.isLoggedOn()

        # this resulted in an error:
        # TypeError: 'SwigPyObject' object is not iterable
        # for sessionID in self.initiator.getSessions():
            # print(sessionID, '|', fix.Session.lookupSession(sessionID).isLoggedOn())

        return (self.isLoggedOnQuote() and self.isLoggedOnTrade())
    

    def isLoggedOnQuote(self):

        return fix.Session.lookupSession(self.app.sender.sessionID_Quote).isLoggedOn() 


    def isLoggedOnTrade(self):
        
        return fix.Session.lookupSession(self.app.sender.sessionID_Trade).isLoggedOn() 
    

    def stop(self):

        self.initiator.stop()
