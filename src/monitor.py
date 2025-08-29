import os
import datetime
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import sqlite3
import psycopg

# Configuration ------------------------------------------------------------------------
mortgage_url = "https://www.mortgagenewsdaily.com/mortgage-rates/mnd"
ticker = "MBB"
SQLITE_FILE = "data.sqlite3"
TABLE_NAME  = "rates_mbb"
POSTGRES_VARS = {
    "host":     os.getenv("PG_HOST"),
    "port":     os.getenv("PG_PORT"),
    "user":     os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
    "dbname":   os.getenv("PG_DB")
}
USE_POSTGRES = all(POSTGRES_VARS.values())

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
def get_connection():
    """
    Makes connection to either SQLite (default) or Postgres (user-defined).
    """
    if USE_POSTGRES:
        return psycopg.connect(**POSTGRES_VARS)
    return sqlite3.connect(SQLITE_FILE)

def init_db(conn):
    """
    Ensures the target table exists.
    """
    cursor = conn.cursor()

    if USE_POSTGRES:
        ddl = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id              SERIAL PRIMARY KEY,
            timestamp       TEXT    NOT NULL,
            mortgage_rate   REAL,
            mbb_price       REAL
        );
        """
    else:
        ddl = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT    NOT NULL,
            mortgage_rate   REAL,
            mbb_price       REAL
        );
        """
    cursor.execute(ddl)
    conn.commit()

def update_table(conn, timestamp, mortgage_rate, mbb_price):
    """
    Appends a new record into the SQLite table.
    """
    cursor = conn.cursor()
    placeholder = "%s" if USE_POSTGRES else "?"
    sql_insert = (
        f"INSERT INTO {TABLE_NAME} "
        f"(timestamp, mortgage_rate, mbb_price) VALUES"
        f"({placeholder}, {placeholder}, {placeholder})"
    )
    cursor.execute(sql_insert, (timestamp, mortgage_rate, mbb_price))
    conn.commit()

# Execution ----------------------------------------------------------------------------
if __name__ == '__main__':
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
    
    # Record the current timestamp and update the table
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    init_db(conn)
    update_table(conn, timestamp_str, mortgage_rate, stock_price)
    conn.close()

    # Feedback
    db_type = "PostgreSQL" if USE_POSTGRES else "SQLite"
    print(f"Data appended to {db_type} table '{TABLE_NAME}'.")
