import grpc
import time
from concurrent import futures
import DC_LAB.exp1.python.medicine_pb2 as pb
import DC_LAB.exp1.python.medicine_pb2_grpc as pb_grpc

# In-memory stores
batches = {}
history = {}

class LedgerServicer(pb_grpc.LedgerServicer):
    def RegisterBatch(self, request, context):
        if request.batch_id in batches:
            return pb.Ack(ok=False, message="Batch already exists")
        batches[request.batch_id] = {
            "drug_name": request.drug_name,
            "manufacturer_id": request.manufacturer_id,
            "expiry_date": request.expiry_date,
            "current_owner": request.owner,
        }
        history[request.batch_id] = []
        return pb.Ack(ok=True, message="Batch registered")

    def TransferBatch(self, request, context):
        if request.batch_id not in batches:
            return pb.Ack(ok=False, message="Unknown batch")
        # NOTE: access as request.from_ (Python keyword workaround)
        if batches[request.batch_id]["current_owner"] != request.from_:
            return pb.Ack(ok=False, message="Transfer denied: not current owner")
        history[request.batch_id].append({
            "from": request.from_,   # stored as plain string "from"
            "to": request.to,
            "timestamp": request.timestamp,
        })
        batches[request.batch_id]["current_owner"] = request.to
        return pb.Ack(ok=True, message="Transfer recorded")

    def VerifyBatch(self, request, context):
        if request.batch_id not in batches:
            return pb.VerifyResponse(found=False, status="NOT_FOUND")
        meta = batches[request.batch_id]
        status = "READY_FOR_SALE" if meta["current_owner"].lower().startswith("pharmacy") else "IN_CHAIN"
        resp = pb.VerifyResponse(
            found=True,
            status=status,
            current_owner=meta["current_owner"],
            drug_name=meta["drug_name"],
            manufacturer_id=meta["manufacturer_id"],
            expiry_date=meta["expiry_date"],
        )
        for rec in history[request.batch_id]:
            resp.history.add(   # NOTE: here we pass 'from=' (no underscore)
                from_=rec["from"],
                to=rec["to"],
                timestamp=rec["timestamp"]
            )
        return resp

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb_grpc.add_LedgerServicer_to_server(LedgerServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Ledger RPC Server running on :50051")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()