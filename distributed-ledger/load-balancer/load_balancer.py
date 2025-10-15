import grpc
import ledger_pb2
import ledger_pb2_grpc
from itertools import cycle
from flask import Flask, request, jsonify

# List of backend nodes (you can add more)
NODES = ["localhost:50051", "localhost:50052", "localhost:50053"]

# Create a round-robin iterator
node_cycle = cycle(NODES)

app = Flask(__name__)

@app.route("/record", methods=["POST"])
def record_transaction():
    data = request.json
    # Pick next node
    node = next(node_cycle)
    print(f"📦 Routing request to {node}")

    try:
        with grpc.insecure_channel(node) as channel:
            stub = ledger_pb2_grpc.LedgerServiceStub(channel)
            response = stub.RecordTransaction(
                ledger_pb2.TransactionRequest(
                    batch_id=data["batch_id"],
                    sender=data["sender"],
                    receiver=data["receiver"],
                    status=data["status"],
                )
            )
        return jsonify({"message": response.message, "node_used": node})
    except Exception as e:
        return jsonify({"error": str(e), "node_used": node}), 500

@app.route("/")
def home():
    return "Load Balancer is running 🚀"

if __name__ == "__main__":
    app.run(port=8080)
