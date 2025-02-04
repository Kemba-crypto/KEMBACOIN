from flask import Flask, request, jsonify
from blockchain.blockchain import Blockchain
from blockchain.block import Block
from flask_cors import CORS
import logging
import os
from functools import lru_cache
import os
os.environ['address_38f57665762f2def'] = '100'

# Configuration Class
class Config:
    WALLET_ADDRESS = os.getenv('address_38f57665762f2def')
    if WALLET_ADDRESS is None:
        logging.error("Environment variable 'address_38f57665762f2def' is not set!")
        exit(1)  # Exit the app if critical config is missing
    NODE_PORT = int(os.getenv('NODE_PORT', 5000))  # Default to 5000 if not set

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable cross-origin requests if needed

# Apply configuration
app.config.from_object(Config)

# Initialize blockchain
blockchain = Blockchain()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

@app.route('/status', methods=['GET'])
def get_status():
    """Returns the status of the blockchain node."""
    return jsonify({
        "status": "online",
        "node": "Kembacoin Blockchain",
        "version": blockchain.version
    }), 200

@app.route('/latest_block', methods=['GET'])
def get_latest_block():
    """Returns the latest block on the blockchain."""
    try:
        latest_block = blockchain.get_latest_block()
        logging.info(f"Latest block: {latest_block}")
        return jsonify(latest_block), 200
    except Exception as e:
        logging.error(f"Error fetching latest block: {e}")
        return jsonify({"error": "Failed to fetch latest block"}), 500

@app.route('/mine_block', methods=['POST'])
def mine_block():
    """Allows miners to mine a block."""
    miner_wallet_address = request.get_json().get('miner_wallet_address', app.config['WALLET_ADDRESS'])

    if not miner_wallet_address:
        return jsonify({"error": "Miner wallet address is required"}), 400

    try:
        blockchain.mine_block(active_miners=[miner_wallet_address])
        return jsonify({"message": "Block mined successfully", "miner": miner_wallet_address}), 200
    except ValueError as ve:
        logging.error(f"Mining value error: {ve}")
        return jsonify({"error": "Invalid mining data"}), 400
    except Exception as e:
        logging.error(f"Error during mining: {e}")
        return jsonify({"error": "Failed to mine block"}), 500

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    """Adds a transaction to the pending transactions pool."""
    data = request.get_json()
    required_fields = ['sender', 'recipient', 'amount_kem', 'signature', 'transaction_id']

    if not all(field in data for field in required_fields):
        logging.warning("Missing transaction fields: %s", [field for field in required_fields if field not in data])
        return jsonify({"error": "Missing transaction fields"}), 400

    if not isinstance(data['amount_kem'], int) or data['amount_kem'] <= 0:
        return jsonify({"error": "Amount must be a positive integer"}), 400

    try:
        blockchain.add_transaction(
            sender=data['sender'],
            recipient=data['recipient'],
            amount_kem=data['amount_kem'],
            signature=data['signature'],
            transaction_id=data['transaction_id']
        )
        logging.info("Transaction added: %s", data['transaction_id'])
        return jsonify({"message": "Transaction added successfully"}), 200
    except Exception as e:
        logging.error(f"Error adding transaction: {e}")
        return jsonify({"error": "Failed to add transaction"}), 500

@app.route('/get_balance/<wallet_address>', methods=['GET'])
def get_balance(wallet_address):
    """Fetches the balance of a wallet."""
    try:
        balance = blockchain.get_balance(wallet_address)
        return jsonify({"wallet_address": wallet_address, "balance": balance / 10**8}), 200
    except Exception as e:
        logging.error(f"Error fetching balance for {wallet_address}: {e}")
        return jsonify({"error": "Failed to fetch balance"}), 500

@app.route('/chain', methods=['GET'])
@lru_cache(maxsize=1)  # Cache the result of this function
def get_chain():
    """Returns the entire blockchain."""
    try:
        chain_data = [block.to_dict() for block in blockchain.chain]
        return jsonify({"length": len(chain_data), "chain": chain_data}), 200
    except Exception as e:
        logging.error(f"Error fetching blockchain: {e}")
        return jsonify({"error": "Failed to fetch blockchain"}), 500

@app.route('/pending_transactions', methods=['GET'])
def get_pending_transactions():
    """Returns the list of pending transactions."""
    try:
        return jsonify({"pending_transactions": blockchain.pending_transactions}), 200
    except Exception as e:
        logging.error(f"Error fetching pending transactions: {e}")
        return jsonify({"error": "Failed to fetch pending transactions"}), 500

@app.route('/set_wallet', methods=['POST'])
def set_wallet():
    """Sets the default wallet address."""
    data = request.get_json()
    wallet_address = data.get('wallet_address', None)
    if wallet_address:
        app.config['WALLET_ADDRESS'] = wallet_address
        return jsonify({"message": f"Wallet address set to {wallet_address}."}), 200
    return jsonify({"error": "Invalid wallet address."}), 400

@app.route('/set_node_port', methods=['POST'])
def set_node_port():
    """Sets the port for the node."""
    data = request.get_json()
    try:
        node_port = int(data.get('port', app.config['NODE_PORT']))
        app.config['NODE_PORT'] = node_port
        return jsonify({"message": f"Node port set to {node_port}."}), 200
    except ValueError:
        return jsonify({"error": "Invalid port number."}), 400

@app.route('/submit_block', methods=['POST'])
def submit_block():
    """Handles block submissions from miners."""
    try:
        block_data = request.get_json()
        logging.info(f"Received block submission: {block_data}")  # Log the incoming payload

        if not block_data:
            return jsonify({"error": "No block data provided"}), 400

        required_fields = ["index", "previous_hash", "timestamp", "transactions", "kemites_reward", "nonce1", "nonce2", "nonce3", "difficulty", "hash"]
        missing_fields = [field for field in required_fields if field not in block_data]

        if missing_fields:
            logging.error(f"Missing fields in block submission: {missing_fields}")
            return jsonify({"error": f"Missing fields: {missing_fields}"}), 400

        new_block = Block(
            index=block_data["index"],
            previous_hash=block_data["previous_hash"],
            timestamp=block_data["timestamp"],
            transactions=block_data["transactions"],
            kemites_reward=block_data["kemites_reward"],
            nonce1=block_data["nonce1"],
            nonce2=block_data["nonce2"],
            nonce3=block_data["nonce3"],
            difficulty=block_data["difficulty"]
        )

        if blockchain.add_block(new_block):
            logging.info(f"Block {new_block.index} added successfully.")
            return jsonify({"status": "Block added successfully"}), 200
        else:
            logging.warning(f"Block validation failed for block: {block_data}")
            return jsonify({"error": "Block validation failed"}), 400

    except Exception as e:
        logging.error(f"Error processing block submission: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Start the blockchain node server
    logging.info("Starting Kembacoin blockchain node...")
    app.run(host='0.0.0.0', port=app.config['NODE_PORT'])

