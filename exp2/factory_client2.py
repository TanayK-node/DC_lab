# factory_client.py
import time, threading, random
from client_common import make_channel, submit_event
import ledger_pb2 as pb, ledger_pb2_grpc as pbg

lamport, lamport_lock = 0, threading.Lock()
def get_next_lamport():
    global lamports
    with lamport_lock: lamport += 1; return lamport

def create_batch(stub, batch_id):
    local_lamport = get_next_lamport()
    ack = submit_event(stub, "factory-1", pb.BATCH_CREATED, batch_id,
                       {"mfg": "ACME", "exp": "2027-12-31"}, local_lamport)
    print("FACTORY created:", batch_id, ack.message, ack.lamport_assigned)

def run_factory(n_batches=5):
    stub = pbg.LedgerStub(make_channel()); threads=[]
    for i in range(n_batches):
        batch_id = f"BATCH-{int(time.time()*1000)}-{i}"
        t = threading.Thread(target=create_batch, args=(stub, batch_id)); t.start(); threads.append(t)
        time.sleep(random.uniform(0.05,0.2))
    for t in threads: t.join()

if __name__ == "__main__": run_factory()
