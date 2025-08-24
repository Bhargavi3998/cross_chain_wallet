# main.py
import json
import requests
import streamlit as st
from dotenv import load_dotenv
from keystore import has_keystore, save_keystore, load_keystore, KEYSTORE_PATH
from keystore import has_keystore, save_keystore, load_keystore, KEYSTORE_PATH

# ETH / XRPL utils from your project
from utils import generate_mnemonic, get_seed
from eth_wallet import derive_eth_wallet, send_eth_transaction, get_web3
from xrp_wallet import derive_xrp_wallet, send_xrp, get_xrp_client

from web3 import Web3
from xrpl.models.requests import AccountInfo

# ---------------------------------------------------------------------
# Boot
# ---------------------------------------------------------------------
load_dotenv()
st.set_page_config(page_title="Cross-Chain Wallet: ETH + XRP", page_icon="🪙", layout="centered")
st.title("🪙 Cross-Chain Wallet: ETH + XRP")
# --- Unlock existing wallet ---
# ---- Landing gate: shown when no wallet is active ----
def landing_gate():
    st.subheader("Open your wallet")

    c1, c2, c3 = st.columns(3)

    # 1) Unlock existing keystore.json (password)
    with c1:
        st.markdown("### 🔐 Unlock keystore")
        if has_keystore():
            pw = st.text_input("Password", type="password", key="unlock_pw")
            if st.button("Unlock", key="unlock_btn"):
                if not pw:
                    st.warning("Enter password.")
                else:
                    try:
                        mnemonic = load_keystore(pw)
                        st.session_state["mnemonic"] = mnemonic
                        st.success("Wallet unlocked!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to unlock: {e}")
        else:
            st.info("No keystore.json found. Create or import first.")

    # 2) Import an existing mnemonic (optionally save keystore)
    with c2:
        st.markdown("### 📥 Import mnemonic")
        words = st.text_area("Enter your 12/24-word seed phrase",
                             placeholder="word1 word2 word3 ...",
                             height=100, key="import_mnemonic")
        pw_save = st.text_input("Set password (optional to save keystore)", type="password", key="import_pw")
        if st.button("Import", key="import_btn"):
            phrase = " ".join(words.strip().split())
            wc = len(phrase.split())
            if wc not in (12, 15, 18, 21, 24):
                st.error("Seed phrase should be 12/15/18/21/24 words.")
            else:
                st.session_state["mnemonic"] = phrase
                if pw_save:
                    try:
                        save_keystore(phrase, pw_save)
                        st.success("Imported and saved to keystore.json.")
                    except Exception as e:
                        st.warning(f"Imported. Keystore save failed: {e}")
                else:
                    st.info("Imported without saving keystore. You can save later on the Generate tab.")
                st.rerun()

    # 3) Create a brand-new wallet
    with c3:
        st.markdown("### ✨ Create new")
        if st.button("Generate new mnemonic", key="create_new"):
            mnemonic = generate_mnemonic()
            st.session_state["mnemonic"] = mnemonic
            st.success("New wallet created!")
            st.rerun()

# If there is no active wallet in session, show the gate and stop the rest of the app.
if "mnemonic" not in st.session_state:
    landing_gate()
    st.stop()

if "mnemonic" not in st.session_state and has_keystore():
    with st.expander("🔐 Unlock existing wallet", expanded=True):
        st.caption(f"Found keystore file: `{KEYSTORE_PATH}`")
        pw = st.text_input("Password", type="password")
        colU1, colU2 = st.columns([1,4])
        with colU1:
            if st.button("Unlock"):
                if not pw:
                    st.warning("Enter password.")
                else:
                    try:
                        mnemonic = load_keystore(pw)
                        st.session_state["mnemonic"] = mnemonic
                        st.success("Wallet unlocked!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to unlock: {e}")

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _require_mnemonic():
    if "mnemonic" not in st.session_state:
        st.error("Generate a mnemonic first (on the **Generate Wallet** tab).")
        return False
    return True

def _parse_amount(s: str):
    try:
        val = float(s)
        if val <= 0:
            return None
        return val
    except Exception:
        return None

def _valid_eth_address(addr: str) -> bool:
    return Web3.is_address(addr)

def get_live_prices() -> dict:
    """
    Fetch live USD prices for ETH and XRP (mainnet pricing) from CoinGecko (no API key).
    Returns: {"ETH": float|None, "XRP": float|None}
    """
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "ethereum,ripple", "vs_currencies": "usd"}
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        eth = float(data.get("ethereum", {}).get("usd")) if data.get("ethereum") else None
        xrp = float(data.get("ripple", {}).get("usd")) if data.get("ripple") else None
        return {"ETH": eth, "XRP": xrp}
    except Exception:
        return {"ETH": None, "XRP": None}

def etherscan_address_url(addr: str, network: str = "sepolia") -> str:
    base = {
        "sepolia": "https://sepolia.etherscan.io/address",
        "goerli": "https://goerli.etherscan.io/address",
        "mainnet": "https://etherscan.io/address",
    }.get(network, "https://sepolia.etherscan.io/address")
    return f"{base}/{addr}"

def xrpl_account_url(addr: str, net: str = "testnet") -> str:
    base = {
        "testnet": "https://testnet.xrpl.org/accounts",
        "devnet": "https://devnet.xrpl.org/accounts",
        "mainnet": "https://livenet.xrpl.org/accounts",
    }.get(net, "https://testnet.xrpl.org/accounts")
    return f"{base}/{addr}"

def safe_eth_balance(w3: Web3, address: str):
    """
    Returns (connected: bool, eth_balance: float).
    If not connected, balance will be 0.0.
    """
    try:
        if not w3.is_connected():
            return (False, 0.0)
        wei = w3.eth.get_balance(Web3.to_checksum_address(address))
        return (True, float(w3.from_wei(wei, "ether")))
    except Exception:
        return (False, 0.0)

def safe_xrp_balance(xrpl_client, classic_address: str):
    """
    Returns (funded: bool, xrp_balance: float).
    If account is unfunded (actNotFound / no account_data), returns (False, 0.0).
    """
    try:
        info = xrpl_client.request(AccountInfo(
            account=classic_address,
            ledger_index="validated",
            strict=True
        ))
        data = info.result.get("account_data")
        if not data:
            return (False, 0.0)
        drops = int(data["Balance"])
        return (True, drops / 1_000_000)
    except Exception:
        # Treat any error as “not funded yet” rather than crashing
        return (False, 0.0)
def fund_test_accounts_panel(eth_address: str, xrp_address: str):
    with st.expander("💧 Fund Test Accounts (free faucets)"):
        st.markdown("Use these faucets to get **test coins** (no real value).")

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**Ethereum — Sepolia**")
            st.caption("Your ETH address")
            st.code(eth_address, language="text")
            st.link_button("Infura Faucet (Sepolia)", "https://www.infura.io/faucet")
            st.caption("Sign in with Infura, paste your Sepolia address, request ETH. Wait ~1 min then click **Refresh** above.")

        with c2:
            st.markdown("**XRP Ledger — Testnet**")
            st.caption("Your XRP classic address")
            st.code(xrp_address, language="text")
            st.link_button("XRPL Testnet Faucet", "https://xrpl.org/xrp-testnet-faucet.html")
            st.caption("Paste your XRP address, click *Get Test XRP*. Wait a few seconds then click **Refresh** above.")
def copy_line(label: str, value: str, key: str):
    # Lightweight HTML/JS copy-to-clipboard row
    st.markdown(
        f"""
        <div style="margin:4px 0 12px 0;">
          <div style="font-weight:600; margin-bottom:4px;">{label}</div>
          <div style="display:flex; gap:8px; align-items:center;">
            <input id="inp-{key}" type="text" value="{value}" readonly
                   style="flex:1; padding:6px 8px; border:1px solid #ddd; border-radius:8px; background:#f8f9fa;"/>
            <button onclick="navigator.clipboard.writeText(document.getElementById('inp-{key}').value)"
                    style="padding:6px 10px; border:1px solid #ddd; border-radius:8px; background:#eee; cursor:pointer;">
              Copy
            </button>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------
tab1, tab2, tab_bal = st.tabs(["🔐 Generate Wallet", "💸 Send Transaction", "📊 Balances"])

# ---------------------------------------------------------------------
# Tab 1: Generate Wallet
# ---------------------------------------------------------------------
with tab1:
    st.caption("Create a 12-word seed phrase and derive ETH & XRP addresses (testnets).")
    if st.button("Generate New Mnemonic"):
        mnemonic = generate_mnemonic()
        st.session_state["mnemonic"] = mnemonic
        st.success("Mnemonic Generated!")
        st.code(mnemonic, language="text")
        # Offer to save encrypted keystore
        # with st.form("save_ks_form", clear_on_submit=False):
        #     st.caption("Optional: protect & reuse this wallet later")
        #     pw1 = st.text_input("Create password", type="password")
        #     pw2 = st.text_input("Confirm password", type="password")
        #     save_pressed = st.form_submit_button("💾 Save encrypted keystore")
        #     if save_pressed:
        #         if not pw1 or pw1 != pw2:
        #             st.error("Passwords must match and not be empty.")
        #         else:
        #             try:
        #                 path = save_keystore(st.session_state["mnemonic"], pw1)
        #                 st.success(f"Saved keystore to {path}. Next time, open app and click **Unlock**.")
        #             except Exception as e:
        #                 st.error(f"Save failed: {e}")
        # # After st.code(mnemonic, language="text")
        with st.form("save_ks_form", clear_on_submit=False):
            st.caption("Optional: protect & reuse this wallet later")
            pw1 = st.text_input("Create password", type="password")
            pw2 = st.text_input("Confirm password", type="password")
            save_pressed = st.form_submit_button("💾 Save encrypted keystore")
            if save_pressed:
                if not pw1 or pw1 != pw2:
                    st.error("Passwords must match and not be empty.")
                else:
                    try:
                        path = save_keystore(st.session_state["mnemonic"], pw1)
                        st.success(f"Saved keystore to {path}. Next time, just click **Unlock** on the home screen.")
                    except Exception as e:
                        st.error(f"Save failed: {e}")


    if "mnemonic" in st.session_state:
        seed = get_seed(st.session_state["mnemonic"])
        eth_wallet = derive_eth_wallet(seed)
        xrp_wallet = derive_xrp_wallet(seed)

                
        # st.write("🦄 **ETH Address:**", eth_wallet.address)
        # st.write("🌊 **XRP Address:**", xrp_wallet.classic_address)

        copy_line("🦄 ETH Address", eth_wallet.address, key="eth_addr_main")
        copy_line("🌊 XRP Address", xrp_wallet.classic_address, key="xrp_addr_main")


# ---------------------------------------------------------------------
# Tab 2: Send Transaction
# ---------------------------------------------------------------------
with tab2:
    st.caption("Send test transactions on Ethereum (Sepolia/custom) or XRPL Testnet.")
    chain = st.selectbox("Choose Chain", ["Ethereum", "XRP"])
    to_address = st.text_input("Recipient Address")
    amount = st.text_input("Amount to Send")

    if st.button("Send Transaction"):
        if not _require_mnemonic():
            st.stop()

        amt = _parse_amount(amount)
        if amt is None:
            st.error("Enter a valid positive amount.")
            st.stop()

        seed = get_seed(st.session_state["mnemonic"])

        try:
            if chain == "Ethereum":
                if not _valid_eth_address(to_address):
                    st.error("Invalid Ethereum address.")
                    st.stop()
                eth_wallet = derive_eth_wallet(seed)
                tx_hash = send_eth_transaction(eth_wallet, to_address, amt)
                url = etherscan_address_url(eth_wallet.address)  # sender account link
                st.success(f"ETH TX sent! Hash: {tx_hash}")
                st.markdown(f"[View your account on Etherscan]({url})")

            elif chain == "XRP":
                if not to_address:
                    st.error("Enter a destination address.")
                    st.stop()
                xrp_wallet = derive_xrp_wallet(seed)
                tx_hash = send_xrp(xrp_wallet, to_address, amt)
                url = xrpl_account_url(xrp_wallet.classic_address)
                st.success(f"XRP TX sent! Hash: {tx_hash}")
                st.markdown(f"[View your account on XRPL Explorer]({url})")

        except Exception as e:
            st.error(f"Transaction failed: {e}")

# ---------------------------------------------------------------------
# Tab 3: Balances (with Refresh, explorer links, and live USD)
# ---------------------------------------------------------------------
with tab_bal:
    st.subheader("📊 Balances")

    # Refresh button
    cols = st.columns([1, 6])
    with cols[0]:
        if st.button("🔄 Refresh"):
            st.rerun()

    if not _require_mnemonic():
        st.stop()

    # Derive & clients
    seed = get_seed(st.session_state["mnemonic"])
    w3 = get_web3()
    eth_acct = derive_eth_wallet(seed)
    xrpl_client = get_xrp_client()
    xrp_wallet = derive_xrp_wallet(seed)

    # Fetch prices once (live)
    prices = get_live_prices()  # {"ETH": float|None, "XRP": float|None}

    col1, col2 = st.columns(2)

    # --- Ethereum native balance (graceful when disconnected) ---
    with col1:
        st.markdown("**Ethereum (Sepolia/custom)**")
        connected, eth_bal = safe_eth_balance(w3, eth_acct.address)
        st.metric(label="ETH Balance", value=f"{eth_bal:.6f} ETH")
        if prices["ETH"] is not None:
            st.caption(f"≈ ${(eth_bal * prices['ETH']):,.2f} (1 ETH ≈ ${prices['ETH']:.2f})")
        else:
            st.caption("Live ETH price unavailable.")
        st.markdown(f"[View on Etherscan]({etherscan_address_url(eth_acct.address, 'sepolia')})")
        st.caption(f"Address: {eth_acct.address}")
        if not connected:
            st.info("Not connected to Ethereum RPC yet — showing 0. Fund with Sepolia ETH or set a working RPC.")

    # --- XRP native balance (graceful when unfunded) ---
    with col2:
        st.markdown("**XRP Ledger (Testnet)**")
        funded, xrp_bal = safe_xrp_balance(xrpl_client, xrp_wallet.classic_address)
        st.metric(label="XRP Balance", value=f"{xrp_bal:.6f} XRP")
        if prices["XRP"] is not None:
            st.caption(f"≈ ${(xrp_bal * prices['XRP']):,.2f} (1 XRP ≈ ${prices['XRP']:.4f})")
        else:
            st.caption("Live XRP price unavailable.")
        st.markdown(f"[View on XRPL Explorer]({xrpl_account_url(xrp_wallet.classic_address, 'testnet')})")
        st.caption(f"Address: {xrp_wallet.classic_address}")
        if not funded:
            st.info("Account not funded on XRPL Testnet — showing 0. Use the XRPL Testnet faucet to fund it.")
    # Show funding panel
    fund_test_accounts_panel(eth_acct.address, xrp_wallet.classic_address)
