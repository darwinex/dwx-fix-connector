import dwxquickfix.Client;
import dwxquickfix.App;
import dwxquickfix.Order;
import dwxquickfix.Sender;
import dwxquickfix.History;
import dwxquickfix.ExecutionReport;
import dwxquickfix.TickProcessor;

import static dwxquickfix.Helpers.*;

/*

compile and run:
javac -cp ".;libs/*" "@sources.txt" 

java -cp ".;libs/*" TestClient

*/

public class TestClient {
    
    public static void main(String args[]) throws Exception {
        
        boolean storeAllTicks = true;
        boolean saveHistoryToFile = true;
		boolean printFromAppMessages = true;
		boolean printFromAdminMessages = true;
		boolean printToAppMessages = true;
		boolean printToAdminMessages = true;
        
        MyTickProcessor tickProcessor = new MyTickProcessor();
        
        Client client = new Client("config/client_sample.conf", tickProcessor, storeAllTicks, saveHistoryToFile, printFromAppMessages, printFromAdminMessages, printToAppMessages, printToAdminMessages);
        
        while (true) {  // client.isLoggedOn()
            try {
                Thread.sleep(3000);
                print("sleeping ... isLoggedOn: "+client.isLoggedOn());
            } catch (Exception e) {
            }
        }
        
        // print("Stopping client. isLoggedOn: "+client.isLoggedOn());
        // client.initiator.stop();
        
    }
}

/*
A user defined class that must include 
onTick() and onExecutionReport() methods.
*/

class MyTickProcessor implements TickProcessor {
			
	boolean tradeDone = false;
    
    public void start(App app) {
        
        // live:
        // String[] symbols = {"EURUSD", "AUDJPY", "GBPNZD"};
        // demo:
        String[] symbols = {"EUR/USD", "AUD/JPY", "GBP/NZD"};
        // String[] symbols = {"EUR/USD"};
        
        for (String symbol: symbols) {
            app.sender.send_MarketDataRequest(symbol);  // how can I access the sender from here?
        }
    }
    
    // use synchronized so that price updates and execution updates are not processed one after the other. 
    public synchronized void onTick(App app, String symbol, History history) {
        // the history class has two variables for the top-of-book bid ans ask price (bidTOP, askTOB). 
		// it also contains array lists that contain the historic data:
		// tickHistory, TOBhistory, bid, ask, bidSize, askSize
		// you can also access the history of other symbols through app.history.get(symbol). 
		print(symbol + " bid: " + history.bidTOB + " ask: " + history.askTOB + " ticks: " + history.tickHistory.size());
		
		
		// to send a trade:
		// if (!tradeDone) {
			// tradeDone = true;
			// // possible order types: "buy_market", "buy_limit", "buy_stop", "sell_market", "sell_limit", "sell_stop"
			// // price can be 0 for market orders. 
			// Order order = new Order("buy_market", symbol, 1000, 1000, 300);
			// app.sender.send_NewOrderSingle(order);
		// }
		
    }
	
	public synchronized void onExecutionReport(App app, ExecutionReport executionReport) {
        print("onExecutionReport");
        print(executionReport);
    }
}

