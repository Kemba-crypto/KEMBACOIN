# © 2024 The Nation of Tamarikemba and Kembacoin Developers  
# © 2024 Ha Malak BN Adam Aman RA  

import hashlib
import logging
import json
from datetime import datetime

# Configure logging for debug purposes
logging.basicConfig(level=logging.INFO)

class Block:
    def __init__(self, index, previous_hash, timestamp, transactions, kemites_reward, nonce1, nonce2, nonce3, difficulty, version="4.0"):
        """
        Initialize a block with the necessary parameters.
        """
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions if transactions is not None else []  # Ensure transactions is always a list
        self.kemites_reward = kemites_reward  # Block reward in kemites
        self.nonce1 = nonce1
        self.nonce2 = nonce2
        self.nonce3 = nonce3
        self.difficulty = difficulty
        self.version = version
        self.hash = self.calculate_hash()  # Calculate the hash after all attributes are set

    def calculate_hash(self):
        """
        Combines block details, version, and transaction data into a single string, then hashes it using SHA-256.
        """
        # Serialize transactions consistently using json.dumps with sorted keys
        transaction_data = json.dumps(self.transactions, sort_keys=True)

        # Build the block content string
        block_content = (
            f"{self.index}{self.previous_hash}{self.timestamp}{transaction_data}"
            f"{self.kemites_reward}{self.nonce1}{self.nonce2}{self.nonce3}"
            f"{self.difficulty}{self.version}"
        )

        # Return the SHA-256 hash of the combined content
        return hashlib.sha256(block_content.encode()).hexdigest()

    def validate_hash(self):
        """
        Validates the block's hash by recalculating it and comparing it to the current hash.
        """
        recalculated_hash = self.calculate_hash()
        if self.hash == recalculated_hash:
            logging.info(f"Block {self.index} hash validated successfully.")
            return True
        logging.warning(f"Block {self.index} hash validation failed. Expected: {recalculated_hash}, Found: {self.hash}")
        return False

    def to_dict(self):
        """
        Convert the Block instance to a dictionary representation, ensuring transactions are serialized correctly.
        """
        return {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'transactions': [transaction.to_dict() if hasattr(transaction, 'to_dict') else transaction for transaction in self.transactions],
            'kemites_reward': self.kemites_reward,
            'nonce1': self.nonce1,
            'nonce2': self.nonce2,
            'nonce3': self.nonce3,
            'difficulty': self.difficulty,
            'version': self.version,
            'hash': self.hash,
        }

    def mine_block(self, max_iterations=10**8):
        """
        Mines the block by adjusting nonces until the hash satisfies the difficulty target.
        """
        target = "0" * self.difficulty  # Define difficulty target
        logging.info(f"Starting mining of block {self.index} with difficulty {self.difficulty}...")
        start_time = datetime.now()

        # Increment nonces until the hash meets the target
        iteration = 0
        static_hash_content = self.calculate_static_hash_content()
        while not self.hash.startswith(target):
            self.nonce1 += 1
            iteration += 1

            if self.nonce1 >= 1_000_000:
                self.nonce1 = 0
                self.nonce2 += 1
                if self.nonce2 >= 1_000_000:
                    self.nonce2 = 0
                    self.nonce3 += 1

            # Recalculate hash using dynamic nonces
            self.hash = hashlib.sha256(f"{static_hash_content}{self.nonce1}{self.nonce2}{self.nonce3}".encode()).hexdigest()

            # Log progress every 10,000 iterations
            if iteration % 10_000 == 0:
                logging.info(f"Mining progress: {iteration} iterations... Current hash: {self.hash[:10]}...")

            # Break if max iterations exceeded (for debugging/testing purposes)
            if iteration >= max_iterations:
                logging.warning(f"Mining stopped after {iteration} iterations (max cap reached).")
                break

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logging.info(
            f"Block {self.index} successfully mined! Hash: {self.hash}, "
            f"Nonces: [nonce1={self.nonce1}, nonce2={self.nonce2}, nonce3={self.nonce3}], "
            f"Time taken: {duration:.2f}s."
        )

    def calculate_static_hash_content(self):
        """
        Calculate the static portion of the hash content, excluding the dynamic nonces.
        """
        transaction_data = json.dumps(self.transactions, sort_keys=True)
        return (
            f"{self.index}{self.previous_hash}{self.timestamp}{transaction_data}"
            f"{self.kemites_reward}{self.difficulty}{self.version}"
        )

    def __str__(self):
        """
        Returns a human-readable string representation of the block.
        """
        transactions_str = "\n".join([str(tx) for tx in self.transactions])
        kem_as_kem = self.kemites_reward / 10**8

        return (
            f"Block(index={self.index}, hash={self.hash[:10]}..., prev_hash={self.previous_hash[:10]}..., "
            f"timestamp={self.timestamp}, difficulty={self.difficulty}, version={self.version}, "
            f"reward={kem_as_kem} KEM (including fees), transactions:\n{transactions_str})"
        )

    def __repr__(self):
        """
        Provides a concise representation for debugging purposes.
        """
        return (
            f"Block(index={self.index}, hash={self.hash[:10]}..., prev_hash={self.previous_hash[:10]}..., "
            f"timestamp={self.timestamp}, difficulty={self.difficulty}, transactions={len(self.transactions)})"
        )

