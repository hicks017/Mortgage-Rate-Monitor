import unittest
from unittest.mock import patch
import pandas as pd
import yfinance as yf

from src.fetch import get_stock_price
from tests.conftest import DummyTicker

class DummyTicker:
    def __init__(self, symbol, history_df, info_dict):
        self.symbol = symbol
        self._history_df = history_df
        self.info = info_dict

    def history(self, period):
        return self._history_df

class TestGetStockPrice(unittest.TestCase):

    @patch.object(yf, 'Ticker')
    def test_returns_last_close(self, mock_ticker_cls):
        # 1. Prepare a DataFrame with known Close values
        df = pd.DataFrame({'Close': [100.0, 105.5, 110.2]})
        # 2. Configure our DummyTicker
        fake_info = {}
        mock_ticker_cls.return_value = DummyTicker('FAKE', df, fake_info)

        # 3. Call the function under test
        result = get_stock_price('FAKE')

        # 4. Verify it picked the last Close value
        self.assertEqual(result, 110.2)

    @patch.object(yf, 'Ticker')
    def test_falls_back_to_current_price(self, mock_ticker_cls):
        # 1. Empty DataFrame simulates no history
        empty_df = pd.DataFrame()
        # 2. Provide a fake currentPrice
        fake_info = {'currentPrice': 42.7}
        # 3. Patch Ticker to use our dummy
        mock_ticker_cls.return_value = DummyTicker('NOHIST', empty_df, fake_info)

        # 4. Call and assert fallback path
        result = get_stock_price('NOHIST')
        self.assertEqual(result, 42.7)

# Created by AI
