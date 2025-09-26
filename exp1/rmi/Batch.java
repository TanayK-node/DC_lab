package med.dto; 
import java.io.Serializable; 
 
public class Batch implements Serializable { 
    public String batchId; 
    public String drugName; 
    public String manufacturerId; 
    public String expiryDate; // ISO yyyy-mm-dd 
    public String owner;      // initial owner (Factory) 
 
    public Batch(String batchId, String drugName, String manufacturerId, String expiryDate, String owner) { 
        this.batchId = batchId; 
        this.drugName = drugName; 
        this.manufacturerId = manufacturerId; 
        this.expiryDate = expiryDate; 
        this.owner = owner; 
    } 
} 

