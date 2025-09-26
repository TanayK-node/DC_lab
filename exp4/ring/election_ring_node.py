
import grpc
from concurrent import futures
import threading
import time
import election_ring_pb2
import election_ring_pb2_grpc

# Global state
NODE_ID = None
NODE_NAME = None
ALL_NODES = {}  # { "factory": ("localhost:50051", 1), ... }
RING_ORDER = ["factory", "distributor", "pharmacy", "patient"]

leader_id = None
lock = threading.Lock()


def get_successor(node_name):
    idx = RING_ORDER.index(node_name)
    return RING_ORDER[(idx + 1) % len(RING_ORDER)]


# ---------------------- gRPC Service ----------------------
class ElectionService(election_ring_pb2_grpc.ElectionServicer):
    def StartRingElection(self, request, context):
        """Handle incoming election token"""
        global leader_id

        collected_ids = list(request.candidate_ids)
        initiator_id = request.initiator_id

        # Add self to candidate list if not already
        if NODE_ID not in collected_ids:
            collected_ids.append(NODE_ID)

        # Check if token returned to initiator
        if initiator_id == NODE_ID and len(collected_ids) > 1:
            new_leader = max(collected_ids)
            with lock:
                leader_id = new_leader
            print(f"[*] Ring Election complete. Leader = Node {new_leader}")
            announce_leader(new_leader)
            return election_ring_pb2.Ack(ok=True)

        # Forward token to next alive successor
        forward_token(collected_ids, initiator_id)
        return election_ring_pb2.Ack(ok=True)

    def DeclareCoordinator(self, request, context):
        """Receive new coordinator announcement"""
        global leader_id
        with lock:
            leader_id = int(request.leader_id)
        print(f"[*] New leader announced: Node {leader_id}")
        return election_ring_pb2.Ack(ok=True)


# ---------------------- Server ----------------------
def start_server(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    election_ring_pb2_grpc.add_ElectionServicer_to_server(ElectionService(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"[*] Ring Election server started on port {port} for node {NODE_ID}")
    return server


# ---------------------- Election Logic ----------------------
def forward_token(collected_ids, initiator_id):
    """Pass token to the next alive successor"""
    idx = RING_ORDER.index(NODE_NAME)

    for i in range(1, len(RING_ORDER)):  # loop at most N-1 times
        successor_name = RING_ORDER[(idx + i) % len(RING_ORDER)]
        successor_address, successor_id = ALL_NODES[successor_name]

        try:
            with grpc.insecure_channel(successor_address) as channel:
                stub = election_ring_pb2_grpc.ElectionStub(channel)
                stub.StartRingElection(
                    election_ring_pb2.RingElection(
                        candidate_ids=collected_ids,
                        initiator_id=initiator_id,
                    )
                )
            return  # ✅ stop once token sent successfully
        except:
            print(f"[!] Successor {successor_name} is down, skipping...")
            continue

    # If no successor is alive, this node is the only one left
    new_leader = max(collected_ids)
    with lock:
        leader_id = new_leader
    print(f"[*] Election complete. Only Node {new_leader} remains as leader.")
    announce_leader(new_leader)


def start_ring_election():
    """Trigger ring election"""
    print(f"[*] Node {NODE_ID} starting ring election...")
    forward_token([NODE_ID], NODE_ID)


def announce_leader(new_leader):
    """Broadcast new leader to all nodes"""
    for name, (address, nid) in ALL_NODES.items():
        try:
            with grpc.insecure_channel(address) as channel:
                stub = election_ring_pb2_grpc.ElectionStub(channel)
                stub.DeclareCoordinator(
                    election_ring_pb2.CoordinatorMsg(leader_id=str(new_leader))
                )
        except:
            continue


# ---------------------- Heartbeat ----------------------
def heartbeat():
    """Periodically check if leader is alive, trigger election if not"""
    global leader_id
    while True:
        time.sleep(5)
        if leader_id is None:
            continue

        leader_alive = False
        for name, (address, nid) in ALL_NODES.items():
            if nid == leader_id:
                try:
                    with grpc.insecure_channel(address) as channel:
                        stub = election_ring_pb2_grpc.ElectionStub(channel)
                        # Just ping using DeclareCoordinator as a dummy
                        stub.DeclareCoordinator(
                            election_ring_pb2.CoordinatorMsg(leader_id=str(leader_id))
                        )
                    leader_alive = True
                except:
                    leader_alive = False
                break

        if not leader_alive:
            print(f"[!] Leader {leader_id} not responding, starting election...")
            start_ring_election()