package med.dto; 
import java.io.Serializable; 
 
public class Transfer implements Serializable { 
    public String batchId; 
    public String from; 
    public String to; 
    public String timestamp; // ISO-8601 
 
    public Transfer(String batchId, String from, String to, String timestamp) { 
        this.batchId = batchId; 
        this.from = from; 
        this.to = to; 
        this.timestamp = timestamp; 
    } 
} 

