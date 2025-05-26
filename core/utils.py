from cryptography.fernet import Fernet

def get_cipher():
    key = b'your-generated-key'  # Ideally load from env variables
    return Fernet(key)

def encrypt_data(data):
    cipher = get_cipher()
    return cipher.encrypt(data.encode())

def decrypt_data(token):
    cipher = get_cipher()
    return cipher.decrypt(token).decode()
