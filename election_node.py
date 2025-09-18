# election_node.py
import grpc
from concurrent import futures
import time
import threading
import election_pb2
import election_pb2_grpc   # ✅ Correct proto import

# Global state
NODE_ID = None   # will be set by each node runner script
ALL_NODES = {}   # { "factory": ("localhost:50051", 1), ... }
leader_id = None
lock = threading.Lock()


# ---------------------- gRPC Service ----------------------
class ElectionService(election_pb2_grpc.ElectionServicer):
    def StartElection(self, request, context):
        """Handle election request from another node"""
        if int(request.node_id) < NODE_ID:
            return election_pb2.ElectionReply(higher_node_alive=True)
        return election_pb2.ElectionReply(higher_node_alive=False)

    def DeclareCoordinator(self, request, context):
        """Receive new coordinator announcement"""
        global leader_id
        with lock:
            leader_id = int(request.leader_id)
        print(f"[*] New leader elected: Node {leader_id}")
        return election_pb2.Ack(ok=True)


# ---------------------- Server ----------------------
def start_server(port):
    """Start election gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    election_pb2_grpc.add_ElectionServicer_to_server(ElectionService(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"[*] Election server started on port {port} for node {NODE_ID}")
    return server


# ---------------------- Bully Algorithm ----------------------
def start_election():
    """Trigger bully election"""
    global leader_id
    print(f"[*] Node {NODE_ID} starting election...")
    higher_found = False

    for name, (address, nid) in ALL_NODES.items():
        if nid > NODE_ID:
            try:
                with grpc.insecure_channel(address) as channel:
                    stub = election_pb2_grpc.ElectionStub(channel)
                    response = stub.StartElection(
                        election_pb2.ElectionRequest(node_id=str(NODE_ID))
                    )
                    if response.higher_node_alive:
                        print(f"[*] Higher node {nid} is alive, waiting for it to take over...")
                        higher_found = True
            except Exception as e:
                print(f"[!] Could not contact node {nid}: {e}")
                continue

    if not higher_found:
        # No higher nodes responded, declare self as leader
        print(f"[*] Node {NODE_ID} becomes leader")
        leader_id = NODE_ID
        for name, (address, nid) in ALL_NODES.items():
            try:
                with grpc.insecure_channel(address) as channel:
                    stub = election_pb2_grpc.ElectionStub(channel)
                    stub.DeclareCoordinator(
                        election_pb2.CoordinatorMsg(leader_id=str(NODE_ID))
                    )
            except:
                continue

