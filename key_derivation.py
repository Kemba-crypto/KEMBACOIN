# © 2024 The Nation of Tamarikemba and Kembacoin Developers  
# © 2024 Ha Malak BN Adam Aman RA  

import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.backends import default_backend

def derive_key_from_password(password, salt=None, iterations=100_000, key_length=32):
    """
    Derive a cryptographic key from a password using PBKDF2-HMAC.
    :param password: The password to derive the key from.
    :param salt: Random salt (16 bytes). If None, generates a new salt.
    :param iterations: Number of PBKDF2 iterations (default: 100,000).
    :param key_length: Desired length of the derived key in bytes (default: 32).
    :return: A tuple of (derived_key, salt), both base64-encoded.
    """
    if salt is None:
        salt = os.urandom(16)  # Generate a new random salt

    kdf = PBKDF2HMAC(
        algorithm=SHA256(),
        length=key_length,
        salt=salt,
        iterations=iterations,
        backend=default_backend(),
    )
    key = kdf.derive(password.encode())
    return base64.urlsafe_b64encode(key), base64.urlsafe_b64encode(salt)

