package dwxquickfix;

// import java.util.Hashtable;
// import java.util.Dictionary;
import java.util.Date;
import java.util.Calendar;
import java.util.TimeZone;
import java.util.concurrent.ConcurrentHashMap;
import java.text.SimpleDateFormat;
import java.text.ParseException;

import java.util.ArrayList;

import quickfix.Application;
import quickfix.Session;
import quickfix.SessionID;
import quickfix.Message;
import quickfix.SessionSettings;

import quickfix.fix44.Logon;
import quickfix.fix44.MassQuote;
import quickfix.fix44.MassQuote.NoQuoteSets;
import quickfix.fix44.MassQuoteAcknowledgement;
import quickfix.fix44.MarketDataSnapshotFullRefresh.NoMDEntries;

import static dwxquickfix.Helpers.*;

public class App implements Application {  // extends Application 

    SessionSettings settings;
    TickProcessor tickProcessor;
    public Sender sender;
    String username = "";
    String password = "";
    boolean storeAllTicks = true;
    boolean saveHistoryToFile = true;
	boolean printFromAppMessages = false;
	boolean printFromAdminMessages = false;
	boolean printToAppMessages = false;
	boolean printToAdminMessages = false;
    
    int IDincrementor = 0;
    int ClOrdIDincrementor = 0;
	
    public ConcurrentHashMap<String, String> IDtoSymbol = new ConcurrentHashMap<String, String>();

    public ConcurrentHashMap<String, History> history = new ConcurrentHashMap<String, History>();
    
    public ConcurrentHashMap<Integer, Order> openOrders = new ConcurrentHashMap<Integer, Order>();
    
    public ConcurrentHashMap<String, Integer> openNetPositions = new ConcurrentHashMap<String, Integer>();
    
    public ArrayList<ExecutionReport> executionHistory = new ArrayList<ExecutionReport>();
    
    App(SessionSettings settings, TickProcessor tickProcessor, boolean storeAllTicks, boolean saveHistoryToFile, boolean printFromAppMessages, boolean printFromAdminMessages, boolean printToAppMessages, boolean printToAdminMessages) {
        this.settings = settings;
        this.tickProcessor = tickProcessor;
        this.storeAllTicks = storeAllTicks;
        this.saveHistoryToFile = saveHistoryToFile;
		this.printFromAppMessages = printFromAppMessages;
        this.sender = new Sender(settings, this);
    }

    public void fromApp(Message message, SessionID sessionID) throws quickfix.FieldNotFound, quickfix.UnsupportedMessageType, quickfix.IncorrectTagValue {
        // crack(message, sessionID);
        if (printFromAppMessages) print("[fromApp] " + messageStr(message));
        
        
        // Get incoming message Type
        quickfix.field.MsgType msgType = new quickfix.field.MsgType();
        message.getHeader().getField(msgType);
        
        // Date sendingTime = extractHeaderTime(message, quickfix.field.SendingTime.FIELD);
        String sendingTimeStr = message.getHeader().getString(quickfix.field.SendingTime.FIELD);
        // print("sendingTime: " + sendingTimeStr + " | msgType: " + msgType.getValue());
        
        // char side = message.getChar(quickfix.field.Side.FIELD);
        // char ordType = message.getChar(quickfix.field.OrdType.FIELD);
		
		if (msgType.valueEquals(quickfix.field.MsgType.MASS_QUOTE)) {
            
            // print("[fromApp] Mass Quote!");
            
            int numSets = message.getInt(quickfix.field.NoQuoteSets.FIELD);
            // print("numSets: " + numSets);
            
            for (int i=0; i<numSets; i++) {
            
                // QuoteSetID is inside the NoQuoteSets GROUP (#1 in MassQuote)
                //   - Bid/Offer data is inside NoQuoteEntries GROUP
                NoQuoteSets NoQuoteSets_Group = new NoQuoteSets();
                
                // // MassQuote messages can contain multiple NoQuoteSets groups
                // // Groups have indexes in FIX messages starting at 1
                message.getGroup(i+1, NoQuoteSets_Group);
                // String reqidStr = NoQuoteSets_Group.getString(quickfix.field.QuoteSetID.FIELD);  // 302
                String reqidStr = NoQuoteSets_Group.getQuoteSetID().getValue();  // 302
                // print("reqidStr: " + reqidStr);
                String symbol = IDtoSymbol.get(reqidStr);
                
                NoQuoteSets.NoQuoteEntries NoQuoteEntries_Group = new NoQuoteSets.NoQuoteEntries() ;         
                NoQuoteSets_Group.getGroup(1, NoQuoteEntries_Group);
                
                // could also use NoQuoteEntries_Group.getOfferSpotRate().getValue(), but then we would need try/catch for each. 
                int depth = extractInt(NoQuoteEntries_Group, quickfix.field.QuoteEntryID.FIELD);  // 299
                double bid = extractDouble(NoQuoteEntries_Group, quickfix.field.BidSpotRate.FIELD);  // here we return -1 if it does not work. 
                double ask = extractDouble(NoQuoteEntries_Group, quickfix.field.OfferSpotRate.FIELD);
                int bidSize = extractInt(NoQuoteEntries_Group, quickfix.field.BidSize.FIELD);
                int askSize = extractInt(NoQuoteEntries_Group, quickfix.field.OfferSize.FIELD);
                
                // somehow this just fails without any message?!
                // double bid = NoQuoteEntries_Group.getDouble(quickfix.field.BidSpotRate.FIELD);  // fffff: what is returned if there is no bid?
                // double ask = NoQuoteEntries_Group.getDouble(quickfix.field.OfferSpotRate.FIELD);
                // double bidSize = NoQuoteEntries_Group.getDouble(quickfix.field.BidSize.FIELD);
                // double askSize = NoQuoteEntries_Group.getDouble(quickfix.field.OfferSize.FIELD);
                
                // print("bid: " + bid + " | ask: " + ask + " | bidSize: " + bidSize + " | askSize: " + askSize);
            
                updateAsset(sendingTimeStr, symbol, depth, bid, ask, bidSize, askSize);
            }
            
            // print("QuoteID set: " + message.isSetField(quickfix.field.QuoteID.FIELD));
            
            // If QuoteID is set the client has to respond immediately with a MassQuoteAcknowledgement.
            // if (message.isSetQuoteID()) {
            if (message.isSetField(quickfix.field.QuoteID.FIELD)) {
				sender.send_MassQuoteAcknowledgement(message);
            }
            
        } else if (msgType.valueEquals(quickfix.field.MsgType.MARKET_DATA_SNAPSHOT_FULL_REFRESH)) {  // 35=W, fffff: check if symbol in dict and save data!
            
            // print("[fromApp] Market data snapshot full refresh!");
            
            String symbol = message.getString(quickfix.field.Symbol.FIELD);
            // print("symbol: " + symbol);
            
            int numEntries = message.getInt(quickfix.field.NoMDEntries.FIELD);
            // print("numEntries: " + numEntries);

            for (int i=0; i<numEntries; i++) {
                // MarketDataSnapshotFullRefresh message contains multiple NoQuoteSets group
                // Groups have indexes in FIX messages starting at 1
                NoMDEntries NoMDEntries_Group = new NoMDEntries();
                message.getGroup(i+1, NoMDEntries_Group);
                
                double bid = 0, ask = 0;
                int bidSize = 0, askSize = 0;
                
                quickfix.field.MDEntryType type = NoMDEntries_Group.getMDEntryType();  // 269, getValue() would not return 0/1 but MDEntryType.
                int depth = Integer.parseInt(NoMDEntries_Group.getQuoteEntryID().getValue());  // 299
                double price = NoMDEntries_Group.getMDEntryPx().getValue();  // 270
                int size = (int)NoMDEntries_Group.getMDEntrySize().getValue();  // 271
                // print(type);
                if (type.valueEquals(quickfix.field.MDEntryType.BID)) {  // will not
                    bid = price;
                    bidSize = size;
                } else {
                    ask = price;
                    askSize = size;
                }
                
                updateAsset(sendingTimeStr, symbol, depth, bid, ask, bidSize, askSize);
                // print("symbol: " + symbol + " | bid: " + bid + " | ask: " + ask + " | bidSize: " + bidSize + " | askSize: " + askSize);
            }
            
            
        } else if (msgType.valueEquals(quickfix.field.MsgType.MARKET_DATA_INCREMENTAL_REFRESH)) {  // 35=X
            
            print("Market data incremental refresh!");
            
        } else if (msgType.valueEquals(quickfix.field.MsgType.EXECUTION_REPORT)) {  // 35=8
            
            print("[fromApp] Execution report:");
            print("[fromApp] " + messageStr(message));
			
            int ClOrdID = message.getInt(quickfix.field.ClOrdID.FIELD);
            // print("ClOrdID: " + ClOrdID);
            
            String ordStatus = message.getString(quickfix.field.OrdStatus.FIELD);
            // print("ordStatus: " + ordStatus);

            // Tag 40 OrderType: 1 = Market, 2 = Limit, 3 = Stop
            int ordType = message.getInt(quickfix.field.OrdType.FIELD);
            // print("ordType: " + ordType);

            // Tag 44
            double price = message.getDouble(quickfix.field.Price.FIELD);
            // print("price: " + price);

            // Tag 54
            int side = message.getInt(quickfix.field.Side.FIELD);
            // print("side: " + side);

            // Tag 55
            String symbol = message.getString(quickfix.field.Symbol.FIELD);
            // print("symbol: " + symbol);
            
            Date transactTime = extractMessageTime(message, quickfix.field.TransactTime.FIELD);
            // print("transactTime: " + transactTime);
            
            // Tag 18, the quantity could in theory also be a double. 
            int orderQty = message.getInt(quickfix.field.OrderQty.FIELD);
            // print("orderQty: " + orderQty);

            // Tag 110
            int minQty = message.getInt(quickfix.field.MinQty.FIELD);
            // print("minQty: " + minQty);

			int cumQty = 0;
			int leavesQty = 0;
			if (ordStatus.equals("1") || ordStatus.equals("2")) {  // otherwise it would result in an error if the filed was not found. 
				// Tag 14 CumQty: Total quantity filled.
				cumQty = message.getInt(quickfix.field.CumQty.FIELD);
				// print("cumQty: " + cumQty);

				// Tag 151 LeavesQty: Quantity open for further execution. 0 if 'Canceled', 'DoneForTheDay', 'Expired', 'Calculated', or' Rejected', else LeavesQty <151> = OrderQty <38> - CumQty <14>. 
				leavesQty = message.getInt(quickfix.field.LeavesQty.FIELD);
				// print("leavesQty: " + leavesQty);
            }
			
            if (!openOrders.containsKey(ClOrdID)) {
                print("[ERROR] ClOrdID not found in OpenOrders: " + ClOrdID);
                print(openOrders);
                return;  // ok to return here? in this case the order would just stay 
            }
            
            if (ordStatus.equals("0")) {  // new
				print("order confirmed. ClOrdID: " + ClOrdID);
                Order order = openOrders.get(ClOrdID);
                order.confirmed = true;
                order.openTime = transactTime;
                openOrders.put(ClOrdID, order);

            } else if (ordStatus.equals("1")) {  // partially filled.  && leavesQty > 0, leavesQty should always be >0 else it should be ordStatus=2. 
				Order order = openOrders.get(ClOrdID);
				order.quantity = leavesQty;
				openOrders.put(ClOrdID, order);
                addPosition(symbol, side, orderQty);  // fffff: check that only added if order was found?!
            } else if (ordStatus.equals("2")) {  // filled
                openOrders.remove(ClOrdID);
                addPosition(symbol, side, orderQty);
            } else if (ordStatus.equals("4") || ordStatus.equals("6") || ordStatus.equals("8")) {  // canceled or rejected, https://www.onixs.biz/fix-dictionary/4.4/tagNum_39.html
                openOrders.remove(ClOrdID);
            }
            
            ExecutionReport executionReport = new ExecutionReport(ClOrdID, symbol, side, price, ordType, ordStatus, orderQty, minQty, cumQty, leavesQty, transactTime);
            executionHistory.add(executionReport);
            
            tickProcessor.onExecutionReport(this, executionReport);
        } else if (msgType.valueEquals(quickfix.field.MsgType.TRADING_SESSION_STATUS)) {  // 35=h
			
			print("Trading Session Status Message:");
			print(messageStr(message));
		} else if (msgType.valueEquals(quickfix.field.MsgType.MARKET_DATA_REQUEST_REJECT)) {  // 35=Y
        
            String text = message.getString(quickfix.field.Text.FIELD);
            print("[fromApp] Market Data Request Reject with message: " + text);
		} else {
            // check for all messages types here and exit if not known (to check for types we missed). 
            print("unknown message type: " + msgType);
            // System.exit(0);  // for debugging. 
        }
        
    }
    
    public void toApp(Message message ,SessionID sessionID) {
        if (printToAppMessages) print("[toApp] " + messageStr(message));
    }
    
    public void toAdmin(Message message ,SessionID sessionID) {
        // System.out.println('Sending admin message = %s.', Read_FIX_Message(message));
        
        if (printToAdminMessages) print("[toAdmin] " + messageStr(message));
        
        try {
            quickfix.field.MsgType msgType = new quickfix.field.MsgType();
            message.getHeader().getField(msgType);
            if (msgType.valueEquals(quickfix.field.MsgType.LOGON)) {  // message.getHeader().getField(new MsgType()).valueEquals(MsgType.LOGON), (message instanceof quickfix.fix44.Logon)
                Logon logon = (Logon) message;
                try {
                    String username = settings.getString(sessionID, "Username");
                    logon.set(new quickfix.field.Username(username));
                    String password = settings.getString(sessionID, "Password");
                    // print(username + " | " + password);
                    logon.set(new quickfix.field.Password(password));
					// print(messageStr(logon));
                }
                catch (Exception e) {
                    throw new RuntimeException("Username and Password must be specified in QuickFIX configuration.");
                }
            } else if (msgType.valueEquals(quickfix.field.MsgType.LOGOUT)) {
                
                print("Sending LOGOUT Request");
                
            } else if (msgType.valueEquals(quickfix.field.MsgType.HEARTBEAT)) {
                
                print("Sending Heartbeat");
                
            }
        } catch(quickfix.FieldNotFound e) {
        }
		
        // elif (msgType.getValue() == fix.MsgType_Logout):
			
			// print(self._client_str + 'Sending LOGOUT Request')
		
		// elif (msgType.getValue() == fix.MsgType_Heartbeat)
		   
			// if self.print_heartbeat:
				// print(self._client_str + 'Heartbeat!')
			
		// else:
			// print('[toAdmin] {}'.format(Read_FIX_Message(message)))
    }
    
    public void fromAdmin(Message message ,SessionID sessionID) {
        if (printFromAdminMessages) print("[fromAdmin] " + messageStr(message));
        // check for all messages types here and exit if not known (to check for types we missed). 
        // print("unknown message type!");
        // System.exit(0);  // for debugging
    }
    
    public void onLogon(SessionID sessionID) {
        print("onLogon, SessionID: "+sessionID.toString());
    }
    
    public void onLogout(SessionID sessionID) {
        print("onLogout, SessionID:"+sessionID.toString());
    }
    
    public void onCreate(SessionID sessionID) {
        
        try {
            if (settings.getString(sessionID, "SessionQualifier").equals("Quote")) {
                print("SessionQualifier=Quote, sessionID="+sessionID.toString());
                sender.set_sessionID_Quote(sessionID);
            } else if (settings.getString(sessionID, "SessionQualifier").equals("Trade")) {
                print("SessionQualifier=Trade, sessionID="+sessionID.toString());
                sender.set_sessionID_Trade(sessionID);
                sender.set_account(settings.getString(sessionID, "Account"));
            }
        } catch (quickfix.ConfigError e) {
            e.printStackTrace();
        }
    }
    
    // could theoretically be <0 (like oil price in 2020). 
    public void updateAsset(String sendingTimeStr, String symbol, int depth, double bid, double ask, int bidSize, int askSize) {
        
        history.get(symbol).updateAsset(sendingTimeStr, symbol, depth, bid, ask, bidSize, askSize);
        
        tickProcessor.onTick(this, symbol, history.get(symbol));
    }
    
    public int checkNewSymbol(String symbol) {
        
        int reqid = IDincrementor;
        
        if (!IDtoSymbol.containsValue(symbol)) {
            print("Adding " + symbol + " to ID dict with MDReqID: " + reqid);
            IDtoSymbol.put(String.valueOf(IDincrementor), symbol);
        }
        if (!openNetPositions.containsKey(symbol)) {
            print("Adding " + symbol + " to position map.");
            openNetPositions.put(symbol, 0);
        }
        if (!history.containsKey(symbol)) {
            print("Adding " + symbol + " to history map.");
            history.put(symbol, new History(symbol, storeAllTicks, saveHistoryToFile));
        }
        
        IDincrementor++;
        
        return reqid;
    }
    
    public void addOrder(Order order) {
        openOrders.put(ClOrdIDincrementor, order);
    }
    
    public void addPosition(String symbol, int side, int orderQty) {
        if (openNetPositions.containsKey(symbol)) {
            if (side == 1) {
                openNetPositions.put(symbol, openNetPositions.get(symbol) + orderQty);
            } else if (side == 2) {
                openNetPositions.put(symbol, openNetPositions.get(symbol) - orderQty);
            }
        } else {  // should never happen!?
            openNetPositions.put(symbol, orderQty);
        }
    }
	
    // get the ClOrdID for the next order. 
    
    public int nextClOrdID() {
        
        ClOrdIDincrementor++;

        // to make sure we don't have duplicates. 
        while (openOrders.containsKey(ClOrdIDincrementor)) 
            ClOrdIDincrementor++;

        return ClOrdIDincrementor;
	}
}
