package med.dto; 
import java.io.Serializable; 
 
public class Ack implements Serializable { 
    public boolean ok; 
    public String message; 
    public Ack(boolean ok, String message) { 
        this.ok = ok; this.message = message; 
    } 
    @Override public String toString() { return "Ack{ok=" + ok + ", message='" + message + "'}"; } 
} 

