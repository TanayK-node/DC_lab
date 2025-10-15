import grpc
import ledger_pb2
import ledger_pb2_grpc

def record_transaction(node_port, batch_id, sender, receiver, status):
    with grpc.insecure_channel(f'localhost:{node_port}') as channel:
        stub = ledger_pb2_grpc.LedgerServiceStub(channel)
        response = stub.RecordTransaction(ledger_pb2.TransactionRequest(
            batch_id=batch_id, sender=sender, receiver=receiver, status=status
        ))
        print(response.message)

if __name__ == "__main__":
    record_transaction(50051, "MED001", "Factory", "Distributor", "Shipped")
    record_transaction(50052, "MED001", "Distributor", "Pharmacy", "Delivered")
    record_transaction(50053, "MED001", "Pharmacy", "Patient", "Sold")
