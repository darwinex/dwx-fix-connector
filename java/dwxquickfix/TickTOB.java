package dwxquickfix;

import java.util.Date;

public class TickTOB {
    
    // Date dateTime;
    String dateTimeStr;
    int depth;
    double bid;
    double ask;
    // int bidSize;
    // int askSize;
    
    public TickTOB(String dateTimeStr, double bid, double ask) {
        this.dateTimeStr = dateTimeStr;
        this.bid = bid;
        this.ask = ask;
        // this.bidSize = bidSize;
        // this.askSize = askSize;
    }
}
