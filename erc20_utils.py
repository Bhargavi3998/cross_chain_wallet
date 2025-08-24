# erc20_utils.py
import json
from pathlib import Path
from typing import Tuple
from web3 import Web3
from eth_account.account import Account

# Minimal ERC-20 ABI (read + write you actually need)
ERC20_ABI = [
    {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"stateMutability":"view","type":"function"},
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"stateMutability":"view","type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
    {"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"constant":True,"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"constant":False,"inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"constant":False,"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}
]

WATCHLIST_FILE = Path("tokens_watchlist.json")

def load_token(w3: Web3, address: str):
    contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=ERC20_ABI)
    return contract

def token_metadata(contract) -> Tuple[str, str, int]:
    name = contract.functions.name().call()
    symbol = contract.functions.symbol().call()
    decimals = contract.functions.decimals().call()
    return name, symbol, decimals

def human_to_units(amount_str: str, decimals: int) -> int:
    # supports "1.23" etc.
    amt = float(amount_str)
    return int(amt * (10 ** decimals))

def units_to_human(amount_int: int, decimals: int) -> str:
    return f"{amount_int / (10 ** decimals):f}".rstrip("0").rstrip(".")

def balance_of(contract, address: str) -> int:
    return contract.functions.balanceOf(Web3.to_checksum_address(address)).call()

def approve(w3: Web3, acct: Account, contract, spender: str, amount_units: int) -> str:
    fn = contract.functions.approve(Web3.to_checksum_address(spender), amount_units)
    tx = _build_eip1559_tx(w3, acct, to=contract.address, data=fn._encode_transaction_data())
    signed = acct.sign_transaction(tx)
    return w3.eth.send_raw_transaction(signed.rawTransaction).hex()

def transfer(w3: Web3, acct: Account, contract, to: str, amount_units: int) -> str:
    fn = contract.functions.transfer(Web3.to_checksum_address(to), amount_units)
    tx = _build_eip1559_tx(w3, acct, to=contract.address, data=fn._encode_transaction_data())
    signed = acct.sign_transaction(tx)
    return w3.eth.send_raw_transaction(signed.rawTransaction).hex()

def _build_eip1559_tx(w3: Web3, acct: Account, to: str, data: bytes):
    latest = w3.eth.get_block("latest")
    base = latest.get("baseFeePerGas", w3.to_wei(1, "gwei"))
    priority = w3.eth.max_priority_fee
    max_fee = int(base) * 2 + int(priority)

    # Let node estimate gas for safety
    gas_estimate = w3.eth.estimate_gas({
        "from": acct.address,
        "to": to,
        "data": data,
    })

    return {
        "from": acct.address,
        "to": Web3.to_checksum_address(to),
        "data": data,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "chainId": w3.eth.chain_id,
        "type": 2,
        "gas": gas_estimate,
        "maxFeePerGas": int(max_fee),
        "maxPriorityFeePerGas": int(priority),
        # no "value" for ERC-20 transfer/approve
    }

# --- simple watchlist persistence ---
def load_watchlist() -> list:
    if WATCHLIST_FILE.exists():
        return json.loads(WATCHLIST_FILE.read_text())
    return []

def save_watchlist(w: list) -> None:
    WATCHLIST_FILE.write_text(json.dumps(w, indent=2))
def balances_for_watchlist(w3: Web3, owner: str, watchlist: list):
    """
    Returns a list of dicts: [{address, label, symbol, decimals, balance_units, balance_human}, ...]
    Skips tokens that error (bad RPC/ABI) but continues gracefully.
    """
    out = []
    for tok in watchlist:
        try:
            c = load_token(w3, tok["address"])
            name, symbol, decimals = token_metadata(c)
            bal_units = balance_of(c, owner)
            out.append({
                "address": tok["address"],
                "label": tok.get("label") or f"{name} ({symbol})",
                "symbol": symbol,
                "decimals": decimals,
                "balance_units": bal_units,
                "balance_human": units_to_human(bal_units, decimals),
            })
        except Exception:
            # Keep going even if one token fails
            continue
    return out
