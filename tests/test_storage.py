import sqlite3
import unittest
from unittest.mock import patch, MagicMock

import src.storage as storage


class TestStorageSQLite(unittest.TestCase):
    def setUp(self):
        # Force SQLite mode and use an in-memory DB
        storage.USE_POSTGRES = False
        storage.SQLITE_FILE = ":memory:"
        storage.TABLE_NAME = "test_table"

        # Tear down any existing in-memory DB
        try:
            self.conn = storage.get_connection()
        except Exception:
            self.conn = None

    def tearDown(self):
        if self.conn:
            self.conn.close()

    def test_get_connection_returns_sqlite_conn(self):
        conn = storage.get_connection()
        self.assertIsInstance(conn, sqlite3.Connection)

    def test_init_db_creates_table(self):
        conn = storage.get_connection()
        storage.init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (storage.TABLE_NAME,)
        )
        found = cursor.fetchone()
        self.assertIsNotNone(found)
        self.assertEqual(found[0], storage.TABLE_NAME)

    def test_update_table_inserts_row(self):
        conn = storage.get_connection()
        storage.init_db(conn)

        # Insert a sample row
        timestamp = "2025-09-04T12:34:56Z"
        mortgage_rate = 3.14
        mbb_price = 99.99
        storage.update_table(conn, timestamp, mortgage_rate, mbb_price)

        # Verify the row is present
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT timestamp, mortgage_rate, mbb_price FROM {storage.TABLE_NAME}"
        )
        row = cursor.fetchone()
        self.assertEqual(row, (timestamp, mortgage_rate, mbb_price))


class TestStoragePostgres(unittest.TestCase):
    def setUp(self):
        # Force Postgres mode
        storage.USE_POSTGRES = True
        storage.POSTGRES_VARS = {"host": "localhost", "port": 5432}
        storage.TABLE_NAME = "pg_table"

        # Create a fake psycopg connection + cursor
        self.mock_conn = MagicMock(name="pg_connection")
        self.mock_cursor = MagicMock(name="pg_cursor")
        self.mock_conn.cursor.return_value = self.mock_cursor

        # Patch psycopg.connect to return our fake connection
        self.patcher = patch("src.storage.psycopg.connect", return_value=self.mock_conn)
        self.mock_connect = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_get_connection_uses_psycopg_and_vars(self):
        conn = storage.get_connection()
        self.mock_connect.assert_called_once_with(**storage.POSTGRES_VARS)
        self.assertIs(conn, self.mock_conn)

    def test_init_db_executes_postgres_ddl(self):
        storage.init_db(self.mock_conn)

        # Grab the SQL string passed to execute
        self.mock_cursor.execute.assert_called_once()
        ddl_sql = self.mock_cursor.execute.call_args[0][0]
        self.assertIn("CREATE TABLE IF NOT EXISTS pg_table", ddl_sql)
        self.assertIn("SERIAL PRIMARY KEY", ddl_sql)
        self.assertIn("mbb_price       REAL", ddl_sql)

        # Ensure commit
        self.mock_conn.commit.assert_called_once()

    def test_update_table_uses_placeholder_and_params(self):
        timestamp = "2025-09-05T01:02:03Z"
        mortgage_rate = 4.56
        mbb_price = 123.45

        storage.update_table(self.mock_conn, timestamp, mortgage_rate, mbb_price)

        # Should get a cursor and execute with %s placeholders
        self.mock_conn.cursor.assert_called_once()
        sql, params = self.mock_cursor.execute.call_args[0]
        self.assertIn("INSERT INTO pg_table", sql)
        # three %s placeholders
        self.assertEqual(sql.count("%s"), 3)
        # Correct param tuple
        self.assertEqual(params, (timestamp, mortgage_rate, mbb_price))

        # Ensure commit after insert
        self.mock_conn.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()

# Created by AI
