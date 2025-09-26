package med.dto; 
import java.io.Serializable; 
 
public class TransferRecord implements Serializable { 
    public String from; 
    public String to; 
    public String timestamp; 
 
    public TransferRecord(String from, String to, String timestamp) { 
        this.from = from; this.to = to; this.timestamp = timestamp; 
    } 
 
    @Override public String toString() { 
        return timestamp + ": " + from + " -> " + to; 
    } 
} 

