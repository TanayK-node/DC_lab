# client_common.py
import grpc, uuid, json
import ledger2_pb2 as pb
import ledger2_pb2_grpc as pbg



def make_channel(addr="localhost:50051"):
    return grpc.insecure_channel(addr)

def submit_event(stub, actor_id, etype, batch_id, payload: dict, lamport):
    ev = pb.Event(
        request_id=str(uuid.uuid4()),
        actor_id=actor_id,
        type=etype,
        batch_id=batch_id,
        payload_json=json.dumps(payload, separators=(",", ":")),
        signature=b"",
        lamport_sent=lamport,
    )
    return stub.SubmitEvent(ev)
