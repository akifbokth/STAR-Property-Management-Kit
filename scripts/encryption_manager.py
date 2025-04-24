from cryptography.fernet import Fernet
import os
from config import ENCRYPTION_KEY_PATH

# Location of the encryption key
KEY_FILE = ENCRYPTION_KEY_PATH


def generate_key():
    """
    Generate the encryption key if it doesn't exist.
    """
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)

    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()

        with open(KEY_FILE, 'wb') as f:
            f.write(key)

        print("✅ Secret key generated and stored.")
    else:
        print("🔑 Secret key already exists.")

def load_key():
    """
    Load the existing encryption key.
    """
    if not os.path.exists(KEY_FILE):
        raise FileNotFoundError("Secret key not found. Run generate_key() first.")

    return open(KEY_FILE, 'rb').read()

def encrypt_file(input_file, output_file):
    """
    Encrypt a file with the global key.
    """
    key = load_key()
    fernet = Fernet(key)

    with open(input_file, 'rb') as file:
        original = file.read()

    encrypted = fernet.encrypt(original)

    with open(output_file, 'wb') as file:
        file.write(encrypted)

def decrypt_file(input_file, output_file):
    """
    Decrypt an encrypted file with the global key.
    """
    key = load_key()
    fernet = Fernet(key)

    with open(input_file, 'rb') as file:
        encrypted = file.read()

    decrypted = fernet.decrypt(encrypted)

    with open(output_file, 'wb') as file:
        file.write(decrypted)
