import pandas as pd

class DummyTicker:
    def __init__(self, symbol, history_df, info_dict):
        self.symbol = symbol
        self._history_df = history_df
        self.info = info_dict

    def history(self, period):
        return self._history_df

# Created by AI
