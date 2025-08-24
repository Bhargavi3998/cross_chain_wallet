# keystore.py
import json, os, secrets, base64
from hashlib import scrypt
from Crypto.Cipher import AES  # from pycryptodome

HERE = os.path.dirname(__file__)
KEYSTORE_PATH = os.path.join(HERE, "keystore.json")

def _kdf(password: str, salt: bytes, n=2**15, r=8, p=1, dklen=32) -> bytes:
    return scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=dklen)

def encrypt_mnemonic(mnemonic: str, password: str) -> dict:
    salt = secrets.token_bytes(16)
    key = _kdf(password, salt)
    nonce = secrets.token_bytes(12)  # AES-GCM nonce
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ct, tag = cipher.encrypt_and_digest(mnemonic.encode("utf-8"))
    return {
        "version": 1,
        "kdf": {"name":"scrypt","n":2**15,"r":8,"p":1,"dklen":32,"salt": base64.b64encode(salt).decode()},
        "cipher": {"name":"AES-GCM","nonce": base64.b64encode(nonce).decode()},
        "ciphertext": base64.b64encode(ct).decode(),
        "tag": base64.b64encode(tag).decode(),
    }

def decrypt_keystore(obj: dict, password: str) -> str:
    if obj.get("version") != 1 or obj.get("kdf", {}).get("name") != "scrypt":
        raise ValueError("Unsupported keystore format.")
    kdf = obj["kdf"]
    salt = base64.b64decode(kdf["salt"])
    key = _kdf(password, salt, n=kdf["n"], r=kdf["r"], p=kdf["p"], dklen=kdf["dklen"])
    nonce = base64.b64decode(obj["cipher"]["nonce"])
    ct = base64.b64decode(obj["ciphertext"])
    tag = base64.b64decode(obj["tag"])
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ct, tag).decode("utf-8")

def save_keystore(mnemonic: str, password: str, path: str = KEYSTORE_PATH) -> str:
    data = encrypt_mnemonic(mnemonic, password)
    with open(path, "w") as f:
        json.dump(data, f)
    return path

def load_keystore(password: str, path: str = KEYSTORE_PATH) -> str:
    with open(path, "r") as f:
        obj = json.load(f)
    return decrypt_keystore(obj, password)

def has_keystore(path: str = KEYSTORE_PATH) -> bool:
    return os.path.exists(path)
