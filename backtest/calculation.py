#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from scipy import stats 
from datetime import date 

class Backtester(object):
    def __init__(self, factor_data: pd.DataFrame, 
                 return_data: pd.DataFrame):
        self.factor_data = factor_data # 因子数据
        self.return_data = return_data # 收益数据

        # 因子分析指标
        self.ic_series : pd.DataFrame | None = None # IC序列
        self.icir : float | None = None # ICIR
        self.rankic : pd.DataFrame | None = None # rankIC
        self.rankic_mean : float | None = None # rankIC的平均值

        # 绩效指标
        self.sharpe_ratio : float | None = None # 夏普比率
        self.maximum_drawdown : float | None = None # 最大回撤

        # 分组收益、多头收益、多空收益、换手率 
        self.group_return : pd.DataFrame | None = None # 分组收益
        self.long_return: np.ndarray | None = None # 多头收益
        self.long_short_return: float | None = None # 多空收益
        self.turnover_long: float | None = None # 多头换手率
        self.turnover_long_short: float | None = None # 多空换手率

        self.factor_data_processed: pd.DataFrame | None = None # 处理后的因子数据
        self.return_data_processed: pd.DataFrame | None = None # 处理后的收益数据

        self._adjusted_return: pd.DataFrame | None = None # 对齐后的收益数据(私有属性)
        self._adjusted_factor: pd.DataFrame | None = None # 对齐后的因子数据(私有属性)

        # 回测日期范围
        self.start_date : str | None = None # 起始日期
        self.end_date : str | None = None # 结束日期
    
    def _data_preprocess(self):
        """
        数据预处理方法：对因子数据和收益数据进行清洗、对齐和格式化
        
        主要功能：
        1. 日期格式转换和对齐 - 确保两个数据集使用相同的日期格式和索引
        2. 股票代码格式统一 - 处理不同数据源的股票代码格式差异
        3. 数据类型转换 - 确保数值数据为float类型
        4. 数据对齐和清理 - 保留共同的股票和日期范围
        
        处理后的数据将保存在以下属性中：
        - self.factor_data_processed: 处理后的因子数据
        - self.return_data_processed: 处理后的收益数据
        - self._adjusted_factor: 对齐后的因子数据
        - self._adjusted_return: 对齐后的收益数据
        """
        # 使用DataFrame.copy()方法复制原始数据，避免修改原始数据框
        # copy()创建深拷贝，确保后续操作不会影响原始数据
        factor_df = self.factor_data.copy()
        return_df = self.return_data.copy()
        
        # ========== 第1步：处理因子数据 ==========
        # 检查并删除pandas读取CSV时自动生成的无用索引列
        # 'Unnamed: 0'通常是CSV文件中的行号列，对分析没有意义
        if 'Unnamed: 0' in factor_df.columns:
            # DataFrame.drop()删除指定列，axis=1表示删除列（axis=0删除行）
            factor_df = factor_df.drop('Unnamed: 0', axis=1)
        
        # 使用pd.to_datetime()将字符串日期转换为pandas的Timestamp对象
        # 这样可以进行日期运算和索引操作，支持多种日期格式自动识别
        factor_df['day_date'] = pd.to_datetime(factor_df['day_date'])
        
        # 使用set_index()将日期列设置为DataFrame的索引
        # 日期索引便于时间序列操作，如切片、对齐等
        factor_df = factor_df.set_index('day_date')
        
        # ========== 第2步：处理收益数据 ==========
        # 对收益数据执行相同的日期处理操作
        # pd.to_datetime()确保日期格式一致，便于后续对齐操作
        return_df['day_date'] = pd.to_datetime(return_df['day_date'])
        
        # 设置日期索引，使两个数据框具有相同的索引结构
        return_df = return_df.set_index('day_date')
        
        # ========== 第3步：统一股票代码格式 ==========
        # 处理不同数据源的股票代码格式差异
        # 收益数据格式：000001.SZ（包含交易所后缀）
        # 因子数据格式：000001（纯股票代码）
        # 需要统一格式以便后续匹配
        return_columns = []
        for col in return_df.columns:
            if '.' in col:  # 检查是否包含交易所后缀（如.SZ, .SH）
                # 使用str.split()按'.'分割，取第一部分作为纯股票代码
                stock_code = col.split('.')[0]  # 000001.SZ -> 000001
                return_columns.append(stock_code)
            else:
                # 如果不包含后缀，直接保留原列名
                return_columns.append(col)
        
        # 重新设置列名，统一股票代码格式
        return_df.columns = return_columns
        
        # ========== 第4步：获取共同的股票代码和日期范围 ==========
        # 使用集合运算找到两个数据框共同包含的股票代码
        # set()转换为集合，&进行交集运算，list()转回列表
        common_stocks = list(set(factor_df.columns) & set(return_df.columns))
        # 使用sort()排序，确保股票代码顺序一致，便于后续分析
        common_stocks.sort()
        
        # 使用Index.intersection()找到两个数据框索引的交集（共同日期）
        # 这确保只保留两个数据集都有数据的日期
        common_dates = factor_df.index.intersection(return_df.index)
        # 使用sort_values()对日期进行排序，确保时间序列的正确顺序
        common_dates = common_dates.sort_values()
        
        # ========== 第5步：根据共同股票和日期筛选数据 ==========
        # 使用DataFrame.loc[]进行标签索引，同时筛选行（日期）和列（股票）
        # loc[行索引, 列索引]可以同时选择特定的行和列
        factor_aligned = factor_df.loc[common_dates, common_stocks]
        return_aligned = return_df.loc[common_dates, common_stocks]
        
        # ========== 第6步：数据类型转换 ==========
        # 使用astype()转换数据类型为float，便于数值计算
        # errors='ignore'表示如果转换失败就保持原类型，避免程序崩溃
        # 这一步确保所有数值列都是float类型，NaN值会被正确处理
        factor_aligned = factor_aligned.astype(float, errors='ignore')
        return_aligned = return_aligned.astype(float, errors='ignore')
    
        # ========== 第7步：设置回测的日期范围 ==========
        # 检查是否有共同日期，避免空数据集导致的错误
        if len(common_dates) > 0:
            # 使用strftime()将Timestamp转换为字符串格式（YYYY-MM-DD）
            # [0]获取最早日期，[-1]获取最晚日期
            start_date = common_dates[0].strftime('%Y-%m-%d')
            end_date = common_dates[-1].strftime('%Y-%m-%d')
        
        # ========== 第8步：保存处理后的数据到实例属性 ==========
        # 保存对齐后的数据到私有属性，用于内部计算
        self._adjusted_factor = factor_aligned
        self._adjusted_return = return_aligned
        self.factor_data_processed = factor_aligned
        self.return_data_processed = return_aligned

        # ========== 第9步：将相关变量保存为私有属性 ==========
        # 将相关变量全部保存为私有属性，后续通过单独方法输出
        self._start_date = start_date
        self._end_date = end_date
        self._common_stocks = common_stocks
        self._common_dates = common_dates
        self._factor_shape = factor_aligned.shape
        self._return_shape = return_aligned.shape
    
    def rankic_ic_icir_calc(self):
        """
        计算rankIC、IC(序列)、ICIR 的综合方法
        
        功能说明：
        使用前一期因子值与本期收益率计算斯皮尔曼秩相关系数（Rank IC），
        体现因子的预测能力，并基于IC序列计算相关统计指标
        
        计算流程：
        1. 数据有效性检查
        2. 逐日计算Rank IC值（t-1期因子 vs t期收益率）
        3. 构建IC序列和DataFrame
        4. 计算统计指标（均值、ICIR）
        5. 保存结果到实例属性
        
        返回对象（保存到实例属性）:
        - self.rankic: pd.DataFrame, 包含每日rankIC值，索引为日期
        - self.ic_series: pd.DataFrame, 包含每日IC值，索引为日期，一个日期对应一个IC值
        - self.icir: float, ICIR值（IC均值/IC标准差）
        - self.rankic_mean: float, rankIC的平均值
        """
        # ========== 第1步：数据有效性检查 ==========
        # 检查数据预处理是否完成，确保有对齐后的因子和收益数据
        if self._adjusted_factor is None or self._adjusted_return is None:
            # 抛出ValueError异常，提示用户先进行数据预处理
            raise ValueError("请先调用_data_preprocess方法进行数据预处理")

        # 获取预处理后的对齐数据
        # self._adjusted_factor: 对齐后的因子数据 [日期 × 股票]
        # self._adjusted_return: 对齐后的收益数据 [日期 × 股票]
        factor_data = self._adjusted_factor
        return_data = self._adjusted_return

        # ========== 第2步：初始化存储结构 ==========
        # 获取交易日列表（已排序的日期索引）
        trading_dates = factor_data.index  # pandas.DatetimeIndex对象
        n_dates = len(trading_dates)       # 交易日总数
        
        # 初始化IC值存储数组
        # 使用np.full()创建数组并初始化为NaN，便于识别无效计算
        ic_values = np.full(n_dates, np.nan, dtype=float)  # 形状: (n_dates,)
        
        # ========== 第3步：逐日计算Rank IC ==========
        # 使用前一期因子对本期收益率计算相关系数，体现因子预测能力
        # 遍历范围：从第1个交易日开始（index=1），因为需要前一期因子
        for i in range(1, n_dates):
            
            # 获取前一期因子日期和当期收益日期
            prev_date = trading_dates[i-1]  # t-1期（前一期）
            curr_date = trading_dates[i]    # t期（当期）
            
            # 提取t-1期因子值和t期收益率
            # .loc[date] 返回pandas.Series，索引为股票代码
            daily_factors = factor_data.loc[prev_date]    # t-1期因子值Series
            daily_returns = return_data.loc[curr_date]    # t期收益率Series
            
            # ========== 数据有效性过滤 ==========
            # 创建布尔掩码，标记同时具有有效因子值和收益率的股票
            # 需要确保股票在两个时期都有数据（前一期有因子值，当期有收益率）
            # pd.isna() 检查NaN值，~取反得到非NaN位置
            # & 运算符进行逻辑与操作，要求两个条件同时满足
            valid_mask = (~pd.isna(daily_factors)) & (~pd.isna(daily_returns))
            
            # 统计有效数据点数量
            n_valid = valid_mask.sum()  # True=1, False=0, sum()计算总数
            
            # 检查有效数据是否足够计算相关系数
            if n_valid < 2:  # 相关系数至少需要2个数据点
                # 数据不足时，ic_values[i]保持初始的NaN值
                continue  # 跳过当前循环，处理下一个交易日
            
            # 筛选有效数据进行相关系数计算
            # 使用布尔索引同时筛选t-1期因子值和t期收益率
            valid_factors = daily_factors[valid_mask]  # t-1期有效因子值
            valid_returns = daily_returns[valid_mask]  # t期有效收益率
            
            # ========== 计算斯皮尔曼秩相关系数 ==========
            try:
                # 使用scipy.stats.spearmanr计算秩相关系数
                # 计算t-1期因子值与t期收益率的相关性，体现因子预测能力
                # 参数说明：
                # - valid_factors: t-1期因子值数组
                # - valid_returns: t期收益率数组  
                # - nan_policy='omit': 自动忽略NaN值（额外保护）
                # 返回值：(correlation, p_value)
                correlation, p_value = stats.spearmanr(
                    valid_factors, 
                    valid_returns, 
                    nan_policy='omit'
                )
                
                # 将计算结果存储到数组中
                # 注意：IC值存储在当期位置（i），表示基于t-1期因子预测t期收益的准确性
                ic_values[i] = correlation
                
            except Exception as e:
                # 捕获计算异常（如数据异常、计算错误等）
                # 保持NaN值，继续处理下一个交易日
                # 静默处理异常，保持接口一致性
                continue
        
        # ========== 第4步：构建IC序列DataFrame ==========
        # 创建IC序列DataFrame，日期为索引，IC值为列
        # 使用统一的DataFrame格式，便于时间序列分析和数据访问
        ic_series_df = pd.DataFrame({
            'IC': ic_values  # IC值列
        }, index=trading_dates)  # 日期索引（pandas.DatetimeIndex）
        
        # ========== 第5步：计算统计指标 ==========
        # 计算IC均值（忽略NaN值）
        # np.nanmean() 自动排除NaN值进行均值计算
        ic_mean = np.nanmean(ic_values)
        
        # 计算ICIR（信息系数比率）
        # 筛选出有效的IC值（非NaN）
        valid_ic_values = ic_values[~np.isnan(ic_values)]
        
        # 检查有效IC值数量是否足够计算标准差
        if len(valid_ic_values) >= 2:
            # 计算IC标准差（样本标准差，使用n-1作为分母）
            ic_std = np.std(valid_ic_values, ddof=1)
            
            # 计算ICIR = IC均值 / IC标准差
            if ic_std != 0:  # 避免除零错误
                icir_value = ic_mean / ic_std
            else:
                icir_value = np.nan  # 标准差为0时返回NaN
        else:
            # 有效数据不足时返回NaN
            icir_value = np.nan
        
        # ========== 第6步：保存结果到实例属性 ==========
        # 保存IC序列（DataFrame格式，日期索引）
        # 格式：index=日期，columns=['IC']，每行一个日期对应一个IC值
        self.ic_series = ic_series_df
        
        # 保存rankIC（DataFrame格式，与ic_series相同结构）
        # 为保持接口一致性，rankic和ic_series使用相同的DataFrame
        self.rankic = ic_series_df
        
        # 保存IC均值
        self.rankic_mean = ic_mean
        
        # 保存ICIR值
        self.icir = icir_value


    def group_by_return(self):
        pass

    def excess_return_long(self):
        pass
        
    def excess_return_long_short(self):
        pass

    def turnover_long(self):    
        pass

    def turnover_long_short(self):
        pass

    def get_preprocess_summary(self) -> dict[str, str]:
        """
        输出预处理阶段的关键信息摘要，便于用户快速了解数据对齐和筛选结果。

        Returns:
            dict[str, str]: 包含起止日期、股票数量、日期数量、因子表结构、收益表结构等信息的字典
        """
        summary = {
            "起始日期": getattr(self, "_start_date", "无"),
            "结束日期": getattr(self, "_end_date", "无"),
            "共同股票数量": str(len(getattr(self, "_common_stocks", []))),
            "共同日期数量": str(len(getattr(self, "_common_dates", []))),
            "因子表结构": str(getattr(self, "_factor_shape", "无")),
            "收益表结构": str(getattr(self, "_return_shape", "无"))
        }
        return summary

    def results(self):
        pass

    def results_to_json(self):
        pass

    


