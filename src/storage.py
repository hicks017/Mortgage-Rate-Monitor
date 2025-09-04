import sqlite3
import psycopg
from src.config import USE_POSTGRES, POSTGRES_VARS, SQLITE_FILE, TABLE_NAME

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

# Created with AI assistance
