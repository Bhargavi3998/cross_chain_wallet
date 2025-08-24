# xrp_wallet.py
from bip_utils import Bip44, Bip44Coins
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.transaction import autofill, sign, submit
from xrpl.models.requests import Tx
from xrpl.wallet import Wallet
import os, time
from xrpl.core.keypairs import generate_seed, derive_keypair
import hashlib


# --- Network config ---
XRPL_NETWORK = (os.getenv("XRPL_NETWORK") or "testnet").lower()
XRPL_RPC_MAP = {
    "testnet": "https://s.altnet.rippletest.net:51234",
    "devnet":  "https://s.devnet.rippletest.net:51234",
    "mainnet": "https://xrplcluster.com",
}
XRPL_RPC_URL = XRPL_RPC_MAP.get(XRPL_NETWORK, XRPL_RPC_MAP["testnet"])
client = JsonRpcClient(XRPL_RPC_URL)

def derive_xrp_wallet(seed: bytes) -> Wallet:
    """
    Deterministically derive an XRPL wallet from BIP-39 seed.
    Steps:
      1) BIP44 derive Ripple node -> 32B privkey
      2) Compress to 16B entropy (SHA-256 -> first 16B)
      3) Make XRPL family seed (s...)
      4) Derive XRPL keypair from the family seed
      5) Construct Wallet with explicit keys (matches your xrpl-py build)
    """
    bip44_xrp = Bip44.FromSeed(seed, Bip44Coins.RIPPLE).DeriveDefaultPath()
    priv_hex = bip44_xrp.PrivateKey().Raw().ToHex()           # 32-byte hex
    priv_bytes = bytes.fromhex(priv_hex)

    # 16-byte deterministic entropy → family seed (s…)
    import hashlib
    entropy16 = hashlib.sha256(priv_bytes).digest()[:16]
    family_seed = generate_seed(entropy16.hex())

    # Derive XRPL keypair from the family seed
    public_key, private_key = derive_keypair(family_seed)

    # Your xrpl-py requires explicit keys in the constructor
    return Wallet(seed=family_seed, public_key=public_key, private_key=private_key)

def _submit_and_wait(tx_blob: str, tx_hash: str, wait_s: float = 2.0, attempts: int = 10) -> None:
    submit(tx_blob, client)  # broadcast
    for _ in range(attempts):
        try:
            resp = client.request(Tx(transaction=tx_hash))
            if resp.result.get("validated"):
                return
        except Exception:
            pass
        time.sleep(wait_s)

def send_xrp(wallet: Wallet, to_address: str, amount_xrp: float) -> str:
    drops = str(int(float(amount_xrp) * 1_000_000))  # 1 XRP = 1,000,000 drops
    # 1) build & autofill (fees, sequence, etc.)
    tx = Payment(account=wallet.classic_address, destination=to_address, amount=drops)
    tx = autofill(tx, client)
    # 2) sign
    signed = sign(tx, wallet)  # -> {"tx_blob": "...", "tx_json": {..., "hash": "..."}}
    tx_blob = signed["tx_blob"]
    tx_hash = signed["tx_json"].get("hash")
    # 3) submit + poll to validated
    if tx_hash:
        _submit_and_wait(tx_blob, tx_hash)
        return tx_hash
    # Edge case: very old builds lacking hash in tx_json
    submit(tx_blob, client)
    return "(hash unavailable in this xrpl-py build)"
def get_xrp_client():
    return client

