import socket
import ssl
import threading
import json
import time
import logging
import asyncio
from blockchain.block import Block  # Ensure Block is imported for block reconstruction

# Configure logging globally
logging.basicConfig(level=logging.INFO)

class NodePeer:
    def __init__(self, host, port, ssl_context):
        """
        Represents a connected peer with a message queue.
        """
        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        self.socket = None
        self.connected = False

    def connect(self):
        """
        Establish a secure connection to the peer.
        """
        try:
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = self.ssl_context.wrap_socket(raw_socket, server_hostname=self.host)
            self.socket.connect((self.host, self.port))
            self.connected = True
            logging.info(f"Connected to peer {self.host}:{self.port} using SSL")
        except Exception as e:
            logging.error(f"Failed to connect to {self.host}:{self.port}: {e}")
            self.connected = False

    def send_message(self, message):
        """
        Send a message to the peer.
        """
        if not self.connected:
            logging.warning(f"Cannot send message. Peer {self.host}:{self.port} is not connected.")
            return

        try:
            message_json = json.dumps(message)
            self.socket.sendall(message_json.encode())
            logging.info(f"Message sent to {self.host}:{self.port}: {message}")
        except Exception as e:
            logging.error(f"Failed to send message to {self.host}:{self.port}: {e}")

    def close_connection(self):
        """
        Close the secure connection to the peer.
        """
        if self.connected:
            self.socket.close()
            self.connected = False
            logging.info(f"Connection to {self.host}:{self.port} closed.")


class P2PNode:
    def __init__(self, host="tamarikemba.com", port=5000, blockchain=None, ssl_cert=None, ssl_key=None):
        """
        Initialize the node with host, port, blockchain reference, and SSL context.

        :param host: The IP address of the node.
        :param port: The port of the node.
        :param blockchain: The blockchain instance associated with the node.
        :param ssl_cert: Path to the SSL certificate file.
        :param ssl_key: Path to the SSL private key file.
        """
        self.host = host
        self.port = port
        self.blockchain = blockchain
        self.peers = []  # List of connected peers

        # Set up SSL context
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        if ssl_cert and ssl_key:
            self.ssl_context.load_cert_chain(certfile=ssl_cert, keyfile=ssl_key)

    async def add_peer(self, peer_host, peer_port):
        """
        Add a peer to the node.
        """
        peer_address = (peer_host, peer_port)
        if peer_address not in self.peers:
            self.peers.append(peer_address)
            logging.info(f"Peer added: {peer_host}:{peer_port}")
        else:
            logging.warning(f"Peer {peer_host}:{peer_port} is already connected.")

    async def start_server(self):
        """
        Start the server to accept incoming connections with SSL.
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server.bind((self.host, self.port))
            server.listen(5)
            logging.info(f"Node started at {self.host}:{self.port}")

            while True:
                client, addr = await asyncio.to_thread(server.accept)
                logging.info(f"Connection from {addr}")
                secure_client = self.ssl_context.wrap_socket(client, server_side=True)
                asyncio.create_task(self.handle_client(secure_client))
        except Exception as e:
            logging.error(f"Error starting server: {e}")
        finally:
            server.close()

    async def handle_client(self, client):
        """
        Handles incoming messages from peers securely.
        """
        try:
            data = await asyncio.to_thread(client.recv, 4096)
            message = json.loads(data.decode())
            logging.info(f"Received message: {message}")

            if message['type'] == 'transaction':
                transaction = message['data']
                transaction_id = transaction.get('transaction_id')

                # Validate transaction with QSystem
                validation_result = self.blockchain.q_system.validate_transaction(transaction_id)
                if validation_result == "valid":
                    if self.blockchain.add_transaction(
                        sender=transaction['sender'],
                        recipient=transaction['recipient'],
                        amount_kem=transaction['amount_kem'],
                        transaction_id=transaction_id
                    ):
                        response = {"status": "success", "message": f"Transaction {transaction_id} added successfully."}
                        logging.info(response["message"])
                    else:
                        response = {"status": "failed", "message": "Transaction addition failed."}
                else:
                    response = {"status": validation_result, "message": f"Transaction {transaction_id} is {validation_result}."}

            elif message['type'] == 'block':
                block_data = message['data']
                logging.info(f"Received block: {block_data}")

                new_block = Block(
                    index=block_data['index'],
                    previous_hash=block_data['previous_hash'],
                    timestamp=block_data['timestamp'],
                    transactions=block_data['transactions'],
                    kemites_reward=block_data.get('kemites_reward', 0),
                    nonce1=block_data.get('nonce1', 0),
                    nonce2=block_data.get('nonce2', 0),
                    nonce3=block_data.get('nonce3', 0),
                    difficulty=block_data.get('difficulty', self.blockchain.difficulty)
                )

                if self.blockchain.add_block(new_block):
                    response = {"status": "block_added", "message": f"Block {new_block.index} added successfully."}
                    logging.info(response["message"])
                else:
                    response = {"status": "block_rejected", "message": "Block validation failed."}
                    logging.warning(response["message"])

            else:
                response = {"status": "error", "reason": "unknown_message_type"}
                logging.warning(f"Unknown message type received: {message['type']}")

            client.sendall(json.dumps(response).encode())

        except Exception as e:
            logging.error(f"Error handling client: {e}")
        finally:
            client.close()

    async def broadcast_transaction(self, transaction):
        """
        Broadcasts a transaction to all connected peers securely.
        """
        for peer_host, peer_port in self.peers:
            try:
                transaction['transaction_id'] = str(time.time())  # Generate new transaction ID
                logging.info(f"Broadcasting transaction to {peer_host}:{peer_port}...")
                await asyncio.to_thread(self._send_message, peer_host, peer_port, {"type": "transaction", "data": transaction})
            except Exception as e:
                logging.error(f"Failed to broadcast transaction to {peer_host}:{peer_port}: {e}")

    async def broadcast_block(self, block):
        """
        Broadcasts a block to all connected peers securely.
        """
        for peer_host, peer_port in self.peers:
            try:
                logging.info(f"Broadcasting block to {peer_host}:{peer_port}...")
                await asyncio.to_thread(self._send_message, peer_host, peer_port, {"type": "block", "data": block.__dict__})
            except Exception as e:
                logging.error(f"Failed to broadcast block to {peer_host}:{peer_port}: {e}")

    def _send_message(self, peer_host, peer_port, message):
        """
        Helper method to send messages securely to peers.
        """
        try:
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            secure_socket = self.ssl_context.wrap_socket(raw_socket)
            secure_socket.connect((peer_host, peer_port))
            secure_socket.sendall(json.dumps(message).encode())
            secure_socket.close()
        except Exception as e:
            logging.error(f"Failed to send message to {peer_host}:{peer_port}: {e}")

