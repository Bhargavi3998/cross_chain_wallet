# 🪙 Cross-Chain Wallet (Ethereum + XRP) — Streamlit App

## 📌 Overview
This is a **non-custodial cross-chain wallet** built with **Python** and **Streamlit**, supporting:
- 🔐 Wallet generation from a **BIP-39 mnemonic**
- 🦄 **Ethereum (ETH)** wallet creation and transactions (Goerli/Sepolia testnet)
- 🌊 **XRP** wallet creation and transactions (XRPL testnet)
- 📥 Keystore JSON download
- 📷 QR code for easy address sharing

---

## ✨ Features

### 1. Wallet Generator
- Generate a 12-word mnemonic (BIP-39)
- Derive Ethereum & XRP wallets from the same seed
- Display addresses and optionally reveal ETH private key
- Download keystore JSON (address + mnemonic)
- QR code for ETH address

### 2. Load Existing Wallet
- Restore ETH & XRP wallets from an existing mnemonic

### 3. Send Transaction
- Send ETH (via Infura) to another ETH address
- Send XRP to another XRP address
- View transaction hash with a link to the explorer

---

## 🛠 Tech Stack
- **Streamlit** — UI framework
- **web3.py** — Ethereum blockchain interactions
- **xrpl-py** — XRP Ledger interactions
- **bip-utils** — Mnemonic & HD wallet derivations
- **qrcode** — Generate QR codes for addresses
- **python-dotenv** — Manage environment variables

---

## 📂 Project Structure

```
cross_chain_wallet/
│
├── main.py          # Streamlit app entry point
├── utils.py         # Mnemonic generation & seed functions
├── eth_wallet.py    # Ethereum wallet derivation & transaction functions
├── xrp_wallet.py    # XRP wallet derivation & transaction functions
├── requirements.txt # Dependencies
└── .env.example     # Environment variable template
```

---

## ⚙️ Installation

1️⃣ **Clone the repository**  
```bash
git clone https://github.com/<your-username>/cross_chain_wallet.git
cd cross_chain_wallet
```

2️⃣ **Create a virtual environment & install dependencies**  
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3️⃣ **Set up environment variables**  
Create a `.env` file:
```
INFURA_API_KEY=your_infura_project_id
ETH_NETWORK=goerli      # or sepolia
XRPL_NETWORK=testnet    # or devnet
```

4️⃣ **Run the app**  
```bash
streamlit run main.py
```

---

## 🚀 Usage

### Generate Wallet
1. Click **🔄 Generate New Wallet**
2. Save the mnemonic safely
3. View ETH & XRP addresses
4. Download keystore JSON and/or scan the QR code

### Load Existing Wallet
1. Paste your 12-word mnemonic
2. Click **🔐 Load Wallet**

### Send Transaction
1. Select chain (**Ethereum** or **XRP**)
2. Enter recipient address & amount
3. Click **🚀 Send Transaction**
4. View transaction hash & explorer link

---

## 🔗 Testnet Faucets
- **Goerli ETH**: https://goerlifaucet.com/
- **Sepolia ETH**: https://sepoliafaucet.com/
- **XRP Testnet**: https://xrpl.org/xrp-testnet-faucet.html

---

## 🔒 Security Notes
- Keys are stored in Streamlit session for demo purposes only
- In production:
  - Use encrypted keystores (PBKDF2/scrypt + AES-GCM)
  - Never expose private keys
  - Integrate with hardware wallets
  - Validate addresses and sanitize inputs

---

## 📜 License
MIT License
