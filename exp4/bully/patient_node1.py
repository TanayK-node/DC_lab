import time, election_node

if __name__ == "__main__":
    election_node.NODE_ID = 4
    election_node.NODE_NAME = "Node4"
    election_node.ALL_NODES = {
        "node1": ("localhost:60051", 1),
        "node2": ("localhost:60052", 2),
        "node3": ("localhost:60053", 3),
        "node4": ("localhost:60054", 4),
    }

    server = election_node.start_server(60054)
    time.sleep(2)
    election_node.start_election()
    election_node.auto_election(10)

    try:
        while True:
            print("Current Leader:", election_node.get_leader())
            time.sleep(5)
    except KeyboardInterrupt:
        server.stop(0)