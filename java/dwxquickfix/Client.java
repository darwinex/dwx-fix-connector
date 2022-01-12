package dwxquickfix;

import java.io.FileInputStream;

import quickfix.Initiator;
import quickfix.Session;
import quickfix.SessionID;
import quickfix.SocketInitiator;
import quickfix.SessionSettings;
import quickfix.LogFactory;
import quickfix.FileLogFactory;
import quickfix.MessageFactory;
import quickfix.MessageStoreFactory;
import quickfix.FileStoreFactory;
import quickfix.DefaultMessageFactory;


import static dwxquickfix.Helpers.*;

public class Client {
    
    public App app;
    public Initiator initiator;

    public Client(String fileName, TickProcessor tickProcessor, boolean storeAllTicks, boolean saveHistoryToFile, boolean printFromAppMessages, boolean printFromAdminMessages, boolean printToAppMessages, boolean printToAdminMessages) throws Exception {

        if (fileName.length() == 0) fileName = "config/client_sample.conf";

        print("Starting FIX session using config file: " + fileName);

        SessionSettings settings = new SessionSettings(new FileInputStream(fileName));
        
        app = new App(settings, tickProcessor, storeAllTicks, saveHistoryToFile, printFromAppMessages, printFromAdminMessages, printToAppMessages, printToAdminMessages);

        MessageStoreFactory storeFactory = new FileStoreFactory(settings);
        LogFactory logFactory = new FileLogFactory(settings);
        MessageFactory messageFactory = new DefaultMessageFactory();
        initiator = new SocketInitiator(app, storeFactory, settings, logFactory, messageFactory);
        initiator.start();
        
        for (int i=0; i<10; i++) {
            if (initiator.isLoggedOn()) break;
            Thread.sleep(1000);
        }
        
        if (isLoggedOn()) {
            tickProcessor.start(app);
        } else {
            print("[ERROR] could not initialize session");
        }
    }
    
    public boolean isLoggedOn() {
        print("isLoggedOn:");
		// print(initiator.getSessions());
        for (SessionID sessionID : initiator.getSessions()) {
            print(sessionID + ": " + Session.lookupSession(sessionID).isLoggedOn());
        }
        return initiator.isLoggedOn();
    }

    // public static void run() {
        
        // pricing.send_MarketDataRequest("EURUSD");
        
        // while (true) {
            // try {
                // Thread.sleep(3000);
                // print("...");
            // } catch (Exception e) {
            // }
        // }
    // }
}
