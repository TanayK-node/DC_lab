import election_node

if __name__ == "__main__":
    # Example: distributor triggers election
    election_node.NODE_ID = 2
    election_node.ALL_NODES = {
        "factory": ("localhost:50051", 1),
        "distributor": ("localhost:50052", 2),
        "pharmacy": ("localhost:50053", 3),
        "patient": ("localhost:50054", 4),
    }
    election_node.start_election()