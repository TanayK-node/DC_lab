import grpc
from concurrent import futures
import ledger_pb2
import ledger_pb2_grpc
from pymongo import MongoClient

class LedgerServiceServicer(ledger_pb2_grpc.LedgerServiceServicer):
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["factory_ledger"]
        self.col = self.db["transactions"]

    def RecordTransaction(self, request, context):
        data = {
            "batch_id": request.batch_id,
            "sender": request.sender,
            "receiver": request.receiver,
            "status": request.status
        }
        self.col.insert_one(data)
        print(f"✅ Recorded: {data}")
        return ledger_pb2.TransactionResponse(message="Transaction recorded at Factory.")

    def GetLedger(self, request, context):
        entries = []
        for tx in self.col.find():
            entries.append(ledger_pb2.LedgerEntry(
                batch_id=tx["batch_id"], sender=tx["sender"],
                receiver=tx["receiver"], status=tx["status"]
            ))
        return ledger_pb2.LedgerData(entries=entries)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ledger_pb2_grpc.add_LedgerServiceServicer_to_server(LedgerServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("🏭 Factory node running on port 50051...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
