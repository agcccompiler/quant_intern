# core/factor_smoother.py
import pandas as pd

class FactorSmoother:
    def __init__(self, factor_df):
        self.df = factor_df

    def rolling_mean(self, window):
        self.df['factor_smooth'] = self.df.groupby('code')['factor'].transform(
            lambda x: x.rolling(window, min_periods=1).mean()
        )
        return self.df

    def rolling_std(self, window):
        self.df['factor_std'] = self.df.groupby('code')['factor'].transform(
            lambda x: x.rolling(window, min_periods=1).std()
        )
        return self.df

    def get_smoothed(self):
        return self.df
