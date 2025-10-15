package med.dto; 
import java.io.Serializable; 
import java.util.ArrayList; 
import java.util.List; 
 
public class VerifyResponse implements Serializable { 
    public boolean found; 
    public String status;          // READY_FOR_SALE / IN_CHAIN / NOT_FOUND 
    public String currentOwner; 
    public String drugName; 
    public String manufacturerId; 
    public String expiryDate; 
    public List<TransferRecord> history = new ArrayList<>(); 
 
    @Override public String toString() { 
        return "VerifyResponse{found=" + found + ", status=" + status + 
               ", owner=" + currentOwner + ", drug=" + drugName + 
               ", history=" + history + "}"; 
    } 
} 

