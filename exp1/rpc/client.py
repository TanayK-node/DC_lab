import grpc
import medicine_pb2 as pb
import medicine_pb2_grpc as pb_grpc

def run():
    # Connect to server
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = pb_grpc.MedicineLedgerStub(channel)

        # Step 1: Register
        response = stub.RegisterMedicine(pb.RegisterMedicineRequest(
            batch_id="batch001",
            owner="Factory"
        ))
        print(response.message)

        # Step 2: Transfer Factory -> Distributor
        response = stub.TransferMedicine(pb.TransferMedicineRequest(
            batch_id="batch001",
            from_party="Factory",             # matches proto field
            to_party="Distributor D45"
        ))
        print("F->D:", response.message)

        # Step 3: Transfer Distributor -> Pharmacy
        response = stub.TransferMedicine(pb.TransferMedicineRequest(
            batch_id="batch001",
            from_party="Distributor D45",     # matches proto field
            to_party="Pharmacy P17"
        ))
        print("D->P:", response.message)

        # Step 4: Verify
        verify = stub.VerifyMedicine(pb.VerifyMedicineRequest(
            batch_id="batch001"
        ))
        status = "READY_FOR_SALE" if verify.exists else "NOT_FOUND"
        print(f"Found: {verify.exists} Owner: {verify.owner} Status: {status}")

        # Step 5: Get History
        print("\n--- Transfer History ---")
        history = stub.GetHistory(pb.GetHistoryRequest(batch_id="batch001"))
        for record in history.records:
            print(f"- {record.timestamp}: {record.from_party} -> {record.to_party}")

if __name__ == "__main__":
    run()
