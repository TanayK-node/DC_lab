import time
import threading
import election_ring_node

if __name__ == "__main__":
    election_ring_node.NODE_NAME = "pharmacy"
    election_ring_node.NODE_ID = 3
    election_ring_node.ALL_NODES = {
        "factory": ("localhost:50051", 1),
        "distributor": ("localhost:50052", 2),
        "pharmacy": ("localhost:50053", 3),
        "patient": ("localhost:50054", 4),
    }
    server = election_ring_node.start_server(50053)
    time.sleep(2)
    election_ring_node.start_ring_election()

    # Heartbeat
    threading.Thread(target=election_ring_node.heartbeat, daemon=True).start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        server.stop(0)