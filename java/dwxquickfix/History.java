package dwxquickfix;

import java .util.ArrayList;

import static dwxquickfix.Helpers.*;

public class History {
    
    boolean storeAllTicks;
    boolean saveHistoryToFile;
    
    String historyDir = "history";
    
    int lowestDepth = -1;
    int lastWriteMinute = -1;
    
    public ArrayList<Tick> tickHistory = new ArrayList<Tick>();
    public ArrayList<TickTOB> TOBhistory = new ArrayList<TickTOB>();
    
    public ArrayList<Double> bid = new ArrayList<>();
    public ArrayList<Double> ask = new ArrayList<>();
    public ArrayList<Integer> bidSize = new ArrayList<>();
    public ArrayList<Integer> askSize = new ArrayList<>();
    
    public double bidTOB = 0, askTOB = 0;
    
    public History(String symbol, boolean storeAllTicks, boolean saveHistoryToFile) {
        this.storeAllTicks = storeAllTicks;
        this.saveHistoryToFile = saveHistoryToFile;
    }
    
    // fffff: could theoretically be <0 (like oil price in 2020). 
    public void updateAsset(String sendingTimeStr, String symbol, int depth, double bid, double ask, int bidSize, int askSize) {
        
        // fffff: what if there were really negative prices?
        if (depth < 0 || (bid <= 0 && ask <= 0 && bidSize <= 0 && askSize <= 0)) return;
        if (depth < lowestDepth || lowestDepth == -1) lowestDepth = depth;
        
        boolean newBidTOB = false, newAskTOB = false;
        if (depth == lowestDepth && bid > 0) {
            this.bidTOB = bid;
            newBidTOB = true;
        }
        if (depth == lowestDepth && ask > 0) {
            this.askTOB = ask;
            newAskTOB = true;
        }
        
        if (bid > 0) {
            if (depth >= this.bid.size()) this.bid.add(bid);
            else this.bid.set(depth, bid);
        }
        if (ask > 0) {
            if (depth >= this.ask.size()) this.ask.add(ask);
            else this.ask.set(depth, ask);
        }
        if (bidSize > 0) {
            if (depth >= this.bidSize.size()) this.bidSize.add(bidSize);
            else this.bidSize.set(depth, bidSize);
        }
        if (askSize > 0) {
            if (depth >= this.askSize.size()) this.askSize.add(askSize);
            else this.askSize.set(depth, askSize);
        }
        
        if (storeAllTicks) {
            try {
                Tick tick = new Tick(sendingTimeStr, depth, this.bid.get(depth), this.ask.get(depth), this.bidSize.get(depth), this.askSize.get(depth));
                tickHistory.add(tick);
                if (newBidTOB || newAskTOB) {
                    TickTOB tickTOB = new TickTOB(sendingTimeStr, this.bidTOB, this.askTOB);
                    TOBhistory.add(tickTOB);
                }
            } catch (Exception e) {
            }
        }
        
        // fffff: change to Calendar.get(Calendar.MINUTE)?
        // final Calendar c = Calendar.getInstance(TimeZone.getTimeZone("UTC"));
        if (saveHistoryToFile) {
            int minute = Integer.parseInt(sendingTimeStr.substring(12, 14));
            if (minute != lastWriteMinute) {
                // lastWriteMinute = sendingTime.getMinutes();
                lastWriteMinute = minute;
                writeHistoryToFile(historyDir, symbol, tickHistory);
                writeHistoryTOBToFile(historyDir, symbol, TOBhistory);
            }
        }
    }
}
