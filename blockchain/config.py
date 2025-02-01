# © 2024 The Nation of Tamarikemba and Kembacoin Developers  
# © 2024 Ha Malak BN Adam Aman RA  

# Configuration File for Blockchain Parameters

# Transaction Parameters
DEFAULT_TRANSACTION_FEE_KEM = 0.01  # Default fee in KEM
KEM_TO_KEMITES_RATIO = 10**8  # Conversion ratio from KEM to kemites (1 KEM = 10^8 kemites)

# Proof-of-Work (PoW) Parameters
POW_DIFFICULTY = 4  # Initial mining difficulty (number of leading zeros in the hash)
BLOCK_TIME_SECONDS = 7 * 60  # Target block time in seconds (7 minutes)

# SHA256Lottery Parameters
RANDOM_INTERVALS = [7, 70, 700, 777, 7000]  # Intervals for triggering lottery-based miner rewards
LOTTERY_MINER_SELECTION_SEED = "block_hash"  # Seed for randomness (e.g., hash of a recent block)
LOTTERY_REWARD_KEM = 77  # Reward for the randomly selected miner (in KEM)

# Cryptographic Settings
HASH_ALGORITHM = "SHA256"  # Hashing algorithm used in PoW and transactions

# Logging Configuration
LOGGING_LEVEL = "INFO"  # Log verbosity level

# Key Management (placeholders)
PRIVATE_KEY_PATH = "/path/to/private/key"
PUBLIC_KEY_PATH = "/path/to/public/key"
