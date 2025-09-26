import grpc
from concurrent import futures
import time, threading
import election_pb2, election_pb2_grpc

# Config
NODE_ID = None
NODE_NAME = ""
ALL_NODES = {}   # { "node1": ("localhost:60051", 1), ... }

# State
leader_id = None
lock = threading.Lock()
coordinator_event = threading.Event()

# Settings
RPC_TIMEOUT = 1.0
WAIT_FOR_COORD = 2.0

class ElectionService(election_pb2_grpc.ElectionServicer):
    def StartElection(self, request, context):
        requester = int(request.node_id)
        if NODE_ID > requester:
            threading.Thread(target=start_election, daemon=True).start()
            return election_pb2.ElectionReply(higher_node_alive=True)
        return election_pb2.ElectionReply(higher_node_alive=False)

    def DeclareCoordinator(self, request, context):
        global leader_id
        with lock:
            leader_id = int(request.leader_id)
            coordinator_event.set()
        print(f"[{NODE_NAME}] Leader updated → Node {leader_id}")
        return election_pb2.Ack(ok=True)

def start_server(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    election_pb2_grpc.add_ElectionServicer_to_server(ElectionService(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"[{NODE_NAME}] Election server running on port {port}")
    return server

def start_election():
    global leader_id
    print(f"[{NODE_NAME}] Starting election...")
    higher = False
    coordinator_event.clear()

    for _, (addr, nid) in ALL_NODES.items():
        if nid <= NODE_ID:
            continue
        try:
            ch = grpc.insecure_channel(addr)
            stub = election_pb2_grpc.ElectionStub(ch)
            resp = stub.StartElection(
                election_pb2.ElectionRequest(node_id=str(NODE_ID)),
                timeout=RPC_TIMEOUT
            )
            if resp.higher_node_alive:
                higher = True
        except:
            continue

    if higher:
        if coordinator_event.wait(timeout=WAIT_FOR_COORD):
            return
        else:
            # no leader announced, retry
            start_election()
            return
    else:
        with lock:
            leader_id = NODE_ID
        print(f"[{NODE_NAME}] I am the new leader")
        for _, (addr, nid) in ALL_NODES.items():
            try:
                ch = grpc.insecure_channel(addr)
                stub = election_pb2_grpc.ElectionStub(ch)
                stub.DeclareCoordinator(
                    election_pb2.CoordinatorMsg(leader_id=str(NODE_ID)),
                    timeout=RPC_TIMEOUT
                )
            except:
                continue
        coordinator_event.set()

def auto_election(interval=10):
    """Run election periodically every `interval` seconds."""
    def loop():
        while True:
            time.sleep(interval)
            start_election()
    t = threading.Thread(target=loop, daemon=True)
    t.start()

def get_leader():
    with lock:
        return leader_id