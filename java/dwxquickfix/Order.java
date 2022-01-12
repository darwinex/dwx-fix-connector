package dwxquickfix;

import java.util.Date;

import static dwxquickfix.Helpers.*;


public class Order {
    
    public Date openTime;
    public int ClOrdID;
    public String symbol;
    double price;
    double deviation;
    public int quantity;
    public int minQuantity;
    public String orderType;
    public int ttl;
    public boolean error;
    public boolean confirmed;
    
    public char side;
    public char type;
    
	// market orders don't need a price or a deviation. 
	public Order(String orderType, String symbol, int quantity, int minQuantity, int ttl) {
		this(0, orderType, symbol, quantity, minQuantity, ttl);
	}
	
	public Order(int ClOrdID, String orderType, String symbol, int quantity, int minQuantity, int ttl) {
		this(ClOrdID, orderType, symbol, 0, quantity, minQuantity, 0, ttl);
	}
	
	// we don't have to specify a ClOrdID. 
	public Order(String orderType, String symbol, double price, int quantity, int minQuantity, double deviation, int ttl) {
		this(0, orderType, symbol, price, quantity, minQuantity, deviation, ttl);
	}
	
	public Order(int ClOrdID, String orderType, String symbol, double price, int quantity, int minQuantity, double deviation, int ttl) {
        this.ClOrdID = ClOrdID;
        this.orderType = orderType;
        this.symbol = symbol;
        this.price = price;
        this.quantity = quantity;
        this.quantity = quantity;
        this.minQuantity = minQuantity;
        this.deviation = deviation;
        this.ttl = ttl;
        
        this.error = false;
        this.confirmed = false;
        
        if (orderType.equals("buy_market")) {
            this.side = '1';
            this.type = '1';
        } else if (orderType.equals("buy_limit")) {
            this.side = '1';
            this.type = '2';
        } else if (orderType.equals("buy_stop")) {
            this.side = '1';
            this.type = '3';
        } else if (orderType.equals("sell_market")) {
            this.side = '2';
            this.type = '1';
        } else if (orderType.equals("sell_limit")) {
            this.side = '2';
            this.type = '1';
        } else if (orderType.equals("sell_stop")) {
            this.side = '2';
            this.type = '1';
        } else {
            this.side = '0';
            this.type = '0';
            this.error = true;
            print("[ERROR] Order direction could not be determined! orderType: " + orderType);
        }
		if (this.type != '1' && price == 0) {
            this.error = true;
            print("[ERROR] Price must be given for limit and stop orders! order_type: " + type + " | price: " + price);
		}
    }
}
