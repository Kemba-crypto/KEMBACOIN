from flask import Flask, jsonify, request
from kembacoin7.blockchain import Blockchain
from kembacoin7.p2p_network import P2PNode
import logging
import asyncio
import threading
from signal import signal, SIGINT
import sys

class Node:
    def __init__(self, node_id, p2p_node=None):
        self.node_id = node_id
        self.blockchain = Blockchain()
        self.p2p_node = p2p_node

    def display_chain(self):
        logging.info("Displaying the blockchain...")
        try:
            return [block.to_dict() for block in self.blockchain.chain]
        except Exception as e:
            logging.error(f"Error displaying blockchain: {e}")
            raise

app = Flask(__name__)

blockchain = Blockchain()
p2p_node = P2PNode(host="127.0.0.1", port=5000, blockchain=blockchain)
node = Node(node_id="node_1", p2p_node=p2p_node)

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "running", "chain_length": len(node.blockchain.chain)}), 200

@app.route('/chain', methods=['GET'])
def get_chain():
    try:
        chain = node.display_chain()
        return jsonify({"chain": chain}), 200
    except Exception as e:
        logging.error(f"Error retrieving blockchain: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    try:
        data = request.json
        required_fields = ["sender", "recipient", "amount_kem", "transaction_id"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing fields in request"}), 400

        transaction_id = data["transaction_id"]
        validation_status = node.blockchain.q_system.validate_transaction(transaction_id)
        if validation_status != "valid":
            return jsonify({"error": f"Transaction {transaction_id} is {validation_status}"}), 400

        if node.blockchain.add_transaction(
            sender=data["sender"],
            recipient=data["recipient"],
            amount_kem=data["amount_kem"],
            signature=data.get("signature", ""),
            transaction_id=transaction_id
        ):
            node.blockchain.q_system.log_transaction(transaction_id)
            asyncio.run(node.p2p_node.broadcast_transaction(data))
            return jsonify({"message": "Transaction added and broadcasted successfully"}), 201
        else:
            return jsonify({"error": "Transaction validation failed"}), 400
    except Exception as e:
        logging.error(f"Error adding transaction: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/mine', methods=['POST'])
def mine_block():
    try:
        data = request.json
        required_fields = ["miner_address", "kemites_reward"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing fields in request"}), 400

        node.blockchain.mine_block(
            active_miners=[data["miner_address"]],
            kemites_reward=data["kemites_reward"]
        )

        latest_block = node.blockchain.get_latest_block()
        asyncio.run(node.p2p_node.broadcast_block(latest_block))
        return jsonify({"message": "Block mined and broadcasted successfully"}), 201
    except Exception as e:
        logging.error(f"Error mining block: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/broadcast_transaction', methods=['POST'])
def broadcast_transaction():
    try:
        data = request.json
        required_fields = ["sender", "recipient", "amount_kem", "transaction_id"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing fields in request"}), 400

        asyncio.run(node.p2p_node.broadcast_transaction(data))
        return jsonify({"message": "Transaction broadcasted successfully"}), 200
    except Exception as e:
        logging.error(f"Error broadcasting transaction: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/broadcast_block', methods=['POST'])
def broadcast_block():
    try:
        data = request.json
        if not data.get("block"):
            return jsonify({"error": "Missing block data"}), 400

        asyncio.run(node.p2p_node.broadcast_block(data["block"]))
        return jsonify({"message": "Block broadcasted successfully"}), 200
    except Exception as e:
        logging.error(f"Error broadcasting block: {e}")
        return jsonify({"error": str(e)}), 500

def shutdown_gracefully(signal, frame):
    logging.info("Shutting down gracefully...")
    sys.exit(0)

signal(SIGINT, shutdown_gracefully)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    def run_p2p_server():
        asyncio.run(p2p_node.start_server())

    threading.Thread(target=run_p2p_server, daemon=True).start()

    app.run(host="0.0.0.0", port=5000)

