# © 2024 The Nation of Tamarikemba and Kembacoin Developers  
# © 2024 Ha Malak BN Adam Aman RA  

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
        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        self.socket = None
        self.connected = False

    def connect(self):
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
        if not self.connected:
            logging.warning(f"Cannot send message. Peer {self.host}:{self.port} is not connected.")
            return
        try:
            self.socket.sendall(json.dumps(message).encode())
            logging.info(f"Message sent to {self.host}:{self.port}: {message}")
        except Exception as e:
            logging.error(f"Failed to send message to {self.host}:{self.port}: {e}")

    def close_connection(self):
        if self.connected:
            self.socket.close()
            self.connected = False
            logging.info(f"Connection to {self.host}:{self.port} closed.")


class P2PNode:
    def __init__(self, host="tamarikemba.com", port=5000, blockchain=None, ssl_cert=None, ssl_key=None):
        self.host = host
        self.port = port
        self.blockchain = blockchain
        self.peers = []
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        if ssl_cert and ssl_key:
            self.ssl_context.load_cert_chain(certfile=ssl_cert, keyfile=ssl_key)

    async def add_peer(self, peer_host, peer_port):
        peer_address = (peer_host, peer_port)
        if peer_address not in self.peers:
            self.peers.append(peer_address)
            logging.info(f"Peer added: {peer_host}:{peer_port}")
        else:
            logging.warning(f"Peer {peer_host}:{peer_port} is already connected.")

    async def start_server(self):
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
        try:
            data = await asyncio.to_thread(client.recv, 4096)
            message = json.loads(data.decode())
            logging.info(f"Received message: {message}")

            if message['type'] == 'bitcoin_anchor':
                anchor_data = message['anchor']
                self.blockchain.store_bitcoin_anchor(anchor_data)
                logging.info(f"Bitcoin anchor stored: {anchor_data}")
                self.broadcast(message)
            elif message['type'] == 'request_anchor_sync':
                self.send_anchor_sync(client)
            else:
                response = {"status": "error", "reason": "unknown_message_type"}
                logging.warning(f"Unknown message type received: {message['type']}")
                client.sendall(json.dumps(response).encode())
        except Exception as e:
            logging.error(f"Error handling client: {e}")
        finally:
            client.close()

    async def broadcast(self, message):
        for peer_host, peer_port in self.peers:
            try:
                await asyncio.to_thread(self._send_message, peer_host, peer_port, message)
            except Exception as e:
                logging.error(f"Failed to broadcast message to {peer_host}:{peer_port}: {e}")

    def _send_message(self, peer_host, peer_port, message):
        try:
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            secure_socket = self.ssl_context.wrap_socket(raw_socket)
            secure_socket.connect((peer_host, peer_port))
            secure_socket.sendall(json.dumps(message).encode())
            secure_socket.close()
        except Exception as e:
            logging.error(f"Failed to send message to {peer_host}:{peer_port}: {e}")

    def request_anchor_sync(self):
        request = {"type": "request_anchor_sync"}
        asyncio.create_task(self.broadcast(request))

    def send_anchor_sync(self, client):
        anchors = self.blockchain.get_all_bitcoin_anchors()
        response = {"type": "anchor_sync", "anchors": anchors}
        client.sendall(json.dumps(response).encode())

    def announce_bitcoin_anchor(self, anchor_data):
        message = {"type": "bitcoin_anchor", "anchor": anchor_data}
        asyncio.create_task(self.broadcast(message))
 
     
          
    
