import os
import datetime
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import csv

# Data extraction functions ------------------------------------------------------------
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

# Data logging -------------------------------------------------------------------------
def update_csv(filename, data):
    """
    Append a dictionary 'data' as a new row into a CSV file.
    Creates the CSV including headers if not already present.
    """
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())
        # Write header only if the file is new
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

# Execution ----------------------------------------------------------------------------
if __name__ == '__main__':
    # Configuration
    mortgage_url = "https://www.mortgagenewsdaily.com/mortgage-rates/mnd"
    ticker = "MBB"
    csv_filename = "data.csv"
    
    # Get current data
    mortgage_rate = extract_30yr_rate(mortgage_url)
    stock_price = get_stock_price(ticker)
    
    if mortgage_rate is not None:
        print("Current 30-year fixed mortgage rate is:", mortgage_rate, "%")
    else:
        print("Failed to extract the 30-year fixed mortgage rate.")
    
    if stock_price is not None:
        print(f"Current {ticker} stock price is: ${stock_price:.2f}")
    else:
        print(f"Failed to retrieve the current price for {ticker}.")
    
    # Record the current timestamp and update CSV log
    current_time = datetime.datetime.now()
    timestamp_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
    new_row = {
        "timestamp": timestamp_str,
        "mortgage_rate": mortgage_rate,
        "mbb_price": stock_price
    }
    update_csv(csv_filename, new_row)
    print(f"Data appended to '{csv_filename}'.")
