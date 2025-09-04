import os

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

# Created with AI assistance
