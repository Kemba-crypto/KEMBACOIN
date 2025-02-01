# © 2024 The Nation of Tamarikemba and Kembacoin Developers  
# © 2024 Ha Malak BN Adam Aman RA  

import time
import logging
import threading
import json

# Configure logging
logging.basicConfig(level=logging.INFO)

class QSystem:
    def __init__(self):
        """
        Initialize the Q system with a global transaction log and adaptive parameters.
        """
        self.global_transaction_log = {}  # Key: transaction_id, Value: (status, timestamp)
        self.timeout_threshold = 30  # Seconds before retrying or flagging late transactions
        self.learning_rate = 0.1  # How quickly Q adapts its parameters
        self.failed_nodes = {}  # Track nodes with repeated failures
        self.lock = threading.Lock()  # For concurrency control

    def log_transaction(self, transaction_id, block):
        """
        Log a new transaction in the global transaction log.

        :param transaction_id: The unique identifier for the transaction.
        :param block: The block containing the transaction.
        :return: True if logged successfully, False if duplicate.
        """
        with self.lock:
            if transaction_id in self.global_transaction_log:
                logging.warning(f"Transaction {transaction_id} is duplicate.")
                return False
            self.global_transaction_log[transaction_id] = {
                'status': 'pending',
                'timestamp': time.time(),
                'block': block.to_dict()  # Store the block details as well
            }
            logging.info(f"Transaction {transaction_id} logged successfully in Block {block.index}.")
            return True

    def validate_transaction(self, transaction_id):
        """
        Validate a transaction to ensure it's not duplicate or late.

        :param transaction_id: The unique identifier for the transaction.
        :return: "valid", "duplicate", or "late".
        """
        with self.lock:
            if transaction_id not in self.global_transaction_log:
                logging.error(f"Transaction {transaction_id} is invalid (unknown or spoofed).")
                return "invalid"

            entry = self.global_transaction_log[transaction_id]
            elapsed_time = time.time() - entry['timestamp']

            if entry['status'] == 'completed':
                logging.warning(f"Transaction {transaction_id} is duplicate.")
                return "duplicate"
            elif elapsed_time > self.timeout_threshold:
                logging.warning(f"Transaction {transaction_id} flagged as late.")
                return "late"
            else:
                return "valid"

    def mark_transaction_completed(self, transaction_id):
        """
        Mark a transaction as successfully processed.

        :param transaction_id: The unique identifier for the transaction.
        """
        with self.lock:
            if transaction_id in self.global_transaction_log:
                self.global_transaction_log[transaction_id]['status'] = 'completed'
                logging.info(f"Transaction {transaction_id} marked as completed.")
            else:
                logging.error(f"Transaction {transaction_id} not found in log.")

    def monitor_node(self, node_id):
        """
        Track node performance and adaptively flag nodes for repeated failures.

        :param node_id: The unique identifier for the node.
        :return: True if node is flagged for failures, False otherwise.
        """
        with self.lock:
            if node_id not in self.failed_nodes:
                self.failed_nodes[node_id] = {'failures': 0, 'last_failure': time.time()}
            else:
                self.failed_nodes[node_id]['failures'] += 1
                self.failed_nodes[node_id]['last_failure'] = time.time()

            if self.failed_nodes[node_id]['failures'] > 3:
                logging.warning(f"Node {node_id} flagged for repeated failures.")
                return True
            return False

    def adapt_timeout(self, network_conditions):
        """
        Dynamically adapt the timeout threshold based on network performance.

        :param network_conditions: "congested" or "smooth" to indicate network state.
        """
        with self.lock:
            previous_threshold = self.timeout_threshold
            if network_conditions == "congested":
                self.timeout_threshold += self.learning_rate * self.timeout_threshold
            elif network_conditions == "smooth":
                self.timeout_threshold = max(5, self.timeout_threshold - self.learning_rate * self.timeout_threshold)

            if previous_threshold != self.timeout_threshold:
                logging.info(f"Timeout threshold adapted from {previous_threshold:.2f} to {self.timeout_threshold:.2f} seconds.")

    def log_activity(self):
        """
        Print the Q system's activity log for monitoring and debugging.
        """
        with self.lock:
            logging.info("\n===== Q System Activity Log =====")
            logging.info("Global Transaction Log:")
            if not self.global_transaction_log:
                logging.info("  - No transactions logged.")
            else:
                for transaction_id, details in self.global_transaction_log.items():
                    block_info = details['block']
                    logging.info(f"  - {transaction_id}: {details['status']}, Block {block_info['index']} ({block_info['hash'][:10]}...)")

            logging.info("\nFailed Nodes:")
            if not self.failed_nodes:
                logging.info("  - No failed nodes.")
            else:
                for node_id, info in self.failed_nodes.items():
                    logging.info(f"  - Node {node_id}: {info['failures']} failures, last failure at {time.ctime(info['last_failure'])}")

    def recover_failed_nodes(self):
        """
        Recover nodes flagged as 'failed' after a stability period.
        """
        with self.lock:
            current_time = time.time()
            for node_id, info in list(self.failed_nodes.items()):
                if current_time - info['last_failure'] > 300:  # 5 minutes recovery time
                    logging.info(f"Node {node_id} has been stable for 5 minutes. Removing from failed nodes.")
                    del self.failed_nodes[node_id]

    def persist_data(self, file_path):
        """
        Persist the Q system's state to a file for recovery purposes.

        :param file_path: The path to save the Q system data.
        """
        try:
            with open(file_path, "w") as file:
                data = {
                    "global_transaction_log": self.global_transaction_log,
                    "failed_nodes": self.failed_nodes,
                    "timeout_threshold": self.timeout_threshold,
                }
                json.dump(data, file)
                logging.info(f"Q System data persisted to {file_path}.")
        except Exception as e:
            logging.error(f"Failed to persist Q System data: {e}")

    def load_data(self, file_path):
        """
        Load the Q system's state from a file.

        :param file_path: The path to load the Q system data from.
        """
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                self.global_transaction_log = data.get("global_transaction_log", {})
                self.failed_nodes = data.get("failed_nodes", {})
                self.timeout_threshold = data.get("timeout_threshold", self.timeout_threshold)
                logging.info(f"Q System data loaded from {file_path}.")
        except Exception as e:
            logging.error(f"Failed to load Q System data: {e}")

