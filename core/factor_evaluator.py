# core/factor_evaluator.py
"""
因子评估器 - 核心计算功能

保留所有重要的计算逻辑，使用简洁的接口
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.font_manager import FontProperties
import os
import warnings
from typing import Dict, Any, Optional, Tuple
import logging

try:
    from ..config.config import EvaluationConfig
except ImportError:
    from factor_backtest_framework.config.config import EvaluationConfig

# 设置中文字体
try:
    font_path = '/System/Library/Fonts/PingFang.ttc'
    if os.path.exists(font_path):
        chinese_font = FontProperties(fname=font_path)
        mpl.rcParams['font.family'] = chinese_font.get_name()
    else:
        mpl.rcParams['font.family'] = 'Arial Unicode MS'
    mpl.rcParams['axes.unicode_minus'] = False
except:
    pass

warnings.filterwarnings('ignore')

class FactorEvaluator:
    """因子评估器"""
    
    def __init__(self, config: Optional[EvaluationConfig] = None):
        """
        初始化评估器
        
        Args:
            config: 评估配置
        """
        self.config = config or EvaluationConfig()
        self.logger = logging.getLogger(__name__)
    
    def _prepare_data(self, factor_df: pd.DataFrame, returns_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """数据预处理和对齐"""
        # 确保索引是日期类型
        if not isinstance(factor_df.index, pd.DatetimeIndex):
            factor_df.index = pd.to_datetime(factor_df.index)
        if not isinstance(returns_df.index, pd.DatetimeIndex):
            returns_df.index = pd.to_datetime(returns_df.index)
        
        # 格式化列名
        factor_df.columns = factor_df.columns.astype(str).str.strip()
        returns_df.columns = returns_df.columns.astype(str).str.strip()
        
        # 数据对齐
        common_stocks = factor_df.columns.intersection(returns_df.columns)
        common_dates = factor_df.index.intersection(returns_df.index)
        
        if len(common_stocks) == 0:
            raise ValueError("因子数据和收益率数据没有共同的股票")
        if len(common_dates) == 0:
            raise ValueError("因子数据和收益率数据没有共同的日期")
        
        factor_aligned = factor_df.loc[common_dates, common_stocks]
        returns_aligned = returns_df.loc[common_dates, common_stocks]
        
        self.logger.info(f"数据对齐完成 - 日期: {len(common_dates)}, 股票: {len(common_stocks)}")
        
        return factor_aligned, returns_aligned
    
    def calculate_ic(self, factor_df: pd.DataFrame, returns_df: pd.DataFrame) -> Dict[str, Any]:
        """计算IC指标"""
        factor_df, returns_df = self._prepare_data(factor_df, returns_df)
        
        # 计算每日IC和RankIC
        ic_series = factor_df.corrwith(returns_df, axis=1)
        rank_ic_series = factor_df.corrwith(returns_df, method='spearman', axis=1)
        
        # 统计指标
        ic_mean = ic_series.mean()
        ic_std = ic_series.std()
        rank_ic_mean = rank_ic_series.mean()
        
        results = {
            'IC': ic_mean,
            'IC_std': ic_std,
            'ICIR': ic_mean / ic_std if ic_std != 0 else 0,
            'average_rank_IC': rank_ic_mean,
            'IC_win_rate': (ic_series > 0).mean(),
            'ic_series': ic_series,
            'rank_ic_series': rank_ic_series
        }
        
        self.logger.info(f"IC计算完成 - ICIR: {results['ICIR']:.4f}, 平均RankIC: {results['average_rank_IC']:.4f}")
        return results
    
    def calculate_group_returns(self, factor_df: pd.DataFrame, returns_df: pd.DataFrame) -> np.ndarray:
        """计算分组收益率"""
        factor_df, returns_df = self._prepare_data(factor_df, returns_df)
        group_num = self.config.group_num
        
        def annualized_return(ret, n_periods):
            return (1 + ret) ** (252 / n_periods) - 1
        
        # 对齐数据
        returns_aligned = returns_df.reindex(columns=factor_df.columns).loc[factor_df.index]
        factor_values = factor_df.values
        returns_values = returns_aligned.fillna(0).values
        
        n_periods = factor_df.shape[0]
        group_returns = np.empty((n_periods, group_num))
        group_returns[:] = np.nan
        
        for i in range(n_periods):
            curr_factor = factor_values[i, :]
            curr_returns = returns_values[i, :]
            
            # 合并数据并排序
            combined = np.vstack([curr_factor, curr_returns])
            valid_mask = ~np.isnan(combined[0, :])
            combined = combined[:, valid_mask]
            
            if combined.shape[1] >= group_num:
                # 按因子值降序排序
                sort_indices = (-combined[0, :]).argsort()
                combined = combined[:, sort_indices]
                
                # 分组计算收益
                n_stocks = combined.shape[1]
                stocks_per_group = n_stocks // group_num
                
                for group_idx in range(group_num):
                    start_idx = group_idx * stocks_per_group
                    end_idx = (group_idx + 1) * stocks_per_group if group_idx < group_num - 1 else n_stocks
                    group_returns[i, group_idx] = np.nanmean(combined[1, start_idx:end_idx])
        
        # 计算年化收益
        group_df = pd.DataFrame(group_returns)
        cumulative_returns = (1 + group_df.fillna(0)).cumprod().iloc[-1] - 1
        annualized_returns = annualized_return(cumulative_returns, n_periods)
        
        self.logger.info(f"分组收益计算完成 - {group_num}组")
        return annualized_returns.values
    
    def calculate_long_short_returns(self, factor_df: pd.DataFrame, returns_df: pd.DataFrame) -> Dict[str, Any]:
        """计算多空组合收益"""
        factor_df, returns_df = self._prepare_data(factor_df, returns_df)
        
        long_percentile = self.config.long_percentile
        short_percentile = self.config.short_percentile
        
        def create_portfolio_weights(factor_row):
            """创建投资组合权重"""
            if factor_row.isna().all():
                return pd.Series(0, index=factor_row.index)
            
            valid_values = factor_row.dropna()
            if len(valid_values) < 10:
                return pd.Series(0, index=factor_row.index)
            
            high_threshold = np.percentile(valid_values, long_percentile)
            low_threshold = np.percentile(valid_values, short_percentile)
            
            weights = pd.Series(0.0, index=factor_row.index)
            
            # 多头权重
            long_mask = factor_row >= high_threshold
            n_long = long_mask.sum()
            if n_long > 0:
                weights[long_mask] = 0.5 / n_long
            
            # 空头权重
            short_mask = factor_row <= low_threshold
            n_short = short_mask.sum()
            if n_short > 0:
                weights[short_mask] = -0.5 / n_short
            
            return weights
        
        # 计算权重和收益
        portfolio_weights = factor_df.apply(create_portfolio_weights, axis=1)
        returns_aligned = returns_df.reindex(index=portfolio_weights.index, columns=portfolio_weights.columns).fillna(0)
        portfolio_returns = (portfolio_weights * returns_aligned).sum(axis=1)
        
        # 计算净值和指标
        cumulative_nav = (1 + portfolio_returns).cumprod()
        total_return = cumulative_nav.iloc[-1] - 1
        annualized_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
        
        # 计算换手率
        turnover = portfolio_weights.diff().abs().sum(axis=1).mean()
        
        results = {
            'portfolio_returns': portfolio_returns,
            'cumulative_nav': cumulative_nav,
            'annualized_return': annualized_return,
            'turnover': turnover,
            'total_return': total_return,
            'portfolio_weights': portfolio_weights
        }
        
        self.logger.info(f"多空组合收益计算完成 - 年化收益: {annualized_return:.4f}")
        return results
    
    def calculate_excess_returns(self, factor_df: pd.DataFrame, returns_df: pd.DataFrame) -> Dict[str, Any]:
        """计算多头超额收益"""
        factor_df, returns_df = self._prepare_data(factor_df, returns_df)
        
        long_percentile = self.config.long_percentile
        
        def create_long_weights(factor_row):
            """创建多头权重"""
            if factor_row.isna().all():
                return pd.Series(0, index=factor_row.index)
            
            valid_values = factor_row.dropna()
            if len(valid_values) < 10:
                return pd.Series(0, index=factor_row.index)
            
            threshold = np.percentile(valid_values, long_percentile)
            weights = pd.Series(0.0, index=factor_row.index)
            selected_mask = factor_row >= threshold
            n_selected = selected_mask.sum()
            
            if n_selected > 0:
                weights[selected_mask] = 1.0 / n_selected
            
            return weights
        
        # 计算权重和收益
        long_weights = factor_df.apply(create_long_weights, axis=1)
        returns_aligned = returns_df.reindex(index=long_weights.index, columns=long_weights.columns).fillna(0)
        
        portfolio_returns = (long_weights * returns_aligned).sum(axis=1)
        benchmark_returns = returns_aligned.mean(axis=1)
        excess_returns = portfolio_returns - benchmark_returns
        
        # 计算净值
        portfolio_nav = (1 + portfolio_returns).cumprod()
        benchmark_nav = (1 + benchmark_returns).cumprod()
        excess_nav = (1 + excess_returns).cumprod()
        
        # 年化超额收益
        total_excess_return = excess_nav.iloc[-1] - 1
        annualized_excess_return = (1 + total_excess_return) ** (252 / len(excess_returns)) - 1
        
        # 换手率
        turnover = long_weights.diff().abs().sum(axis=1).mean()
        
        results = {
            'portfolio_returns': portfolio_returns,
            'benchmark_returns': benchmark_returns,
            'excess_returns': excess_returns,
            'portfolio_nav': portfolio_nav,
            'benchmark_nav': benchmark_nav,
            'excess_nav': excess_nav,
            'annualized_excess_return': annualized_excess_return,
            'turnover': turnover
        }
        
        self.logger.info(f"多头超额收益计算完成 - 年化超额收益: {annualized_excess_return:.4f}")
        return results
    
    def evaluate(self, factor_df: pd.DataFrame, returns_df: pd.DataFrame) -> Dict[str, Any]:
        """完整评估"""
        self.logger.info("开始因子评估...")
        
        try:
            # 数据取反（保持原有逻辑）
            factor_df = -factor_df
            
            # 各项指标计算
            ic_results = self.calculate_ic(factor_df, returns_df)
            group_returns = self.calculate_group_returns(factor_df, returns_df)
            long_short_results = self.calculate_long_short_returns(factor_df, returns_df)
            excess_results = self.calculate_excess_returns(factor_df, returns_df)
            
            # 汇总结果
            results = {
                'evaluation_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_period': {
                    'start_date': factor_df.index.min().strftime('%Y-%m-%d'),
                    'end_date': factor_df.index.max().strftime('%Y-%m-%d'),
                    'total_days': len(factor_df),
                    'total_stocks': len(factor_df.columns)
                },
                
                # IC指标
                'ICIR': ic_results['ICIR'],
                'average_rank_IC': ic_results['average_rank_IC'],
                'IC': ic_results['IC'],
                'IC_std': ic_results['IC_std'],
                
                # 分组收益
                'group_returns': group_returns,
                
                # 多空组合
                'long_short_return': long_short_results['annualized_return'],
                'long_short_turnover': long_short_results['turnover'],
                'long_short_nav': long_short_results['cumulative_nav'],
                
                # 多头超额收益
                'excess_return': excess_results['annualized_excess_return'],
                'long_turnover': excess_results['turnover'],
                'excess_nav': excess_results['excess_nav'],
                
                # 时间序列数据
                'ic_series': ic_results['ic_series'],
                'rank_ic_series': ic_results['rank_ic_series']
            }
            
            self.logger.info("因子评估完成")
            self._log_summary(results, verbose=True)
            
            return results
            
        except Exception as e:
            self.logger.error(f"因子评估失败: {str(e)}")
            raise
    
    def _log_summary(self, results: Dict[str, Any], verbose: bool = True):
        """打印评估摘要"""
        if verbose:
            # 详细模式 - 显示完整信息
            self.logger.info("="*50)
            self.logger.info("因子评估结果摘要")
            self.logger.info("="*50)
            self.logger.info(f"数据期间: {results['data_period']['start_date']} 至 {results['data_period']['end_date']}")
            self.logger.info(f"ICIR: {results['ICIR']:.4f}  |  平均RankIC: {results['average_rank_IC']:.4f}")
            self.logger.info(f"多空年化收益: {results['long_short_return']:.4f}  |  超额年化收益: {results['excess_return']:.4f}")
            self.logger.info(f"多空换手率: {results['long_short_turnover']:.4f}")
            
            # 分组收益率 - 紧凑格式
            group_returns = results['group_returns']
            groups_str = "  |  ".join([f"组{i+1}: {ret:.4f}" for i, ret in enumerate(group_returns)])
            self.logger.info(f"分组收益: {groups_str}")
            self.logger.info("="*50)
        else:
            # 简洁模式 - 只显示关键指标
            self.logger.info(f"ICIR: {results['ICIR']:.4f} | RankIC: {results['average_rank_IC']:.4f} | "
                           f"多空收益: {results['long_short_return']:.4f} | 超额收益: {results['excess_return']:.4f}")
    
    def create_chart(self, results: Dict[str, Any], figsize: Tuple[int, int] = (16, 12)) -> plt.Figure:
        """创建评估图表"""
        self.logger.info("创建评估图表...")
        
        # 设置字体和样式
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams.update({'font.size': 12})
        
        # 创建2x2子图
        fig, axs = plt.subplots(2, 2, figsize=figsize)
        
        try:
            # 图1: 分组年化收益率
            group_returns = results['group_returns']
            group_num = len(group_returns)
            
            bars = axs[0, 0].bar(range(1, group_num + 1), group_returns, 
                               color='skyblue', alpha=0.7, edgecolor='navy', linewidth=1)
            axs[0, 0].set_xlabel('分组', fontsize=12)
            axs[0, 0].set_ylabel('年化收益率', fontsize=12)
            axs[0, 0].set_title(f"分组年化收益率 (多空收益: {results['long_short_return']:.4f})", 
                               fontsize=14, fontweight='bold')
            axs[0, 0].set_xticks(range(1, group_num + 1))
            axs[0, 0].grid(True, alpha=0.3)
            
            # 添加数值标签
            for bar, value in zip(bars, group_returns):
                height = bar.get_height()
                axs[0, 0].text(bar.get_x() + bar.get_width()/2., height + 0.001,
                              f'{value:.3f}', ha='center', va='bottom', fontsize=10)
            
            # 图2: 多头超额净值
            excess_nav = results['excess_nav']
            axs[0, 1].plot(excess_nav.index, excess_nav, color='orange', 
                          linewidth=2.5, label='超额净值')
            axs[0, 1].axhline(y=1, color='gray', linestyle='--', alpha=0.7)
            axs[0, 1].set_xlabel('日期', fontsize=12)
            axs[0, 1].set_ylabel('累计净值', fontsize=12)
            axs[0, 1].set_title(f"多头超额净值 (年化: {results['excess_return']:.4f})", 
                               fontsize=14, fontweight='bold')
            axs[0, 1].grid(True, alpha=0.3)
            axs[0, 1].legend()
            
            # 图3: 多空净值曲线
            nav = results['long_short_nav']
            axs[1, 0].plot(nav.index, nav, color='green', 
                          linewidth=2.5, label='多空净值')
            axs[1, 0].axhline(y=1, color='gray', linestyle='--', alpha=0.7)
            axs[1, 0].set_xlabel('日期', fontsize=12)
            axs[1, 0].set_ylabel('累计净值', fontsize=12)
            axs[1, 0].set_title(f"多空净值 (Rank IC: {results['average_rank_IC']:.4f}, "
                               f"换手率: {results['long_short_turnover']:.4f})", 
                               fontsize=14, fontweight='bold')
            axs[1, 0].grid(True, alpha=0.3)
            axs[1, 0].legend()
            
            # 图4: 累计Rank IC
            ic_series = results['rank_ic_series']
            cumulative_ic = ic_series.cumsum()
            axs[1, 1].plot(cumulative_ic.index, cumulative_ic, color='blue', 
                          linewidth=2.5, label='累计Rank IC')
            axs[1, 1].axhline(y=0, color='gray', linestyle='--', alpha=0.7)
            axs[1, 1].set_xlabel('日期', fontsize=12)
            axs[1, 1].set_ylabel('累计Rank IC', fontsize=12)
            axs[1, 1].set_title(f"累计Rank IC (ICIR: {results['ICIR']:.4f})", 
                               fontsize=14, fontweight='bold')
            axs[1, 1].grid(True, alpha=0.3)
            axs[1, 1].legend()
            
            # 调整布局
            plt.tight_layout(pad=3.0)
            
            self.logger.info("评估图表创建完成")
            return fig
            
        except Exception as e:
            self.logger.error(f"创建图表失败: {str(e)}")
            raise