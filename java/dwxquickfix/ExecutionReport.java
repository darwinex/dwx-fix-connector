package dwxquickfix;

import java.util.Date;
import java.util.TimeZone;
import java.text.SimpleDateFormat;

public class ExecutionReport {
    
    int ClOrdID;
    String Symbol;
    int Side;
    double Price;
    int OrdType;
    String OrdStatus;
    int OrderQty;
    int MinQty;
    int CumQty;
    int LeavesQty;
	Date transactTime;
	
	SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS");
    
    public ExecutionReport(int ClOrdID, String Symbol, int Side, double Price, int OrdType, String OrdStatus, int OrderQty, int MinQty, int CumQty, int LeavesQty, Date transactTime) {
        this.ClOrdID = ClOrdID;
        this.Symbol = Symbol;
        this.Side = Side;
        this.Price = Price;
        this.OrdType = OrdType;
        this.OrdStatus = OrdStatus;
        this.OrderQty = OrderQty;
        this.MinQty = MinQty;
        this.CumQty = CumQty;
        this.LeavesQty = LeavesQty;
		this.transactTime = transactTime;
		
		sdf.setTimeZone(TimeZone.getTimeZone("UTC"));
    }
	
	public String toString() {
		return "\nExecution report: "
			 + "\ntransactTime: " + sdf.format(transactTime)
		     + "\nClOrdID: " + ClOrdID
			 + "\nOrdStatus: " + OrdStatus
			 + "\nSide: " + Side
			 + "\nPrice: " + Price
			 + "\nOrdType: " + OrdType
			 + "\nOrderQty: " + OrderQty
			 + "\nMinQty: " + MinQty
			 + "\nCumQty: " + CumQty
			 + "\nLeavesQty: " + LeavesQty;
	}
	
	// void toString() {
        // return "ClOrdID: "  ClOrdID + " | Symbol: " + Symbol + " | Side: " + Side + " | Price: " + Price, 
                 // + " | OrdType: " + OrdType + " | OrdStatus: " + OrdStatus + " | OrderQty: " + OrderQty, 
                 // + " | MinQty: " + MinQty + " | CumQty: " + CumQty + " | LeavesQty: " + LeavesQty;
	// }
}
