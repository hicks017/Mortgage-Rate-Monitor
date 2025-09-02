from src.storage import get_connection, init_db, update_table
from src.fetch import extract_30yr_rate, get_stock_price
from src.config import mortgage_url, ticker
from datetime import datetime
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_db():
    """
    Initialize the database to ensure the table exists.
    """
    conn = get_connection()
    init_db(conn)
    conn.close()

def fetch_and_store_data():
    """
    Fetch the mortgage rate and stock price, then store them in the database.
    """
    # Ping the mortgage_url to check if the host is reachable
    try:
        response = requests.get(mortgage_url, timeout=5)
        response.raise_for_status()
        logger.info(f"Ping to {mortgage_url} returned status code {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"Failed to reach {mortgage_url}: {e}")
        return
    
    # Scrape for mortgage rate
    try:
        mortgage_rate = extract_30yr_rate(mortgage_url)
        logger.info(f"Fetched 30-year fixed mortgage rate: {mortgage_rate}%")
    except Exception as e:
        mortgage_rate = None
        logger.error("Failed to find the 30-year fixed mortgage rate.")
    
    # Fetch stock price
    try:
        stock_price = get_stock_price(ticker)
        logger.info(f"Fetched {ticker} stock price: ${stock_price:.2f}")
    except Exception as e:
        stock_price = None
        logger.error(f"Failed to fetch the stock price for {ticker}.")
    
    # Decide to skip table update if there's any missing data
    if mortgage_rate is None or stock_price is None:
        logger.warning(
            f"Skipping table update: "
            f"mortgage_rate={mortgage_rate}, stock_price={stock_price}"
        )
        return
    
    # Persist     
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    update_table(conn, timestamp_str, mortgage_rate, stock_price)
    conn.close()
    logger.info("Data successfully stored in the database.")

# Created with AI assistance
