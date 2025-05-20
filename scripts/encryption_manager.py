from cryptography.fernet import Fernet
import os
from config import ENCRYPTION_KEY_PATH

# Location of the encryption key
KEY_FILE = ENCRYPTION_KEY_PATH

# This script handles the generation, loading, encryption, and decryption of files using a symmetric encryption key.
# It uses the Fernet symmetric encryption algorithm from the cryptography library.

def generate_key(): # Generate a new encryption key
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True) # Ensure the directory exists

    if not os.path.exists(KEY_FILE): # Check if the key file already exists
        print("🔑 Generating a new secret key...")
        key = Fernet.generate_key() # Generate a new key

        with open(KEY_FILE, 'wb') as f: # Open the key file in write-binary mode
            f.write(key) # Write the key to the file

        print("✅ Secret key generated and stored.")

    else: # If the key file already exists
        print("🔑 Secret key already exists.")

def load_key(): # Load the encryption key from the file
    if not os.path.exists(KEY_FILE): # Check if the key file exists
        raise FileNotFoundError("Secret key not found. Run generate_key() first.")

    return open(KEY_FILE, 'rb').read() # Read the key from the file

def encrypt_file(input_file, output_file): # Encrypt a file using the global key
    key = load_key() # Load the encryption key
    fernet = Fernet(key) # Create a Fernet object with the key

    with open(input_file, 'rb') as file: # Open the input file in read-binary mode
        original = file.read()

    encrypted = fernet.encrypt(original) # Encrypt the original file content

    with open(output_file, 'wb') as file: # Open the output file in write-binary mode
        file.write(encrypted)

def decrypt_file(input_file, output_file): # Decrypt a file using the global key
    key = load_key() # Load the encryption key
    fernet = Fernet(key) # Create a Fernet object with the key

    with open(input_file, 'rb') as file: # Open the input file in read-binary mode
        encrypted = file.read()

    decrypted = fernet.decrypt(encrypted) # Decrypt the encrypted file content

    with open(output_file, 'wb') as file: # Open the output file in write-binary mode
        file.write(decrypted)
