# price_utils.py
import os
import requests

CMC_API_KEY = os.getenv("CMC_API_KEY")  # optional for higher rate limits

def get_eth_price_usd() -> float | None:
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {"symbol": "ETH", "convert": "USD"}
    headers = {"Accepts": "application/json"}
    if CMC_API_KEY:
        headers["X-CMC_PRO_API_KEY"] = CMC_API_KEY

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return float(data["data"]["ETH"]["quote"]["USD"]["price"])
    except Exception:
        return None
