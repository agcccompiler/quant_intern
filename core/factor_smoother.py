# core/factor_smoother.py
"""
因子平滑器 - 简洁的平滑功能

提供常用的因子平滑方法
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

try:
    from ..config.config import SmoothingConfig
except ImportError:
    from factor_backtest_framework.config.config import SmoothingConfig

class FactorSmoother:
    """因子平滑器"""
    
    def __init__(self, config: Optional[SmoothingConfig] = None):
        """
        初始化平滑器
        
        Args:
            config: 平滑配置
        """
        self.config = config or SmoothingConfig()
        self.logger = logging.getLogger(__name__)
    
    def rolling_mean(self, factor_df: pd.DataFrame, window: int = None) -> pd.DataFrame:
        """滚动均值平滑"""
        if window is None:
            window = self.config.rolling_window
        
        if 'code' in factor_df.columns:
            # 长格式数据（包含code列）
            result = factor_df.copy()
            result['factor_smooth'] = result.groupby('code')['factor'].rolling(
                window=window, min_periods=1
            ).mean().reset_index(0, drop=True)
        else:
            # 宽格式数据（股票为列）
            result = factor_df.rolling(window=window, min_periods=1).mean()
        
        self.logger.info(f"滚动均值平滑完成 - 窗口: {window}")
        return result
    
    def rolling_std(self, factor_df: pd.DataFrame, window: int = None) -> pd.DataFrame:
        """滚动标准差"""
        if window is None:
            window = self.config.rolling_window
        
        if 'code' in factor_df.columns:
            # 长格式数据
            result = factor_df.copy()
            result['factor_std'] = result.groupby('code')['factor'].rolling(
                window=window, min_periods=1
            ).std().reset_index(0, drop=True)
        else:
            # 宽格式数据
            result = factor_df.rolling(window=window, min_periods=1).std()
        
        self.logger.info(f"滚动标准差计算完成 - 窗口: {window}")
        return result
    
    def zscore(self, factor_df: pd.DataFrame, window: int = None) -> pd.DataFrame:
        """Z-score标准化"""
        if window is None:
            window = self.config.rolling_window
        
        if 'code' in factor_df.columns:
            # 长格式数据
            result = factor_df.copy()
            grouped = result.groupby('code')['factor']
            rolling_mean = grouped.rolling(window=window, min_periods=1).mean()
            rolling_std = grouped.rolling(window=window, min_periods=1).std()
            result['factor_zscore'] = (
                (result['factor'] - rolling_mean.reset_index(0, drop=True)) / 
                rolling_std.reset_index(0, drop=True)
            ).fillna(0)
        else:
            # 宽格式数据
            rolling_mean = factor_df.rolling(window=window, min_periods=1).mean()
            rolling_std = factor_df.rolling(window=window, min_periods=1).std()
            result = ((factor_df - rolling_mean) / rolling_std).fillna(0)
        
        self.logger.info(f"Z-score标准化完成 - 窗口: {window}")
        return result
    
    def ema(self, factor_df: pd.DataFrame, alpha: float = 0.3) -> pd.DataFrame:
        """指数移动平均"""
        if 'code' in factor_df.columns:
            # 长格式数据
            result = factor_df.copy()
            result['factor_ema'] = result.groupby('code')['factor'].ewm(
                alpha=alpha, adjust=False
            ).mean().reset_index(0, drop=True)
        else:
            # 宽格式数据
            result = factor_df.ewm(alpha=alpha, adjust=False).mean()
        
        self.logger.info(f"指数移动平均完成 - alpha: {alpha}")
        return result
    
    def smooth(self, 
              factor_df: pd.DataFrame, 
              methods: Optional[Dict[str, Dict[str, Any]]] = None) -> pd.DataFrame:
        """
        应用多种平滑方法
        
        Args:
            factor_df: 因子数据
            methods: 平滑方法配置字典
            
        Returns:
            平滑后的因子数据
        """
        if not self.config.enable:
            self.logger.info("因子平滑已禁用")
            return factor_df
        
        if methods is None:
            methods = self.config.methods
        
        result = factor_df.copy()
        
        for method_name, method_params in methods.items():
            if method_name == 'rolling_mean':
                window = method_params.get('window', self.config.rolling_window)
                smoothed = self.rolling_mean(result, window)
                
                if 'code' in result.columns:
                    result['factor'] = smoothed['factor_smooth']
                else:
                    result = smoothed
                    
            elif method_name == 'rolling_std':
                window = method_params.get('window', self.config.rolling_window)
                std_result = self.rolling_std(result, window)
                
                if 'code' in result.columns:
                    result['factor_std'] = std_result['factor_std']
                    
            elif method_name == 'zscore':
                window = method_params.get('window', self.config.rolling_window)
                zscore_result = self.zscore(result, window)
                
                if 'code' in result.columns:
                    result['factor'] = zscore_result['factor_zscore']
                else:
                    result = zscore_result
                    
            elif method_name == 'ema':
                alpha = method_params.get('alpha', 0.3)
                ema_result = self.ema(result, alpha)
                
                if 'code' in result.columns:
                    result['factor'] = ema_result['factor_ema']
                else:
                    result = ema_result
        
        self.logger.info(f"因子平滑完成 - 方法: {list(methods.keys())}")
        return result
