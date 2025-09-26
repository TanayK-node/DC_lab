package med; 
 
import med.dto.*; 
import java.rmi.server.UnicastRemoteObject; 
import java.rmi.RemoteException; 
import java.util.*; 
 
public class LedgerImpl extends UnicastRemoteObject implements Ledger { 
 
    // In-memory stores 
    private final Map<String, Map<String, String>> batches = new HashMap<>(); 
    private final Map<String, List<TransferRecord>> history = new HashMap<>(); 
 
    public LedgerImpl() throws RemoteException { 
        super(); // exports the object 
    } 
 
    @Override 
    public synchronized Ack registerBatch(Batch b) throws RemoteException { 
        if (batches.containsKey(b.batchId)) return new Ack(false, "Batch already exists"); 
        Map<String, String> meta = new HashMap<>(); 
        meta.put("drug_name", b.drugName); 
        meta.put("manufacturer_id", b.manufacturerId); 
        meta.put("expiry_date", b.expiryDate); 
        meta.put("current_owner", b.owner); 
        batches.put(b.batchId, meta); 
 
        history.put(b.batchId, new ArrayList<>()); 
        return new Ack(true, "Batch registered"); 
    } 
 
    @Override 
    public synchronized Ack transferBatch(Transfer t) throws RemoteException { 
        if (!batches.containsKey(t.batchId)) return new Ack(false, "Unknown batch"); 
        String current = batches.get(t.batchId).get("current_owner"); 
        if (!Objects.equals(current, t.from)) { 
            return new Ack(false, "Transfer denied: not current owner"); 
        } 
        history.get(t.batchId).add(new TransferRecord(t.from, t.to, t.timestamp)); 
        batches.get(t.batchId).put("current_owner", t.to); 
        return new Ack(true, "Transfer recorded"); 
    } 
 
    @Override 
    public synchronized VerifyResponse verifyBatch(String batchId) throws RemoteException { 
        VerifyResponse v = new VerifyResponse(); 
        if (!batches.containsKey(batchId)) { 
            v.found = false; v.status = "NOT_FOUND"; return v; 
        } 
        Map<String, String> meta = batches.get(batchId); 
        v.found = true; 
        v.currentOwner = meta.get("current_owner"); 
        v.drugName = meta.get("drug_name"); 
        v.manufacturerId = meta.get("manufacturer_id"); 
        v.expiryDate = meta.get("expiry_date"); 
        v.status = v.currentOwner.toLowerCase().startsWith("pharmacy") ? "READY_FOR_SALE" : "IN_CHAIN"; 
        v.history.addAll(history.get(batchId)); 
        return v; 
    } 
} 

