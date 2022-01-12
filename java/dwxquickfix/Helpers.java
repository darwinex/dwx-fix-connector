package dwxquickfix;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Date;
import java.util.TimeZone;
import java.util.concurrent.ConcurrentHashMap;
import java.text.SimpleDateFormat;
import java.text.ParseException;

import quickfix.FieldMap;
import quickfix.Message;
import quickfix.FieldNotFound;
// import quickfix.Field;

public class Helpers {
    
    public static void print(Object obj) {
        System.out.println(obj);
    }
    
    public static void print(Object obj, String colorString) {
        System.out.println(colorString + obj + Colors.RESET);
    }
    
    public static String messageStr(Message message) {
        return message.toString().replace("\u0001", ", ");
        // return str;
    }
    
    public static int extractInt(FieldMap fieldMap, int field) {
        
        try {
            return Integer.parseInt(fieldMap.getString(field));
        } catch (FieldNotFound e) {
            // print("[ERROR] field not found: " + field);
            return -1;
        }
    }
    
    public static double extractDouble(FieldMap fieldMap, int field) {
        
        try {
            return Double.parseDouble(fieldMap.getString(field));
        } catch (FieldNotFound e) {
            // print("[ERROR] field not found: " + field);
            return -1;
        }
    }
    
    public static Date extractTime(Message message, int field, boolean fromHeader) {
        
        // String sendingTimeStr = "20210517-07:32:14.786";
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd-HH:mm:ss.SSS");
        sdf.setTimeZone(TimeZone.getTimeZone("GMT+0"));
        try {
            String dateTimeStr;
            if (fromHeader) dateTimeStr = message.getHeader().getString(field);
            else dateTimeStr = message.getString(field);
            try {
                // Calendar cal = Calendar.getInstance();
                // return cal.setTime(sdf.parse(dateTimeStr));
                return sdf.parse(dateTimeStr);
            } catch (ParseException e) {
                print("[ERROR] dateTime could not be parsed: " + dateTimeStr);
                return null;
            }
        } catch (FieldNotFound e) {
            print("[ERROR] field not found: " + field);
            return null;
        }
    }
    
    public static Date extractHeaderTime(Message message, int field) {
        return extractTime(message, field, true);
    }
    
    public static Date extractMessageTime(Message message, int field) {
        return extractTime(message, field, false);
    }
    
    // maybe use append and only write new ticks?
    public static void writeHistoryToFile(String historyDir, String symbol, ArrayList<Tick> history) {
        
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd-HH:mm:ss.SSS");
        sdf.setTimeZone(TimeZone.getTimeZone("GMT+0"));
        
        File directory = new File(historyDir);
        if(!directory.exists()) directory.mkdir();
        
        String delimiter = ",";
        
        String text = "dateTime,bid,ask,bidSize,askSize" + System.lineSeparator();
        for (int i=0; i<history.size(); i++) {
            // sdf.format(history.get(i).dateTime)
            text += history.get(i).dateTimeStr + delimiter + history.get(i).depth + delimiter
                    + history.get(i).bid + delimiter + history.get(i).ask + delimiter
                    + history.get(i).bidSize + delimiter + history.get(i).askSize + System.lineSeparator();
        }
        writeToFile(historyDir + "/" + symbol.replace("/", "") + ".csv", text);
    }
    
    public static void writeHistoryTOBToFile(String historyDir, String symbol, ArrayList<TickTOB> history) {
        
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd-HH:mm:ss.SSS");
        sdf.setTimeZone(TimeZone.getTimeZone("GMT+0"));
        
        File directory = new File(historyDir);
        if(!directory.exists()) directory.mkdir();
        
        String delimiter = ",";
        String text = "dateTime,bid,ask" + System.lineSeparator();
        for (int i=0; i<history.size(); i++) {
            // sdf.format(history.get(i).dateTime)
            text += history.get(i).dateTimeStr + delimiter
                    + history.get(i).bid + delimiter + history.get(i).ask + System.lineSeparator();
        }
        writeToFile(historyDir + "/" + symbol.replace("/", "") + "_TOB.csv", text);
    }
    
    public static boolean writeToFile(String filePath, String text) {
        return writeToFile(filePath, text, false);
    }
    
    public static boolean writeToFile(String filePath, String text, boolean append) {
        try {
            FileWriter fileWriter = new FileWriter(filePath, append);
            PrintWriter out = new PrintWriter(fileWriter);
            out.println(text);
            out.close();
            fileWriter.close();
            return true;
        } catch(Exception e) {
            print("Could not write string to file: " + filePath);
//             System.exit(0);
            return false;
        }
    }
    
    public static class Colors {
        // Reset
        public static final String RESET = "\033[0m";  // Text Reset

        // for bold add "1;" after "[". 
        public static final String HEADER = "\033[1;95m";
        public static final String OKBLUE = "\033[1;94m";
        public static final String OKGREEN = "\033[1;92m";
        public static final String WARNING = "\033[1;93m";
        public static final String FAIL = "\033[1;91m";
        
        // Regular Colors
        public static final String BLACK = "\033[0;30m";   // BLACK
        public static final String RED = "\033[0;31m";     // RED
        public static final String GREEN = "\033[0;32m";   // GREEN
        public static final String YELLOW = "\033[0;33m";  // YELLOW
        public static final String BLUE = "\033[0;34m";    // BLUE
        public static final String PURPLE = "\033[0;35m";  // PURPLE
        public static final String CYAN = "\033[0;36m";    // CYAN
        public static final String WHITE = "\033[0;37m";   // WHITE

        // Bold
        public static final String BLACK_BOLD = "\033[1;30m";  // BLACK
        public static final String RED_BOLD = "\033[1;31m";    // RED
        public static final String GREEN_BOLD = "\033[1;32m";  // GREEN
        public static final String YELLOW_BOLD = "\033[1;33m"; // YELLOW
        public static final String BLUE_BOLD = "\033[1;34m";   // BLUE
        public static final String PURPLE_BOLD = "\033[1;35m"; // PURPLE
        public static final String CYAN_BOLD = "\033[1;36m";   // CYAN
        public static final String WHITE_BOLD = "\033[1;37m";  // WHITE

        // Background
        public static final String BLACK_BG = "\033[40m";  // BLACK
        public static final String RED_BG = "\033[41m";    // RED
        public static final String GREEN_BG = "\033[42m";  // GREEN
        public static final String YELLOW_BG = "\033[43m"; // YELLOW
        public static final String BLUE_BG = "\033[44m";   // BLUE
        public static final String PURPLE_BG = "\033[45m"; // PURPLE
        public static final String CYAN_BG = "\033[46m";   // CYAN
        public static final String WHITE_BG = "\033[47m";  // WHITE
    }
}
