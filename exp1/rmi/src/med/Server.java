package med; 
 
import java.rmi.registry.LocateRegistry; 
import java.rmi.registry.Registry; 
 
public class Server { 
    public static void main(String[] args) throws Exception { 
        // Start (or get) registry on default port 1099 
        try { 
            LocateRegistry.createRegistry(1099); 
            System.out.println("RMI registry started on 1099"); 
        } catch (Exception e) { 
            System.out.println("RMI registry probably already running"); 
        } 
 
        LedgerImpl ledger = new LedgerImpl(); 
        Registry reg = LocateRegistry.getRegistry(); 
        reg.rebind("Ledger", ledger); 
        System.out.println("Ledger RMI server bound as 'Ledger' and ready"); 
    } 
} 

