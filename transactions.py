# © 2024 The Nation of Tamarikemba and Kembacoin Developers  
# © 2024 Ha Malak BN Adam Aman RA  

from ecdsa_keygen import ECDSA_keygen  # Import the ECDSA_keygen class for signing and verification


class WalletTransaction:
    def __init__(self, sender, recipient, amount_kem, fee_kem=0.01):
        """
        Represents a transaction created by the wallet.
        :param sender: Address of the sender
        :param recipient: Address of the recipient
        :param amount_kem: Amount of KEM to transfer
        :param fee_kem: Transaction fee in KEM
        """
        if amount_kem <= 0:
            raise ValueError("Transaction amount must be greater than zero.")
        if not sender or not recipient:
            raise ValueError("Sender and recipient addresses cannot be empty.")

        self.sender = sender  # Sender's address
        self.recipient = recipient  # Recipient's address
        self.amount_kemites = int(amount_kem * 10**8)  # Convert amount to kemites
        self.fee_kemites = int(fee_kem * 10**8)  # Convert fee to kemites
        self.signature = None  # Will be set when the transaction is signed

    def sign_transaction(self, private_key):
        """
        Sign the transaction data with the sender's private key.
        :param private_key: Sender's private key
        :return: The transaction object (with signature set)
        """
        transaction_data = f"{self.sender}->{self.recipient}:{self.amount_kemites}"
        ecdsa_keygen = ECDSA_keygen()
        ecdsa_keygen.private_key = private_key
        self.signature = ecdsa_keygen.sign_message(transaction_data)
        return self

    def get_transaction_data(self):
        """
        Returns the transaction data as a dictionary, suitable for broadcasting.
        :return: Dictionary representing the transaction.
        """
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount_kemites": self.amount_kemites,
            "fee_kemites": self.fee_kemites,
            "signature": self.signature.hex() if self.signature else None,
        }

    def __str__(self):
        """
        Provides a readable string representation of the transaction.
        """
        return (f"Transaction(sender={self.sender}, recipient={self.recipient}, "
                f"amount={self.amount_kemites / 10**8} KEM ({self.amount_kemites} kemites), "
                f"fee={self.fee_kemites / 10**8} KEM ({self.fee_kemites} kemites), "
                f"signature={'Present' if self.signature else 'Not signed'})")


class WalletLibraryTransaction:
    def __init__(self, uploader, title, content, category, fee_kemites):
        """
        Represents a library-related transaction for uploading content to the blockchain.
        :param uploader: Address of the uploader
        :param title: Title of the uploaded book/document
        :param content: Content of the book/document
        :param category: Categorization of the content
        :param fee_kemites: Fee in kemites for the transaction
        """
        self.uploader = uploader
        self.title = title
        self.content = content
        self.category = category
        self.fee_kemites = int(fee_kemites * 10**8)

    def prepare_metadata(self, blockchain):
        """
        Process content through the AI librarian and return metadata.
        :param blockchain: Blockchain object with AI librarian integration.
        :return: Metadata dictionary.
        """
        return blockchain.library_ai.process_content(self.content, {"uploader": self.uploader, "title": self.title})

    def get_transaction_data(self, metadata):
        """
        Returns the transaction data as a dictionary, including metadata for broadcasting.
        :param metadata: Metadata dictionary generated by the blockchain AI librarian.
        :return: Dictionary representing the library transaction.
        """
        return {
            "type": "library",
            "uploader": self.uploader,
            "title": self.title,
            "cid": metadata.get("cid", None),
            "hash_value": metadata.get("hash", None),
            "category": self.category,
            "fee_kemites": self.fee_kemites,
        }

    def __str__(self):
        """
        Provides a readable string representation of the library transaction.
        """
        return (f"LibraryTransaction(uploader={self.uploader}, title={self.title}, "
                f"category={self.category}, fee={self.fee_kemites / 10**8} KEM)")

