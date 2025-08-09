from mnemonic import Mnemonic
from bip_utils import Bip39SeedGenerator

def generate_mnemonic():
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=128)

def get_seed(mnemonic):
    return Bip39SeedGenerator(mnemonic).Generate()