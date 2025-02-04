import os
import hashlib
import hmac
from mnemonic import Mnemonic


class MnemonicHelper:
    def __init__(self, language="english"):
        """
        Initialize the mnemonic helper.
        :param language: Language for the mnemonic wordlist.
        """
        self.mnemonic = Mnemonic(language)

    def generate_mnemonic(self, strength=128):
        """
        Generate a new 12-word mnemonic phrase.
        :param strength: Entropy strength (128 bits = 12 words, 256 bits = 24 words).
        :return: A mnemonic phrase.
        """
        return self.mnemonic.generate(strength=strength)

    def validate_mnemonic(self, mnemonic_phrase):
        """
        Validate a given mnemonic phrase.
        :param mnemonic_phrase: The mnemonic phrase to validate.
        :return: True if valid, False otherwise.
        """
        return self.mnemonic.check(mnemonic_phrase)

    def mnemonic_to_seed(self, mnemonic_phrase, passphrase=""):
        """
        Convert a mnemonic phrase to a seed.
        :param mnemonic_phrase: The mnemonic phrase.
        :param passphrase: An optional passphrase for added security.
        :return: The derived seed.
        """
        return self.mnemonic.to_seed(mnemonic_phrase, passphrase=passphrase)

    def mnemonic_to_entropy(self, mnemonic_phrase):
        """
        Convert a mnemonic phrase to entropy.
        :param mnemonic_phrase: The mnemonic phrase.
        :return: The entropy as a hex string.
        """
        return self.mnemonic.to_entropy(mnemonic_phrase).hex()

