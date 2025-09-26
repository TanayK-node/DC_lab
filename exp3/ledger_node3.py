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
        self._chain, self._processed, self._lamport = [], set(), 0

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
            rec = ChainRecord(len(self._chain), ev.type, ev.batch_id, ev.payload_json,
                              ev.actor_id, lamport, ev.request_id)
            self._chain.append(rec); self._processed.add(ev.request_id)
            return True, lamport, "appended"

    def verify_batch(self, batch_id: str, lamport_sent: int):
        with self._lock:
            lamport = self._bump_lamport(lamport_sent)
            status, last_actor = "UNKNOWN", ""
            for r in reversed(self._chain):
                if r.batch_id == batch_id:
                    if r.event_type == pb.BATCH_CREATED: status="CREATED"
                    elif r.event_type == pb.SHIPMENT_UPDATED: status="IN_TRANSIT"
                    elif r.event_type == pb.READY_FOR_SALE: status="READY_FOR_SALE"
                    elif r.event_type == pb.SOLD_TO_PATIENT: status="SOLD"
                    last_actor = r.actor_id; break
            return status!="UNKNOWN", status, last_actor, lamport

    def head(self): 
        with self._lock: return len(self._chain), self._lamport

@dataclass
class WorkItem:
    ev: pb.Event
    ctx: grpc.ServicerContext
    result_event: threading.Event = field(default_factory=threading.Event)
    result: tuple[bool, int, str] | None = None

class WorkerPool:
    def __init__(self, ledger: AppendOnlyLedger, n_workers=4):
        self.q, self.ledger, self._stop, self.workers = queue.Queue(), ledger, threading.Event(), []
        for i in range(n_workers):
            t=threading.Thread(target=self._run, name=f"worker-{i}", daemon=True)
            t.start(); self.workers.append(t)

    def _run(self):
        while not self._stop.is_set():
            try: item=self.q.get(timeout=0.25)
            except queue.Empty: continue
            try: item.result=self.ledger.append_if_new(item.ev)
            except Exception as e: item.result=(False,0,f"error:{e}")
            finally: item.result_event.set(); self.q.task_done()

    def submit(self, item: WorkItem): self.q.put(item)
    def stop(self):
        self.
