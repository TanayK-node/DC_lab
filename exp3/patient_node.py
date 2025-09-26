import time
import election_node
import ledger_pb2, ledger_pb2_grpc   # for medicine ledger
import election_pb2, election_pb2_grpc  # for bully algorithm

if __name__ == "__main__":
    election_node.NODE_ID = 4
    election_node.ALL_NODES = {
        "factory": ("localhost:50051", 1),
        "distributor": ("localhost:50052", 2),
        "pharmacy": ("localhost:50053", 3),
        "patient": ("localhost:50054", 4),
    }
    server = election_node.start_server(50054)
    time.sleep(2)
    election_node.start_election()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        server.stop(0)

