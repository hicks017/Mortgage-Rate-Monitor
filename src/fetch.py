import requests
from bs4 import BeautifulSoup
import yfinance as yf

def extract_30yr_rate(url):
    """
    Fetches the mortgage rates page and extracts the 30-year fixed rate.
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Error fetching page: {response.status_code}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    for row in soup.find_all("tr"):
        header = row.find("th")
        if header and "30 Yr. Fixed" in header.get_text():
            rate_cell = row.find("td")
            if rate_cell:
                raw_rate = rate_cell.get_text(strip=True)
                try:
                    rate_value = float(raw_rate.replace("%", ""))
                except ValueError:
                    # Return raw value if conversion fails.
                    return raw_rate
                return rate_value
    return None

def get_stock_price(ticker):
    """
    Uses yfinance to fetch the current stock closing price for the given ticker.
    """
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    if not data.empty:
        price = data["Close"].iloc[-1]
        return price
    else:
        # Fallback to currentPrice info if historical data is empty.
        return stock.info.get("currentPrice")

# Created with AI assistance
