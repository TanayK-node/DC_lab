# pharmacy_client.py
import time, threading, random
from client_common import make_channel, submit_event
import ledger_pb2 as pb, ledger_pb2_grpc as pbg

lamport, lamport_lock = 0, threading.Lock()
def get_next_lamport():
    global lamport
    with lamport_lock: lamport += 1; return lamport

def process_batch(stub, batch_id):
    lam1=get_next_lamport()
    ack=submit_event(stub,"pharmacy-A",pb.READY_FOR_SALE,batch_id,{"shelf":"A3"},lam1)
    print("PHARM ready:", batch_id, ack.message, ack.lamport_assigned)
    time.sleep(random.uniform(0.02,0.1))
    lam2=get_next_lamport()
    ack2=submit_event(stub,"pharmacy-A",pb.SOLD_TO_PATIENT,batch_id,{"order_id":"ORD-"+batch_id},lam2)
    print("PHARM sold:", batch_id, ack2.message, ack2.lamport_assigned)

def run_pharmacy(batch_ids):
    stub=pbg.LedgerStub(make_channel()); threads=[]
    for b in batch_ids:
        t=threading.Thread(target=process_batch,args=(stub,b)); t.start(); threads.append(t)
    for t in threads: t.join()

if __name__=="__main__": run_pharmacy([...])
