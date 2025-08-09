from bip_utils import Bip44, Bip44Coins
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.transaction import safe_sign_and_submit_transaction
from xrpl.wallet import Wallet

client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

def derive_xrp_wallet(seed):
    bip44_xrp = Bip44.FromSeed(seed, Bip44Coins.RIPPLE).DeriveDefaultPath()
    private_key = bip44_xrp.PrivateKey().Raw().ToHex()
    public_key = bip44_xrp.PublicKey().RawCompressed().ToHex()
    return Wallet(seed=private_key, sequence=0)

def send_xrp(wallet, to_address, amount_xrp):
    payment = Payment(
        account=wallet.classic_address,
        destination=to_address,
        amount=str(int(float(amount_xrp) * 1_000_000))
    )
    tx_response = safe_sign_and_submit_transaction(payment, wallet, client)
    return tx_response.result["hash"]