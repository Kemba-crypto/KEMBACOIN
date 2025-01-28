import os
import json
import time
import random
import logging
from blockchain.q_system import QSystem
from blockchain.block import Block
from blockchain.transactions import Transaction
from blockchain.ai_librarian import AILibrarian
from blockchain.config import DEFAULT_TRANSACTION_FEE_KEM, KEM_TO_KEMITES_RATIO
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

CONFIG_PATH = "/etc/kembacoin777/config.json"

class Blockchain:
    _instance = None  # Singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Load configuration
        self.config = self.load_config()

        self.version = self.config.get("version", "4.0")
        self.difficulty = self.config.get("difficulty", 4)
        self.chain = [self.create_genesis_block()]  # Blockchain starts with a genesis block
        self.pending_transactions = []
        self.q_system = QSystem()
        self.max_supply_kem = self.config.get("max_supply_kem", 77_700_000)
        self.total_supply_kemites = self.max_supply_kem * 10**8
        self.current_supply_kemites = 0
        self.block_time = self.config.get("block_time", 7 * 60)  # 7 minutes in seconds
        self.adjustment_interval = self.config.get("adjustment_interval", 5)
        self.random_intervals = self.config.get("random_intervals", [7, 70, 700, 777, 7000])
        self.next_random_block = self.set_next_random_block()
        self.library_ai = AILibrarian()

        # Bitcoin RPC Setup
        self.bitcoin_rpc = None
        self.setup_bitcoin_rpc()

        logging.info(f"Blockchain initialized. Genesis block hash: {self.chain[0].hash}")

    @staticmethod
    def load_config():
        try:
            with open(CONFIG_PATH, "r") as config_file:
                config = json.load(config_file)
                logging.info(f"Configuration loaded from {CONFIG_PATH}")
                return config
        except FileNotFoundError:
            logging.error(f"Configuration file not found at {CONFIG_PATH}. Using defaults.")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding configuration file: {e}. Using defaults.")
            return {}

    def setup_bitcoin_rpc(self):
        rpc_user = self.config.get("rpc_user", "user")
        rpc_password = self.config.get("rpc_password", "password")
        rpc_host = self.config.get("rpc_host", "127.0.0.1")
        rpc_port = self.config.get("rpc_port", "8332")

        try:
            self.bitcoin_rpc = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")
            logging.info("Connected to Bitcoin Core RPC")
        except Exception as e:
            logging.error(f"Failed to connect to Bitcoin RPC: {e}")

    def create_genesis_block(self):
        genesis_block = Block(
            index=0,
            previous_hash="0",
            timestamp=1700000000,
            transactions=[],
            kemites_reward=0,
            nonce1=0,
            nonce2=0,
            nonce3=0,
            difficulty=self.difficulty,
            version=self.version,
        )
        genesis_block.hash = genesis_block.calculate_hash()
        logging.info(f"Genesis block created: {genesis_block.hash}")
        return genesis_block

    def set_next_random_block(self):
        interval = random.choice(self.random_intervals)
        next_block_index = len(self.chain) + interval
        logging.info(f"Next random block will occur at block index {next_block_index}")
        return next_block_index

    def get_latest_block(self):
        latest_block = self.chain[-1]
        logging.info(f"Latest Block: Index: {latest_block.index}, Hash: {latest_block.hash}, Previous Hash: {latest_block.previous_hash}")
        return latest_block

    def add_block(self, block):
        latest_block = self.get_latest_block()

        if block.previous_hash != latest_block.hash:
            logging.warning(
                f"Block {block.index} rejected: Previous hash mismatch (Expected: {latest_block.hash}, Found: {block.previous_hash}).")
            return False

        if block.difficulty != self.difficulty:
            logging.warning(
                f"Block {block.index} rejected: Difficulty mismatch (Expected: {self.difficulty}, Found: {block.difficulty}).")
            return False

        if not block.hash.startswith("0" * block.difficulty):
            logging.warning(
                f"Block {block.index} rejected: Proof of Work mismatch (Hash: {block.hash}, Difficulty: {block.difficulty}).")
            return False

        if block.hash != block.calculate_hash():
            logging.warning(
                f"Block {block.index} rejected: Hash mismatch (Expected: {block.calculate_hash()}, Found: {block.hash}).")
            return False

        self.chain.append(block)
        logging.info(f"Block {block.index} added to the chain successfully.")
        return True

    def mine_block(self, active_miners, kemites_reward=77 * 10**8):
        if not self.pending_transactions:
            logging.info("No transactions to mine.")
            return

        current_block_index = len(self.chain)

        miner_wallet_address = self.select_random_miner(active_miners) if current_block_index == self.next_random_block else active_miners[0]
        if not miner_wallet_address:
            logging.warning("No miner available.")
            return

        reward_transaction = {
            "sender": "BLOCKCHAIN_REWARD",
            "recipient": miner_wallet_address,
            "amount_kem": kemites_reward / 10**8,
            "fee_kem": 0,
            "transaction_id": f"reward_{current_block_index}",
        }
        self.q_system.log_transaction(reward_transaction["transaction_id"])
        self.pending_transactions.append(reward_transaction)

        new_block = Block(
            index=current_block_index,
            previous_hash=self.get_latest_block().hash,
            timestamp=time.time(),
            transactions=self.pending_transactions,
            kemites_reward=kemites_reward,
            nonce1=0,
            nonce2=0,
            nonce3=0,
            difficulty=self.difficulty,
            version=self.version,
        )
        new_block.mine_block()
        self.chain.append(new_block)
        self.pending_transactions.clear()
        logging.info(f"Block {new_block.index} mined by {miner_wallet_address}")

    def anchor_to_bitcoin(self, data):
        if not self.bitcoin_rpc:
            logging.warning("Bitcoin RPC is not available.")
            return False

        try:
            data_hex = data.encode().hex()
            txid = self.bitcoin_rpc.createrawtransaction(inputs=[], outputs={"data": data_hex})
            signed_tx = self.bitcoin_rpc.signrawtransactionwithwallet(txid)
            txid = self.bitcoin_rpc.sendrawtransaction(signed_tx["hex"])
            logging.info(f"Data anchored to Bitcoin blockchain. TXID: {txid}")
            return txid
        except JSONRPCException as e:
            logging.error(f"Failed to anchor data to Bitcoin: {e}")
            return False

