# © 2024 The Nation of Tamarikemba and Kembacoin Developers  
# © 2024 Ha Malak BN Adam Aman RA  

import requests
import json


class WalletInterface:
    def __init__(self, node_url):
        """
        Initialize the wallet interface with a blockchain node URL.
        :param node_url: URL of the blockchain node.
        """
        self.node_url = node_url

    def broadcast_transaction(self, sender, recipient, amount_kem, signature):
        """
        Broadcast a transaction from the wallet to the blockchain node.
        :param sender: Sender's wallet address.
        :param recipient: Recipient's wallet address.
        :param amount_kem: Amount of KEM to transfer.
        :param signature: Signature of the transaction.
        :return: Response from the node.
        """
        transaction = {
            "sender": sender,
            "recipient": recipient,
            "amount_kem": amount_kem,
            "signature": signature,
        }
        try:
            response = requests.post(f"{self.node_url}/broadcast_transaction", json=transaction)
            return response.json()
        except requests.RequestException as e:
            print(f"Error broadcasting transaction: {e}")
            return None

    def get_wallet_balance(self, wallet_address):
        """
        Fetch the balance of a wallet address from the blockchain node.
        :param wallet_address: The wallet address to query.
        :return: Balance in KEM or None in case of error.
        """
        try:
            response = requests.get(f"{self.node_url}/get_balance/{wallet_address}")
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching wallet balance: {e}")
            return None

    def get_transaction_status(self, transaction_id):
        """
        Check the status of a transaction.
        :param transaction_id: The ID of the transaction to query.
        :return: Transaction status or None in case of error.
        """
        try:
            response = requests.get(f"{self.node_url}/transaction_status/{transaction_id}")
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching transaction status: {e}")
            return None

    def fetch_transaction_history(self, wallet_address):
        """
        Fetch the transaction history for a wallet address.
        :param wallet_address: The wallet address to query.
        :return: List of transactions or None in case of error.
        """
        try:
            response = requests.get(f"{self.node_url}/get_transaction_history/{wallet_address}")
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching transaction history: {e}")
            return None

