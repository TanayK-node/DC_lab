# ledger_node.py
import json, threading, queue, time
from concurrent import futures
from dataclasses import dataclass, field
import grpc

import ledger_pb2 as pb
import ledger_pb2_grpc as pbg

@dataclass(frozen=True)
class ChainRecord:
    index: int
    event_type: pb.EventType
    batch_id: str
    payload_json: str
    actor_id: str
    lamport_assigned: int
    request_id: str

class AppendOnlyLedger:
    def __init__(self):
        self._lock = threading.RLock()
        self._chain = []
        self._processed = set()
        self._lamport = 0

    def _bump_lamport(self, incoming):
        self._lamport = max(self._lamport, incoming) + 1
        return self._lamport

    def append_if_new(self, ev: pb.Event) -> tuple[bool, int, str]:
        with self._lock:
            if ev.request_id in self._processed:
                for r in reversed(self._chain):
                    if r.request_id == ev.request_id:
                        return True, r.lamport_assigned, "duplicate_request_id_accepted"
                return True, self._lamport, "duplicate_request_id_accepted"

            lamport = self._bump_lamport(ev.lamport_sent)
            rec = ChainRecord(
                index=len(self._chain),
                event_type=ev.type,
                batch_id=ev.batch_id,
                payload_json=ev.payload_json,
                actor_id=ev.actor_id,
                lamport_assigned=lamport,
                request_id=ev.request_id,
            )
            self._chain.append(rec)
            self._processed.add(ev.request_id)
            return True, lamport, "appended"

    def verify_batch(self, batch_id: str, lamport_sent: int) -> tuple[bool, str, str, int]:
        with self._lock:
            lamport = self._bump_lamport(lamport_sent)
            status, last_actor = "UNKNOWN", ""
            for r in reversed(self._chain):
                if r.batch_id == batch_id:
                    if r.event_type == pb.BATCH_CREATED: status = "CREATED"
                    elif r.event_type == pb.SHIPMENT_UPDATED: status = "IN_TRANSIT"
                    elif r.event_type == pb.READY_FOR_SALE: status = "READY_FOR_SALE"
                    elif r.event_type == pb.SOLD_TO_PATIENT: status = "SOLD"
                    last_actor = r.actor_id
                    break
            return status != "UNKNOWN", status, last_actor, lamport

    def head(self): 
        with self._lock: return len(self._chain), self._lamport

@dataclass
class WorkItem:
    ev: pb.Event
    ctx: grpc.ServicerContext
    result_event: threading.Event = field(default_factory=threading.Event)
    result: tuple[bool, int, str] | None = None

class WorkerPool:
    def __init__(self, ledger: AppendOnlyLedger, n_workers: int = 4):
        self.q = queue.Queue()
        self.ledger, self._stop, self.workers = ledger, threading.Event(), []
        for i in range(n_workers):
            t = threading.Thread(target=self._run, name=f"worker-{i}", daemon=True)
            t.start(); self.workers.append(t)

    def _run(self):
        while not self._stop.is_set():
            try: item = self.q.get(timeout=0.25)
            except queue.Empty: continue
            try: item.result = self.ledger.append_if_new(item.ev)
            except Exception as e: item.result = (False, 0, f"error:{e}")
            finally: item.result_event.set(); self.q.task_done()

    def submit(self, item: WorkItem): self.q.put(item)
    def stop(self):
        self._stop.set()
        for _ in self.workers: self.q.put(WorkItem(ev=pb.Event(), ctx=None))
        for t in self.workers: t.join(timeout=1.0)

class LedgerService(pbg.LedgerServicer):
    def __init__(self, pool, ledger): self.pool, self.ledger = pool, ledger

    def SubmitEvent(self, ev, context):
        wi = WorkItem(ev=ev, ctx=context); self.pool.submit(wi)
        wi.result_event.wait(timeout=5.0)
        if wi.result is None: return pb.EventAck(accepted=False, message="timeout", lamport_assigned=0)
        ok, lam, msg = wi.result; return pb.EventAck(accepted=ok, message=msg, lamport_assigned=lam)

    def VerifyBatch(self, req, context):
        authentic, status, last_actor, lam = self.ledger.verify_batch(req.batch_id, req.lamport_sent)
        return pb.VerifyReply(authentic=authentic, status=status, last_actor=last_actor, lamport_observed=lam)

    def GetChainHead(self, req, context):
        h, l = self.ledger.head(); return pb.ChainHeadReply(height=h, lamport=l)

def serve(host="0.0.0.0", port=50051, rpc_workers=8, worker_threads=4):
    ledger, pool = AppendOnlyLedger(), WorkerPool(AppendOnlyLedger(), worker_threads)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=rpc_workers))
    pbg.add_LedgerServicer_to_server(LedgerService(pool, ledger), server)
    server.add_insecure_port(f"{host}:{port}"); server.start()
    print(f"[LedgerNode] listening on {host}:{port}"); 
    try: 
        while True: time.sleep(86400)
    except KeyboardInterrupt: pool.stop(); server.stop(grace=None)

if __name__ == "__main__": serve()
