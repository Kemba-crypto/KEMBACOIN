import logging
from ecdsa_keygen import ECDSA_keygen  # Ensure this import reflects your codebase implementation
from blockchain.config import DEFAULT_TRANSACTION_FEE_KEM, KEM_TO_KEMITES_RATIO


# Configure logging
logging.basicConfig(level=logging.INFO)


class Transaction:
    def __init__(self, sender, recipient, amount_kem, signature, fee_kem=DEFAULT_TRANSACTION_FEE_KEM):
        """
        Represents a transaction.

        :param sender: Address of the sender.
        :param recipient: Address of the recipient.
        :param amount_kem: Amount of KEM to transfer.
        :param signature: Transaction signature by the sender.
        :param fee_kem: Transaction fee in KEM.
        :raises ValueError: If input values are invalid.
        """
        if amount_kem <= 0:
            raise ValueError("Transaction amount must be greater than zero.")
        if fee_kem < 0:
            raise ValueError("Transaction fee must be non-negative.")
        if not sender or not recipient:
            raise ValueError("Sender and recipient addresses cannot be empty.")

        self.sender = sender  # Sender's address
        self.recipient = recipient  # Recipient's address
        self.amount_kemites = int(amount_kem * KEM_TO_KEMITES_RATIO)  # Convert amount to kemites
        self.fee_kemites = int(fee_kem * KEM_TO_KEMITES_RATIO)  # Convert fee to kemites
        self.signature = signature  # Signature by the sender
        self.transaction_id = self.generate_transaction_id()  # Unique transaction ID

        logging.info(f"Transaction created: {self}")

    def generate_transaction_id(self):
        """
        Generate a unique transaction ID based on the sender, recipient, amount, and current time.
        """
        import hashlib
        transaction_data = f"{self.sender}{self.recipient}{self.amount_kemites}{self.fee_kemites}{self.signature}"
        return hashlib.sha256(transaction_data.encode()).hexdigest()

    @staticmethod
    def sign_transaction(private_key, sender, recipient, amount_kem):
        """
        Sign the transaction data with the sender's private key.

        :param private_key: Sender's private key.
        :param sender: Sender's address.
        :param recipient: Recipient's address.
        :param amount_kem: Amount of KEM to transfer.
        :return: Signature of the transaction.
        :raises ValueError: If signing fails due to invalid inputs.
        """
        try:
            transaction_data = f"{sender}->{recipient}:{int(amount_kem * KEM_TO_KEMITES_RATIO)}"
            ecdsa_keygen = ECDSA_keygen()
            ecdsa_keygen.private_key = private_key
            signature = ecdsa_keygen.sign_message(transaction_data)
            logging.info("Transaction signed successfully.")
            return signature
        except ValueError as e:
            logging.error(f"Error signing transaction: {e}")
            raise ValueError(f"Error signing transaction: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during signing: {e}")
            raise RuntimeError(f"Unexpected error during signing: {e}")

    def verify_transaction(self, public_key):
        """
        Verify that the transaction was signed by the sender's private key.

        :param public_key: The sender's public key for verification.
        :return: True if valid, False otherwise.
        :raises ValueError: If verification fails due to invalid inputs.
        """
        try:
            transaction_data = f"{self.sender}->{self.recipient}:{self.amount_kemites}"
            ecdsa_keygen = ECDSA_keygen()
            result = ecdsa_keygen.verify_signature(self.signature, transaction_data)
            if result:
                logging.info("Transaction verification succeeded.")
            else:
                logging.warning("Transaction verification failed.")
            return result
        except ValueError as e:
            logging.error(f"Error verifying transaction: {e}")
            raise ValueError(f"Error verifying transaction: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during verification: {e}")
            raise RuntimeError(f"Unexpected error during verification: {e}")

    def __str__(self):
        """
        Provides a readable string representation of the transaction.
        """
        return (f"Transaction(sender={self.sender}, recipient={self.recipient}, "
                f"amount={self.amount_kemites / KEM_TO_KEMITES_RATIO} KEM ({self.amount_kemites} kemites), "
                f"fee={self.fee_kemites / KEM_TO_KEMITES_RATIO} KEM ({self.fee_kemites} kemites))")


class LibraryTransaction:
    def __init__(self, uploader, title, hash_value, category, fee_kemites):
        """
        Represents a library-related transaction for the AI-driven library.

        :param uploader: Address of the uploader.
        :param title: Title of the uploaded book/document.
        :param hash_value: Hash of the book's content.
        :param category: Categorization of the content.
        :param fee_kemites: Fee in kemites for the transaction.
        :raises ValueError: If input values are invalid.
        """
        if not uploader or not title:
            raise ValueError("Uploader and title cannot be empty.")
        if not hash_value:
            raise ValueError("Hash value is required to verify content integrity.")
        if fee_kemites < 0:
            raise ValueError("Transaction fee must be non-negative.")

        self.uploader = uploader
        self.title = title
        self.hash_value = hash_value
        self.category = category
        self.fee_kemites = int(fee_kemites)

        logging.info(f"Library transaction created: {self}")

    def verify_content_hash(self, content):
        """
        Verify that the provided content matches the recorded hash.

        :param content: Content to verify against the recorded hash.
        :return: True if the content hash matches, False otherwise.
        """
        import hashlib
        try:
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            if content_hash == self.hash_value:
                logging.info("Content hash verification succeeded.")
                return True
            else:
                logging.warning("Content hash verification failed.")
                return False
        except Exception as e:
            logging.error(f"Error verifying content hash: {e}")
            raise ValueError(f"Error verifying content hash: {e}")

    def __str__(self):
        """
        Provides a readable string representation of the library transaction.
        """
        return (f"LibraryTransaction(uploader={self.uploader}, title={self.title}, "
                f"hash_value={self.hash_value}, category={self.category}, "
                f"fee={self.fee_kemites / KEM_TO_KEMITES_RATIO} KEM)")


# Example usage for testing
if __name__ == "__main__":
    try:
        tx = Transaction(sender="address1", recipient="address2", amount_kem=10, signature="sample_signature")
        print(tx)

        lib_tx = LibraryTransaction(uploader="address1", title="Sample Title", hash_value="abc123", category="Tech", fee_kemites=100)
        print(lib_tx)
    except ValueError as e:
        logging.error(f"Validation error: {e}")

