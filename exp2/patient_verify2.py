# patient_verify.py
import time, threading, random, grpc
import ledger_pb2 as pb, ledger_pb2_grpc as pbg

lamport, lamport_lock = 0, threading.Lock()
def get_next_lamport():
    global lamport
    with lamport_lock: lamport += 1; return lamport

def verify_batch(stub, batch_id):
    reply = stub.VerifyBatch(pb.VerifyRequest(
        request_id=f"vrf-{time.time_ns()}",
        batch_id=batch_id,
        lamport_sent=get_next_lamport()
    ))
    print("PATIENT verify:", batch_id, reply.authentic, reply.status, "@L", reply.lamport_observed)

def verify_loop(batch_ids, rounds=10):
    stub=pbg.LedgerStub(grpc.insecure_channel("localhost:50051"))
    for _ in range(rounds):
        threads=[]
        for b in batch_ids:
            t=threading.Thread(target=verify_batch,args=(stub,b)); t.start(); threads.append(t)
        for t in threads: t.join()
        time.sleep(random.uniform(0.05,0.2))

if __name__=="__main__": verify_loop([...])
