import time
import hmac
import hashlib
import requests
import logging

from urllib.parse import urlencode
from config import API_KEY, API_SECRET, BASE_URL
from logger import setup_logger

class BasicBot:
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.logger = setup_logger()
        self.logger.info("BasicBot initialized")

    def _sign(self, params: dict) -> str:
        """Create HMAC SHA256 signature."""
        query = urlencode(params)
        return hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()

    def _post(self, path: str, params: dict) -> dict:
        """Send signed POST request to Binance Futures Testnet."""
        params['timestamp'] = int(time.time() * 1000)
        params['signature'] = self._sign(params)
        url = f"{self.base_url}{path}"
        headers = {"X-MBX-APIKEY": self.api_key}

        self.logger.info(f"POST {url} – params: {params}")
        try:
            r = requests.post(url, params=params, headers=headers, timeout=10)
            data = r.json()
            if r.status_code != 200:
                self.logger.error(f"Error response: {data}")
            else:
                self.logger.info(f"Success response: {data}")
            return data
        except requests.RequestException as e:
            self.logger.exception("HTTP request failed")
            return {"error": str(e)}

    def _get(self, path: str, params: dict = None) -> dict:
        """Send signed GET request to Binance Futures Testnet."""
        if params is None:
            params = {}
        params['timestamp'] = int(time.time() * 1000)
        params['signature'] = self._sign(params)
        url = f"{self.base_url}{path}"
        headers = {"X-MBX-APIKEY": self.api_key}

        self.logger.info(f"GET {url} – params: {params}")
        try:
            r = requests.get(url, params=params, headers=headers, timeout=10)
            data = r.json()
            if r.status_code != 200:
                self.logger.error(f"Error response: {data}")
            else:
                self.logger.info(f"Success response: {data}")
            return data
        except requests.RequestException as e:
            self.logger.exception("HTTP GET failed")
            return {"error": str(e)}

    def get_balance(self, asset: str = "USDT") -> float:
        """
        Fetch futures account balances and return the free balance of the given asset.
        """
        data = self._get("/fapi/v2/balance")
        for entry in data:
            if entry.get('asset') == asset:
                free = float(entry.get('withdrawAvailable', 0))
                self.logger.info(f"{asset} balance: {free}")
                return free
        self.logger.error(f"{asset} not found in balance response")
        return 0.0

    def place_order(self, symbol: str, side: str, order_type: str,
                    quantity: float, price: float = None, stop_price: float = None) -> dict:
        """
        Place MARKET, LIMIT or STOP (stop-limit) orders.
        - MARKET: needs quantity
        - LIMIT: needs quantity + price
        - STOP:  needs quantity + stopPrice + price
        """
        path = "/fapi/v1/order"
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity
        }

        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = "GTC"
        if order_type == "STOP":
            params["stopPrice"] = stop_price
            params["price"]     = price
            params["timeInForce"] = "GTC"

        return self._post(path, params)

    def menu(self):
        """Interactive CLI menu loop."""
        MENU = """
Select an action:
  1) Show USDT Balance
  2) Place MARKET order
  3) Place LIMIT order
  4) Place STOP-LIMIT order
  5) Exit
> """
        while True:
            choice = input(MENU).strip()

            if choice == "5":
                print("Goodbye!")
                break

            if choice == "1":
                balance = self.get_balance("USDT")
                print(f"Your USDT balance: {balance}")
                continue

            # For order options, always show balance first
            balance = self.get_balance("USDT")
            print(f"Your USDT balance: {balance}")

            symbol = input("Symbol (e.g. BTCUSDT): ").strip().upper()
            side   = input("Side (BUY/SELL): ").strip().upper()
            qty    = float(input("Quantity: ").strip())

            if choice == "2":
                data = self.place_order(symbol, side, "MARKET", qty)

            elif choice == "3":
                price = float(input("Limit price: ").strip())
                data  = self.place_order(symbol, side, "LIMIT", qty, price=price)

            elif choice == "4":
                stop_price = float(input("Stop trigger price: ").strip())
                price      = float(input("Limit price: ").strip())
                data       = self.place_order(symbol, side, "STOP", qty,
                                              price=price, stop_price=stop_price)
            else:
                print("Invalid choice.")
                continue

            print("Order response:", data)

if __name__ == "__main__":
    bot = BasicBot(API_KEY, API_SECRET, BASE_URL)
    bot.menu()
