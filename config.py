import os
from dotenv import load_dotenv

# Load variables from .env into environment
load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

if not API_KEY or not API_SECRET:
    raise ValueError("Please set BINANCE_API_KEY and BINANCE_API_SECRET in your .env file")

# Binance Futures Testnet base URL
BASE_URL = "https://testnet.binancefuture.com"
