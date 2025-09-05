import unittest
from datetime import datetime as real_datetime
from unittest.mock import patch
import requests

import tasks


# A fake database connection that lets us verify close() was called
class DummyConn:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


# A fake HTTP response that tracks whether raise_for_status() was invoked
class DummyResponse:
    def __init__(self, status_code=200, raise_exc=None):
        self.status_code = status_code
        # If raise_exc is set, raise it when raise_for_status() is called
        self._raise_exc = raise_exc
        self.raise_called = False

    def raise_for_status(self):
        self.raise_called = True
        if self._raise_exc:
            # Simulate HTTP errors
            raise self._raise_exc


class TestTasks(unittest.TestCase):
    """
    Test suite for tasks.initialize_db() and tasks.fetch_and_store_data()
    """

    def test_initialize_db_calls_init_and_closes(self):
        # Prepare a dummy connection and spy on init_db
        dummy_conn = DummyConn()

        # Patch get_connection() to return our dummy, and init_db() to a mock
        with patch('tasks.get_connection', return_value=dummy_conn), \
             patch('tasks.init_db') as mock_init_db:
            # Call the function under test
            tasks.initialize_db()

        # Verify init_db was called with our dummy connection
        mock_init_db.assert_called_once_with(dummy_conn)
        # And ensure that close() was called on the connection
        self.assertTrue(dummy_conn.closed)

    def test_fetch_and_store_data_on_request_failure(self):
        # Simulate requests.get() throwing a network error
        # Stub out extraction and price functions (should never run)
        # Provide a dummy DB connection and spy on update_table()
        with patch('tasks.requests.get',
                   side_effect=requests.RequestException("network error")), \
             patch('tasks.extract_30yr_rate', return_value=1.0), \
             patch('tasks.get_stock_price', return_value=2.0), \
             patch('tasks.get_connection', return_value=DummyConn()), \
             patch('tasks.update_table') as mock_update_table:

            # Running fetch_and_store_data() should catch the exception and return None
            result = tasks.fetch_and_store_data()

        self.assertIsNone(result)
        # Because HTTP failed, we never call update_table()
        mock_update_table.assert_not_called()

    def test_fetch_and_store_data_on_extraction_error(self):
        # Simulate a successful HTTP ping
        dummy_resp = DummyResponse()
        # Now extract_30yr_rate() throws, so mortgage_rate becomes None
        # Stock price still succeeds
        with patch('tasks.requests.get', return_value=dummy_resp), \
             patch('tasks.extract_30yr_rate', side_effect=ValueError("no rate")), \
             patch('tasks.get_stock_price', return_value=100.0), \
             patch('tasks.get_connection', return_value=DummyConn()), \
             patch('tasks.update_table') as mock_update_table:

            tasks.fetch_and_store_data()

        # On extraction error, we skip persisting data
        mock_update_table.assert_not_called()

    def test_fetch_and_store_data_on_stock_error(self):
        # Simulate a successful HTTP ping
        dummy_resp = DummyResponse()
        # Mortgage extraction succeeds
        # Stock fetch throws, so stock_price becomes None
        with patch('tasks.requests.get', return_value=dummy_resp), \
             patch('tasks.extract_30yr_rate', return_value=3.5), \
             patch('tasks.get_stock_price', side_effect=RuntimeError("bad ticker")), \
             patch('tasks.get_connection', return_value=DummyConn()), \
             patch('tasks.update_table') as mock_update_table:

            tasks.fetch_and_store_data()

        # On stock fetch error, we skip persisting data
        mock_update_table.assert_not_called()

    def test_fetch_and_store_data_success(self):
        # Freeze datetime.now() so we can predict the timestamp string
        fixed_dt = real_datetime(2021, 5, 6, 7, 8, 9)

        class DummyDateTime(real_datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed_dt

        # Prepare dummy HTTP response and DB connection
        dummy_resp = DummyResponse()
        dummy_conn = DummyConn()

        # HTTP ping returns OK
        # Mortgage and stock fetches succeed
        # Provide our dummy connection and spy on update_table()
        with patch('tasks.datetime', DummyDateTime), \
             patch('tasks.requests.get', return_value=dummy_resp), \
             patch('tasks.extract_30yr_rate', return_value=4.2), \
             patch('tasks.get_stock_price', return_value=123.45), \
             patch('tasks.get_connection', return_value=dummy_conn), \
             patch('tasks.update_table') as mock_update_table:

            tasks.fetch_and_store_data()

        # Ensure we actually called raise_for_status() on the response
        self.assertTrue(dummy_resp.raise_called)

        # Build the timestamp string we expect from our frozen datetime
        expected_ts = fixed_dt.strftime("%Y-%m-%d %H:%M:%S")

        # Verify update_table() got called with the right parameters
        mock_update_table.assert_called_once_with(
            dummy_conn, expected_ts, 4.2, 123.45
        )
        # And ensure the connection was closed at the end
        self.assertTrue(dummy_conn.closed)


if __name__ == '__main__':
    unittest.main()

# Created by AI
