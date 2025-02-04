# © 2024 The Nation of Tamarikemba and Kembacoin Developers  
# © 2024 Ha Malak BN Adam Aman RA  

import time
from threading import Thread

class Synchronizer:
    def __init__(self, wallet, network):
        """
        Initialize the synchronizer.
        :param wallet: The wallet instance to synchronize.
        :param network: The network connection to interact with the blockchain.
        """
        self.wallet = wallet
        self.network = network
        self.running = False

    def start(self):
        """
        Start the synchronization process in a separate thread.
        """
        self.running = True
        self.sync_thread = Thread(target=self.run)
        self.sync_thread.start()

    def stop(self):
        """
        Stop the synchronization process.
        """
        self.running = False
        if self.sync_thread:
            self.sync_thread.join()

    def run(self):
        """
        Main loop for synchronizing the wallet with the blockchain.
        """
        while self.running:
            try:
                # Fetch the latest transactions for the wallet's addresses
                for address in self.wallet.get_addresses():
                    transactions = self.network.get_transactions(address)
                    self.wallet.update_transactions(address, transactions)

                # Update the wallet's balance
                self.wallet.update_balance()

                # Polling interval
                time.sleep(10)  # Poll every 10 seconds
            except Exception as e:
                print(f"Synchronization error: {e}")
                time.sleep(5)  # Retry after a short delay

    def fetch_utxos(self, address):
        """
        Fetch UTXOs for a specific address from the network.
        :param address: Wallet address.
        :return: List of UTXOs.
        """
        return self.network.get_utxos(address)

    def handle_new_block(self, block_data):
        """
        Handle a new block event from the network.
        :param block_data: New block data.
        """
        print(f"New block detected: {block_data['block_height']}")
        self.run()  # Re-synchronize to process changes

