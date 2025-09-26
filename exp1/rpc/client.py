import grpc
import datetime
import DC_LAB.exp1.python.medicine_pb2 as pb
import DC_LAB.exp1.python.medicine_pb2_grpc as pb_grpc

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = pb_grpc.LedgerStub(channel)

    # 1) Factory registers batch
    ack = stub.RegisterBatch(pb.Batch(
        batch_id="M123",
        drug_name="Paracetamol 500mg",
        manufacturer_id="MF-ACME",
        expiry_date="2026-12-31",
        owner="Factory"
    ))
    print("Register:", ack.ok, ack.message)

    # 2) Transfer Factory -> Distributor
    ack = stub.TransferBatch(pb.Transfer(
        batch_id="M123",
        from="Factory",   # <-- MUST be 'from' (proto field name)
        to="Distributor D45",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    ))
    print("F->D:", ack.ok, ack.message)

    # 3) Transfer Distributor -> Pharmacy
    ack = stub.TransferBatch(pb.Transfer(
        batch_id="M123",
        from="Distributor D45",   # <-- 'from' again
        to="Pharmacy P17",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    ))
    print("D->P:", ack.ok, ack.message)

    # 4) Patient verifies
    v = stub.VerifyBatch(pb.VerifyRequest(batch_id="M123"))
    print("Found:", v.found, "Owner:", v.current_owner, "Status:", v.status)
    for rec in v.history:
        print(f"- {rec.timestamp}: {rec.from} -> {rec.to}")

if __name__ == '__main__':
    run()