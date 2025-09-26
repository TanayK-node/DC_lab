package med; 
 
import med.dto.*; 
import java.rmi.registry.LocateRegistry; 
import java.rmi.registry.Registry; 
import java.time.Instant; 
 
public class Client { 
    public static void main(String[] args) throws Exception { 
        Registry reg = LocateRegistry.getRegistry("127.0.0.1", 1099); 
        Ledger ledger = (Ledger) reg.lookup("Ledger"); 
 
        // 1) Register 
        Ack a1 = ledger.registerBatch(new Batch( 
            "M123", "Paracetamol 500mg", "MF-ACME", "2026-12-31", "Factory" 
        )); 
        System.out.println("Register: " + a1.ok + " " + a1.message); 
 
        // 2) Factory -> Distributor 
        Ack a2 = ledger.transferBatch(new Transfer( 
            "M123", "Factory", "Distributor D45", Instant.now().toString() 
        )); 
        System.out.println("F->D: " + a2.ok + " " + a2.message); 
 
        // 3) Distributor -> Pharmacy 
        Ack a3 = ledger.transferBatch(new Transfer( 
            "M123", "Distributor D45", "Pharmacy P17", Instant.now().toString() 
        )); 
        System.out.println("D->P: " + a3.ok + " " + a3.message); 
 
        // 4) Verify 
        VerifyResponse v = ledger.verifyBatch("M123"); 
        System.out.println("Found: " + v.found + " Owner: " + v.currentOwner + " Status: " + v.status); 
        for (TransferRecord tr : v.history) { 
            System.out.println("- " + tr); 
        } 
    } 
} 

