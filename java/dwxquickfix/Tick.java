package dwxquickfix;

import java.util.Date;


public class Tick {
    
    // Date dateTime;
    String dateTimeStr;
    int depth;
    double bid;
    double ask;
    int bidSize;
    int askSize;
    
    public Tick(String dateTimeStr, int depth, double bid, double ask, int bidSize, int askSize) {
        this.dateTimeStr = dateTimeStr;
        this.depth = depth;
        this.bid = bid;
        this.ask = ask;
        this.bidSize = bidSize;
        this.askSize = askSize;
    }
}
