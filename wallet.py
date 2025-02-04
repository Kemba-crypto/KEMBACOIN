import os
import json
import hashlib
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA256
import base64
import logging
import requests
import secrets
import time

SALT_SIZE = 16
ITERATIONS = 100_000
KEY_LENGTH = 32
WALLET_FILE = "wallet.json"

logging.basicConfig(level=logging.INFO)


class Wallet:
    def __init__(self, password, blockchain_url="http://127.0.0.1:5000"):
        """
        Initialize the wallet with password and blockchain URL.
        If a wallet file exists, load the wallet; otherwise, create a new one.
        """
        self.password = password
        self.blockchain_url = blockchain_url
        self.wallet_file = WALLET_FILE
        self.salt = None
        self.key = None
        self.address = None
        self.encrypted_seed_phrase = None
        self.balance = 0

        if os.path.exists(self.wallet_file):
            self.load_wallet(password)
        else:
            self.create_new_wallet()

    def _generate_encryption_key(self, salt):
        """
        Generate an encryption key using PBKDF2 and the provided salt.
        """
        kdf = PBKDF2HMAC(
            algorithm=SHA256(),
            length=KEY_LENGTH,
            salt=salt,
            iterations=ITERATIONS,
            backend=default_backend(),
        )
        return base64.urlsafe_b64encode(kdf.derive(self.password.encode()))

    def _generate_wallet_address(self, salt):
        """
        Generate a unique wallet address using the password and salt.
        """
        derived_key = hashlib.pbkdf2_hmac("sha256", self.password.encode(), salt, ITERATIONS)
        return f"address_{hashlib.sha256(derived_key).hexdigest()[:16]}"

    def create_new_wallet(self):
        """
        Create a new wallet with a unique address and encrypted seed phrase.
        """
        self.salt = os.urandom(SALT_SIZE)
        self.key = self._generate_encryption_key(self.salt)
        self.address = self._generate_wallet_address(self.salt)
        seed_phrase = " ".join(secrets.choice(open("/usr/share/dict/words").readlines()).strip() for _ in range(12))
        self.encrypted_seed_phrase = self.encrypt_seed_phrase(seed_phrase)
        self.save_wallet()
        logging.info(f"New wallet created. Address: {self.address}")

    def encrypt_seed_phrase(self, seed_phrase):
        """
        Encrypt the seed phrase using the wallet's encryption key.
        """
        return base64.urlsafe_b64encode(
            hashlib.pbkdf2_hmac(
                "sha256", seed_phrase.encode(), self.key, ITERATIONS
            )
        ).decode()

    def decrypt_seed_phrase(self):
        """
        Decrypt the seed phrase using the wallet's encryption key.
        """
        try:
            return base64.urlsafe_b64decode(self.encrypted_seed_phrase).decode()
        except Exception as e:
            logging.error(f"Failed to decrypt seed phrase: {e}")
            return None

    def save_wallet(self):
        """
        Save wallet details to a file.
        """
        data = {
            "address": self.address,
            "salt": base64.urlsafe_b64encode(self.salt).decode() if self.salt else None,
            "encrypted_seed_phrase": self.encrypted_seed_phrase,
        }
        with open(self.wallet_file, "w") as file:
            json.dump(data, file)
        logging.info("Wallet saved successfully.")

    def load_wallet(self, password):
        """
        Load wallet details from a file and validate the password.
        """
        try:
            with open(self.wallet_file, "r") as file:
                data = json.load(file)

            # Backward compatibility: If salt is missing, assume it's an old wallet
            if "salt" in data and data["salt"]:
                self.salt = base64.urlsafe_b64decode(data["salt"])
                self.key = self._generate_encryption_key(self.salt)
                self.address = self._generate_wallet_address(self.salt)
            else:
                # Old wallet logic: Address stored directly in the file
                self.salt = None
                self.key = None
                self.address = data["address"]

            self.encrypted_seed_phrase = data.get("encrypted_seed_phrase")
            logging.info(f"Wallet loaded successfully. Address: {self.address}")
        except FileNotFoundError:
            raise ValueError("Wallet file not found.")
        except json.JSONDecodeError:
            raise ValueError("Corrupted wallet file.")
        except Exception as e:
            logging.error(f"Error loading wallet: {e}")
            raise

    def query_balance(self):
        """
        Query the wallet's balance from the blockchain.
        """
        try:
            response = requests.get(f"{self.blockchain_url}/get_balance/{self.address}")
            if response.status_code == 200:
                balance_data = response.json()
                self.balance = balance_data.get("balance", 0) / 10**8  # Convert to KEM
                return self.balance
            else:
                error_msg = response.json().get("error", "Unknown error")
                raise Exception(f"Error fetching balance: {error_msg}")
        except requests.RequestException as e:
            logging.error(f"Connection error while fetching balance: {e}")
            return 0

    def refresh_balance(self):
        """
        Refresh the wallet balance and return the updated value.
        """
        self.balance = self.query_balance()
        logging.info(f"Balance refreshed: {self.balance} KEM")
        return self.balance

    def sign_transaction(self, data):
        """
        Create a cryptographic signature for a transaction using the private key.
        """
        private_key = hashlib.pbkdf2_hmac("sha256", self.password.encode(), self.salt or b"", ITERATIONS)
        transaction_hash = hashlib.sha256(json.dumps(data).encode()).digest()
        signature = hashlib.pbkdf2_hmac("sha256", transaction_hash, private_key, ITERATIONS)
        return base64.urlsafe_b64encode(signature).decode()

    def send_transaction(self, recipient, amount):
        """
        Send a transaction to the blockchain.
        """
        transaction_data = {
            "sender": self.address,
            "recipient": recipient,
            "amount_kem": amount,
            "timestamp": int(time.time()),
        }
        signature = self.sign_transaction(transaction_data)
        transaction_data["signature"] = signature

        try:
            response = requests.post(
                f"{self.blockchain_url}/add_transaction",
                json=transaction_data
            )
            if response.status_code == 200:
                logging.info("Transaction sent successfully.")
                return response.json()
            else:
                error_msg = response.json().get("error", "Unknown error")
                raise Exception(f"Transaction failed: {error_msg}")
        except requests.RequestException as e:
            logging.error(f"Connection error while sending transaction: {e}")
            return {"error": str(e)}

    def export_wallet(self, export_path):
        """
        Export wallet details (excluding sensitive data) to a file for backup.
        """
        try:
            data = {
                "address": self.address,
                "encrypted_seed_phrase": self.encrypted_seed_phrase,
            }
            with open(export_path, "w") as file:
                json.dump(data, file)
            logging.info(f"Wallet exported successfully to {export_path}.")
        except Exception as e:
            logging.error(f"Failed to export wallet: {e}")

