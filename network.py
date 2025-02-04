import requests
import json

class Network:
    def __init__(self, node_url="http://127.0.0.1:5000"):
        """
        Initialize the network connection.
        :param node_url: URL of the blockchain node to connect to.
        """
        self.node_url = node_url

    def get_latest_block(self):
        """
        Fetch the latest block from the blockchain.
        :return: Latest block data as a dictionary.
        """
        try:
            response = requests.get(f"{self.node_url}/latest_block")
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching latest block: {e}")
            return None

    def get_transactions(self, address):
        """
        Fetch transactions related to a specific wallet address.
        :param address: Wallet address.
        :return: List of transactions.
        """
        try:
            response = requests.get(f"{self.node_url}/transactions/{address}")
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching transactions: {e}")
            return []

    def broadcast_transaction(self, transaction_data):
        """
        Broadcast a transaction to the blockchain network.
        :param transaction_data: Transaction details as a dictionary.
        :return: Response from the node.
        """
        try:
            response = requests.post(f"{self.node_url}/broadcast_transaction", json=transaction_data)
            return response.json()
        except requests.RequestException as e:
            print(f"Error broadcasting transaction: {e}")
            return {"status": "error", "message": str(e)}

    def get_utxos(self, address):
        """
        Fetch UTXOs for a specific wallet address.
        :param address: Wallet address.
        :return: List of UTXOs.
        """
        try:
            response = requests.get(f"{self.node_url}/utxos/{address}")
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching UTXOs: {e}")
            return []

    def check_connection(self):
        """
        Check the connection to the blockchain node.
        :return: True if connected, False otherwise.
        """
        try:
            response = requests.get(f"{self.node_url}/ping")
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Connection error: {e}")
            return False

