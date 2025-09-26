# distributor_client.py
import time, threading, random
from client_common import make_channel, submit_event
import ledger_pb2 as pb, ledger_pb2_grpc as pbg

lamport, lamport_lock = 0, threading.Lock()
def get_next_lamport():
    global lamport
    with lamport_lock: lamport += 2; return lamport

def ship_batch(stub, batch_id):
    ack = submit_event(stub, "distributor-1", pb.SHIPMENT_UPDATED, batch_id,
                       {"from":"ACME","to":"Pharmacy-A"}, get_next_lamport())
    print("DIST shipped:", batch_id, ack.message, ack.lamport_assigned)

def run_distributor(batch_ids):
    stub = pbg.LedgerStub(make_channel()); threads=[]
    for b in batch_ids:
        t=threading.Thread(target=ship_batch,args=(stub,b)); t.start(); threads.append(t)
        time.sleep(random.uniform(0.03,0.15))
    for t in threads: t.join()

if __name__=="__main__":
    run_distributor(["BATCH-..."])
