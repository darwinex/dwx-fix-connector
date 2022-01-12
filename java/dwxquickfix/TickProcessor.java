package dwxquickfix;


public interface TickProcessor {
    
    public void start(App app);
    
    public void onTick(App app, String symbol, History history);
	
	public void onExecutionReport(App app, ExecutionReport executionReport);
}
