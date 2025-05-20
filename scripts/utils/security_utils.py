import hashlib

def hash_password(password: str) -> str:
    # This function hashes a password using SHA-256.
    # It returns the hashed password as a hexadecimal string.
    return hashlib.sha256(password.encode()).hexdigest()