package dwxquickfix;

import java.util.Hashtable;
import java.util.Dictionary;
import java.util.Date;
import java.util.Calendar;
import java.util.TimeZone;
import java.text.SimpleDateFormat;
import java.text.ParseException;

import quickfix.Application;
import quickfix.Session;
import quickfix.SessionID;
import quickfix.Message;
import quickfix.SessionSettings;
import quickfix.SessionNotFound;
import quickfix.FieldNotFound;
import quickfix.IncorrectTagValue;
import quickfix.UnsupportedMessageType;

import quickfix.fix44.Logon;
import quickfix.fix44.MarketDataRequest;
import quickfix.fix44.NewOrderSingle;
import quickfix.fix44.MarketDataRequest.NoRelatedSym;
import quickfix.fix44.MassQuote;
import quickfix.fix44.MassQuote.NoQuoteSets;
import quickfix.fix44.MassQuoteAcknowledgement;
import quickfix.fix44.MarketDataSnapshotFullRefresh.NoMDEntries;

import static dwxquickfix.Helpers.*;

public class Sender {  // implements Application 

    SessionSettings settings;
    App app;
    SessionID sessionID_Quote;
    SessionID sessionID_Trade;
    String account;
    
    Sender(SessionSettings settings, App app) {
        this.settings = settings;
        this.app = app;
    }
    
    public void set_sessionID_Quote(SessionID sessionID) {
        this.sessionID_Quote = sessionID;
    }
    
    public void set_sessionID_Trade(SessionID sessionID) {
        this.sessionID_Trade = sessionID;
    }
    
    public void set_account(String account) {
        this.account = account;
    }
    
    // example: https://github.com/quickfix-j/quickfixj/blob/master/quickfixj-examples/ordermatch/src/main/java/quickfix/examples/ordermatch/Application.java
    public void send_MarketDataRequest(String symbol) {
        
        int reqid = app.checkNewSymbol(symbol);
        
        MarketDataRequest message = new MarketDataRequest();
        NoRelatedSym symGroup = new NoRelatedSym();
        symGroup.set(new quickfix.field.Symbol(symbol));
        message.addGroup(symGroup);
        message.set(new quickfix.field.MDReqID(String.valueOf(reqid)));
        message.set(new quickfix.field.SubscriptionRequestType('1'));  // 1: SNAPSHOT_PLUS_UPDATES
        message.set(new quickfix.field.MarketDepth('0'));              // 0: full book, 1: top of book, fffff: better send top of book since we don't handle depth?
        message.set(new quickfix.field.MDUpdateType('1'));             // 1: INCREMENTAL_REFRESH
        
        send(message, sessionID_Quote);
        
        // for (char mdEntryType : mdEntryTypes) {
            // NoMDEntryTypes entryTypesGroup = new NoMDEntryTypes();
            // entryTypesGroup.set(new MDEntryType(mdEntryType));
            // message.addGroup(entryTypesGroup);
        // }
    }
    
    // fffff: insert code!
    public void send_MassQuoteAcknowledgement(Message incomingMessage) throws FieldNotFound {
        // QuoteID in response should be the QuoteID from the MassQuote 
        // received from the server (tag 117)
        quickfix.field.QuoteID quoteID = new quickfix.field.QuoteID();
        incomingMessage.getField(quoteID);
        // print("quoteID: " + quoteID.getValue());
        
        MassQuoteAcknowledgement message = new MassQuoteAcknowledgement();
    
        // Set QuoteID to MassQuote QuoteID
        message.set(quoteID);
        
		// print("sending MassQuoteAcknowledgement");
        // print(message.toString());
        // print(messageStr(message));
        
        send(message, sessionID_Quote);
    }
    
    public void send_NewOrderSingle(Order order) {
        
        if (order.error) {
            print("[ERROR] The order cannot be sent because it contains errors.");
            return;
        }
		
		if (order.ClOrdID == 0) 
			order.ClOrdID = app.nextClOrdID();
        
        NewOrderSingle message = new NewOrderSingle();
        
        // Tag 11 - Unique ID to assign to this trade.
        message.setField(new quickfix.field.ClOrdID(String.valueOf(order.ClOrdID)));
        
        // Tag 1 - Account ID as provided by FIX administrator
        message.setField(new quickfix.field.Account(account));
        
        // Tag 55
        message.setField(new quickfix.field.Symbol(order.symbol));
        
        // Tag 54 (1 == buy, 2 == sell)
        message.setField(new quickfix.field.Side(order.side));
        
        // Tag 38
        message.setField(new quickfix.field.OrderQty(order.quantity));
        
        // Tag 40 (1 == market, 2 == limit)
        message.setField(new quickfix.field.OrdType(order.type));

        // Tag 44: not needed for market orders.
		if (order.price != 0)
			message.setField(new quickfix.field.Price(order.price));
         
        // Tag 10000 - TTL in milliseconds for open trade expiration.
        message.setField(new quickfix.IntField(10000, order.ttl));

        // Tag 10001 (deviation: maximum allowed slippage)
        // Double value. Accepted deviation from the price submitted in tag 44. Only applicable if 40=2. 
        // Defaults to 0.0. Setting this value to 0.00002 for a sell EURUSD limit order would allow for 
        // execution on prices as low as 0.2 pips below the specified price. The preferred mode of operation 
        // for limit orders is to set tag 44 at current market price and use tag 10001 to define a specific
        // slippage acceptance. 
        if (order.type == '2') {
            message.setField(new quickfix.DoubleField(10001, order.deviation));
        }
        
        // Tag 60 (current time in UTC). fffff: test if set automatically?
        message.setField(new quickfix.field.TransactTime());
        
        if (sessionID_Trade != null) {
        
            // Add trade to local open orders:
            app.addOrder(order);
            
            send(message, sessionID_Trade);
        } else {
            print("[ERROR] send_MassQuoteAcknowledgement() failed. sessionID_Trade is None!");
        }
    }
    
    public void send(Message message, SessionID sessionID) {
        try {
            // print("Sending with sessionID: " + sessionID.toString());
			// print("Sender: " + messageStr(message));
            Session.sendToTarget(message, sessionID);
        } catch (SessionNotFound e) {
            print("[ERROR] Session not found! sessionID: " + sessionID.toString());
        }
    }
}
