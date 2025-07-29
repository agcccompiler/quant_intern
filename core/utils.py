# core/utils.py
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, List, Tuple
import logging
import json
import warnings

def setup_logging(log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    """
    设置日志记录
    
    Args:
        log_dir: 日志目录
        level: 日志级别
        
    Returns:
        配置好的logger对象
    """
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger('factor_backtest')
    logger.setLevel(level)
    
    # 避免重复添加handler
    if not logger.handlers:
        # 文件handler
        log_file = os.path.join(log_dir, f"backtest_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        
        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def validate_date_format(date_str: str, format_str: str = "%Y.%m.%d") -> bool:
    """
    验证日期格式
    
    Args:
        date_str: 日期字符串
        format_str: 期望的日期格式
        
    Returns:
        是否符合格式
    """
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False

def convert_date_format(date_str: str, 
                       from_format: str = "%Y-%m-%d", 
                       to_format: str = "%Y.%m.%d") -> str:
    """
    转换日期格式
    
    Args:
        date_str: 输入日期字符串
        from_format: 输入格式
        to_format: 输出格式
        
    Returns:
        转换后的日期字符串
    """
    try:
        date_obj = datetime.strptime(date_str, from_format)
        return date_obj.strftime(to_format)
    except ValueError as e:
        raise ValueError(f"日期格式转换失败: {e}")

def generate_date_range(start_date: str, end_date: str, 
                       format_str: str = "%Y.%m.%d") -> List[str]:
    """
    生成日期范围列表
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        format_str: 日期格式
        
    Returns:
        日期字符串列表
    """
    start = datetime.strptime(start_date, format_str)
    end = datetime.strptime(end_date, format_str)
    
    date_list = []
    current = start
    while current <= end:
        date_list.append(current.strftime(format_str))
        current += timedelta(days=1)
    
    return date_list

def validate_file_exists(filepath: str, create_if_missing: bool = False) -> bool:
    """
    验证文件是否存在
    
    Args:
        filepath: 文件路径
        create_if_missing: 如果文件不存在是否创建目录
        
    Returns:
        文件是否存在
    """
    if os.path.exists(filepath):
        return True
    
    if create_if_missing:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        return False
    
    return False

def validate_dataframe_structure(df: pd.DataFrame, 
                                required_columns: List[str],
                                allow_missing: bool = False) -> Tuple[bool, List[str]]:
    """
    验证DataFrame结构
    
    Args:
        df: 要验证的DataFrame
        required_columns: 必需的列名列表
        allow_missing: 是否允许缺失值
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    
    # 检查是否为空
    if df.empty:
        errors.append("DataFrame为空")
        return False, errors
    
    # 检查必需列
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        errors.append(f"缺少必需列: {missing_cols}")
    
    # 检查缺失值
    if not allow_missing:
        for col in required_columns:
            if col in df.columns and df[col].isnull().any():
                null_count = df[col].isnull().sum()
                errors.append(f"列 '{col}' 包含 {null_count} 个缺失值")
    
    # 检查数据类型
    for col in required_columns:
        if col in df.columns:
            if df[col].dtype == 'object':
                # 尝试转换为数值类型
                try:
                    pd.to_numeric(df[col], errors='raise')
                except (ValueError, TypeError):
                    pass  # 可能是字符串列，不需要报错
    
    return len(errors) == 0, errors

def clean_dataframe(df: pd.DataFrame, 
                   drop_duplicates: bool = True,
                   fill_method: Optional[str] = None,
                   outlier_method: Optional[str] = None,
                   outlier_threshold: float = 3.0) -> pd.DataFrame:
    """
    清理DataFrame数据
    
    Args:
        df: 输入DataFrame
        drop_duplicates: 是否删除重复行
        fill_method: 缺失值填充方法 ('mean', 'median', 'forward', 'backward', 'zero')
        outlier_method: 异常值处理方法 ('zscore', 'iqr', 'clip')
        outlier_threshold: 异常值阈值
        
    Returns:
        清理后的DataFrame
    """
    df_clean = df.copy()
    
    # 删除重复行
    if drop_duplicates:
        df_clean = df_clean.drop_duplicates()
    
    # 处理缺失值
    if fill_method:
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        
        if fill_method == 'mean':
            df_clean[numeric_cols] = df_clean[numeric_cols].fillna(df_clean[numeric_cols].mean())
        elif fill_method == 'median':
            df_clean[numeric_cols] = df_clean[numeric_cols].fillna(df_clean[numeric_cols].median())
        elif fill_method == 'forward':
            df_clean = df_clean.fillna(method='ffill')
        elif fill_method == 'backward':
            df_clean = df_clean.fillna(method='bfill')
        elif fill_method == 'zero':
            df_clean = df_clean.fillna(0)
    
    # 处理异常值
    if outlier_method:
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if outlier_method == 'zscore':
                z_scores = np.abs((df_clean[col] - df_clean[col].mean()) / df_clean[col].std())
                df_clean = df_clean[z_scores <= outlier_threshold]
            
            elif outlier_method == 'iqr':
                Q1 = df_clean[col].quantile(0.25)
                Q3 = df_clean[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - outlier_threshold * IQR
                upper_bound = Q3 + outlier_threshold * IQR
                df_clean = df_clean[(df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)]
            
            elif outlier_method == 'clip':
                lower_percentile = (100 - 99) / 2
                upper_percentile = 100 - lower_percentile
                lower_bound = df_clean[col].quantile(lower_percentile / 100)
                upper_bound = df_clean[col].quantile(upper_percentile / 100)
                df_clean[col] = df_clean[col].clip(lower_bound, upper_bound)
    
    return df_clean

def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """
    从文件加载配置
    
    Args:
        config_path: 配置文件路径 (.json, .py 或 .yaml)
        
    Returns:
        配置字典
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    file_ext = os.path.splitext(config_path)[1].lower()
    
    if file_ext == '.json':
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    elif file_ext == '.py':
        # 导入Python模块作为配置
        import importlib.util
        spec = importlib.util.spec_from_file_location("config", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        
        # 提取所有大写的变量作为配置
        config = {}
        for attr_name in dir(config_module):
            if attr_name.isupper() and not attr_name.startswith('_'):
                config[attr_name] = getattr(config_module, attr_name)
        return config
    
    elif file_ext in ['.yml', '.yaml']:
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except ImportError:
            raise ImportError("需要安装PyYAML库以支持YAML配置文件: pip install PyYAML")
    
    else:
        raise ValueError(f"不支持的配置文件格式: {file_ext}")

def save_config_to_file(config: Dict[str, Any], config_path: str):
    """
    保存配置到文件
    
    Args:
        config: 配置字典
        config_path: 保存路径
    """
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    file_ext = os.path.splitext(config_path)[1].lower()
    
    if file_ext == '.json':
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    
    elif file_ext in ['.yml', '.yaml']:
        try:
            import yaml
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        except ImportError:
            raise ImportError("需要安装PyYAML库以支持YAML配置文件: pip install PyYAML")
    
    else:
        raise ValueError(f"不支持的配置文件格式: {file_ext}")

def format_number(value: Union[int, float], 
                 precision: int = 4, 
                 percentage: bool = False) -> str:
    """
    格式化数字显示
    
    Args:
        value: 数值
        precision: 小数位数
        percentage: 是否显示为百分比
        
    Returns:
        格式化后的字符串
    """
    if pd.isna(value):
        return "N/A"
    
    if percentage:
        return f"{value * 100:.{precision}f}%"
    else:
        return f"{value:.{precision}f}"

def calculate_performance_metrics(returns: pd.Series) -> Dict[str, float]:
    """
    计算性能指标
    
    Args:
        returns: 收益率序列
        
    Returns:
        性能指标字典
    """
    returns = returns.dropna()
    
    if len(returns) == 0:
        return {}
    
    metrics = {}
    
    # 基础统计
    metrics['total_return'] = (1 + returns).prod() - 1
    metrics['annualized_return'] = (1 + returns.mean()) ** 252 - 1
    metrics['volatility'] = returns.std() * np.sqrt(252)
    metrics['sharpe_ratio'] = metrics['annualized_return'] / metrics['volatility'] if metrics['volatility'] != 0 else 0
    
    # 风险指标
    metrics['max_drawdown'] = calculate_max_drawdown(returns)
    metrics['var_95'] = returns.quantile(0.05)
    metrics['cvar_95'] = returns[returns <= metrics['var_95']].mean()
    
    # 胜率
    metrics['win_rate'] = (returns > 0).mean()
    
    return metrics

def calculate_max_drawdown(returns: pd.Series) -> float:
    """
    计算最大回撤
    
    Args:
        returns: 收益率序列
        
    Returns:
        最大回撤值
    """
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    return drawdown.min()

def progress_bar(current: int, total: int, prefix: str = "进度", length: int = 50):
    """
    显示进度条
    
    Args:
        current: 当前进度
        total: 总数
        prefix: 前缀文本
        length: 进度条长度
    """
    percent = current / total
    filled_length = int(length * percent)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix}: |{bar}| {percent:.1%} ({current}/{total})', end='', flush=True)
    
    if current == total:
        print()  # 完成时换行

def suppress_warnings():
    """抑制常见警告"""
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', category=RuntimeWarning)

def memory_usage_mb() -> float:
    """
    获取当前内存使用量(MB)
    
    Returns:
        内存使用量
    """
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0

def time_it(func):
    """
    装饰器：计算函数执行时间
    
    Args:
        func: 要计时的函数
        
    Returns:
        装饰后的函数
    """
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        print(f"函数 {func.__name__} 执行时间: {execution_time:.2f} 秒")
        return result
    return wrapper
