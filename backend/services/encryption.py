import os
import base64
from cryptography.fernet import Fernet

_KEY: bytes | None = None


def _get_key() -> bytes:
    global _KEY
    if _KEY is None:
        env_key = os.environ.get("ENCRYPTION_KEY", "")
        if env_key:
            _KEY = env_key.encode()
        else:
            _KEY = Fernet.generate_key()
    return _KEY


def encrypt_password(password: str) -> str:
    f = Fernet(_get_key())
    return f.encrypt(password.encode()).decode()


def decrypt_password(encrypted: str) -> str:
    f = Fernet(_get_key())
    return f.decrypt(encrypted.encode()).decode()
