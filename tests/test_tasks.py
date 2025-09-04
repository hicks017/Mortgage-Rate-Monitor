# test/test_tasks.py

import pytest
import requests
from datetime import datetime as real_datetime

import tasks
from tasks import initialize_db, fetch_and_store_data


class DummyConn:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class DummyResponse:
    def __init__(self, status_code=200, raise_exc=None):
        self.status_code = status_code
        self._raise_exc = raise_exc
        self.raise_called = False

    def raise_for_status(self):
        self.raise_called = True
        if self._raise_exc:
            raise self._raise_exc


def test_initialize_db_calls_init_and_closes(monkeypatch):
    dummy_conn = DummyConn()

    # Patch get_connection to return our dummy, and init_db to be a spy
    monkeypatch.setattr(tasks, "get_connection", lambda: dummy_conn)
    init_db_spy = monkeypatch.spy(tasks, "init_db")

    initialize_db()

    # init_db must be called with our connection
    init_db_spy.assert_called_once_with(dummy_conn)
    # And the connection must be closed
    assert dummy_conn.closed


def test_fetch_and_store_data_on_request_failure(monkeypatch):
    # Simulate requests.get raising a RequestException
    monkeypatch.setattr(requests, "get", lambda url, timeout: (_ for _ in ()).throw(
        requests.RequestException("network error")
    ))

    # Patch all downstream calls so they cannot run
    monkeypatch.setattr(tasks, "extract_30yr_rate", lambda url: 1.0)
    monkeypatch.setattr(tasks, "get_stock_price", lambda t: 2.0)
    monkeypatch.setattr(tasks, "get_connection", lambda: DummyConn())
    update_table_spy = monkeypatch.spy(tasks, "update_table")

    # Should return None and never reach update_table
    result = fetch_and_store_data()
    assert result is None
    update_table_spy.assert_not_called()


def test_fetch_and_store_data_on_extraction_error(monkeypatch):
    # 1) requests.get succeeds
    dummy_resp = DummyResponse()
    monkeypatch.setattr(requests, "get", lambda url, timeout: dummy_resp)

    # 2) extract_30yr_rate raises
    monkeypatch.setattr(
        tasks, "extract_30yr_rate", lambda url: (_ for _ in ()).throw(ValueError("no rate"))
    )

    # 3) get_stock_price returns a value
    monkeypatch.setattr(tasks, "get_stock_price", lambda t: 100.0)

    # Spy on DB interactions
    monkeypatch.setattr(tasks, "get_connection", lambda: DummyConn())
    update_table_spy = monkeypatch.spy(tasks, "update_table")

    fetch_and_store_data()
    # Because mortgage_rate is None, update_table never called
    update_table_spy.assert_not_called()


def test_fetch_and_store_data_on_stock_error(monkeypatch):
    # 1) requests.get succeeds
    dummy_resp = DummyResponse()
    monkeypatch.setattr(requests, "get", lambda url, timeout: dummy_resp)

    # 2) extract_30yr_rate returns a value
    monkeypatch.setattr(tasks, "extract_30yr_rate", lambda url: 3.5)

    # 3) get_stock_price raises
    monkeypatch.setattr(
        tasks, "get_stock_price", lambda t: (_ for _ in ()).throw(RuntimeError("bad ticker"))
    )

    # Spy on DB interactions
    monkeypatch.setattr(tasks, "get_connection", lambda: DummyConn())
    update_table_spy = monkeypatch.spy(tasks, "update_table")

    fetch_and_store_data()
    # Because stock_price is None, update_table never called
    update_table_spy.assert_not_called()


def test_fetch_and_store_data_success(monkeypatch):
    # Freeze datetime.now
    fixed_dt = real_datetime(2021, 5, 6, 7, 8, 9)

    class DummyDateTime(real_datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_dt

    monkeypatch.setattr(tasks, "datetime", DummyDateTime)

    # 1) HTTP ping succeeds
    dummy_resp = DummyResponse()
    monkeypatch.setattr(requests, "get", lambda url, timeout: dummy_resp)

    # 2) extraction & price both succeed
    monkeypatch.setattr(tasks, "extract_30yr_rate", lambda url: 4.2)
    monkeypatch.setattr(tasks, "get_stock_price", lambda t: 123.45)

    # 3) DB connection and update
    dummy_conn = DummyConn()
    monkeypatch.setattr(tasks, "get_connection", lambda: dummy_conn)
    update_table_spy = monkeypatch.spy(tasks, "update_table")

    fetch_and_store_data()

    # Ensure raise_for_status was called
    assert dummy_resp.raise_called

    # Build expected timestamp string
    timezone = fixed_dt.strftime("%Y-%m-%d %H:%M:%S")

    # update_table must have been called with our values
    update_table_spy.assert_called_once_with(dummy_conn, timezone, 4.2, 123.45)

    # And the connection must close
    assert dummy_conn.closed

# Created by AI
