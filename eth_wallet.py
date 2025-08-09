from bip_utils import Bip44, Bip44Coins
from web3 import Web3
from eth_account import Account
import os

INFURA_URL = f"https://goerli.infura.io/v3/{os.getenv('INFURA_API_KEY')}"
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

def derive_eth_wallet(seed):
    bip44_eth = Bip44.FromSeed(seed, Bip44Coins.ETHEREUM).DeriveDefaultPath()
    private_key = bip44_eth.PrivateKey().Raw().ToHex()
    acct = Account.from_key(private_key)
    return acct

def send_eth_transaction(wallet, to_address, amount_eth):
    tx = {
        'to': to_address,
        'value': w3.to_wei(amount_eth, 'ether'),
        'gas': 21000,
        'maxFeePerGas': w3.to_wei(2, 'gwei'),
        'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
        'nonce': w3.eth.get_transaction_count(wallet.address),
        'chainId': 5
    }
    signed_tx = wallet.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash.hex()