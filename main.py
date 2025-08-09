import streamlit as st
from dotenv import load_dotenv
from utils import generate_mnemonic, get_seed
from eth_wallet import derive_eth_wallet, send_eth_transaction
from xrp_wallet import derive_xrp_wallet, send_xrp

load_dotenv()

st.title("🪙 Cross-Chain Wallet: ETH + XRP")

tab1, tab2 = st.tabs(["🔐 Generate Wallet", "💸 Send Transaction"])

with tab1:
    if st.button("Generate New Mnemonic"):
        mnemonic = generate_mnemonic()
        st.session_state['mnemonic'] = mnemonic
        st.success("Mnemonic Generated!")
        st.code(mnemonic, language='text')

    if 'mnemonic' in st.session_state:
        seed = get_seed(st.session_state['mnemonic'])
        eth_wallet = derive_eth_wallet(seed)
        xrp_wallet = derive_xrp_wallet(seed)

        st.write("🦄 ETH Address:", eth_wallet.address)
        st.write("🌊 XRP Address:", xrp_wallet.classic_address)

with tab2:
    chain = st.selectbox("Choose Chain", ["Ethereum", "XRP"])
    to_address = st.text_input("Recipient Address")
    amount = st.text_input("Amount to Send")

    if st.button("Send Transaction"):
        seed = get_seed(st.session_state['mnemonic'])
        if chain == "Ethereum":
            eth_wallet = derive_eth_wallet(seed)
            tx_hash = send_eth_transaction(eth_wallet, to_address, amount)
            st.success(f"ETH TX sent! Hash: {tx_hash}")
        elif chain == "XRP":
            xrp_wallet = derive_xrp_wallet(seed)
            tx_hash = send_xrp(xrp_wallet, to_address, amount)
            st.success(f"XRP TX sent! Hash: {tx_hash}")