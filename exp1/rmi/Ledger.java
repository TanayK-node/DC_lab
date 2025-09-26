package med; 
 
import java.rmi.Remote; 
import java.rmi.RemoteException; 
import med.dto.*; 
 
public interface Ledger extends Remote { 
    Ack registerBatch(Batch b) throws RemoteException; 
    Ack transferBatch(Transfer t) throws RemoteException; 
    VerifyResponse verifyBatch(String batchId) throws RemoteException; 
} 

