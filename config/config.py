# config/config.py
"""
因子回测框架配置管理

统一管理所有配置参数，支持动态配置和环境变量
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path

@dataclass
class DolphinDBConfig:
    """DolphinDB连接配置"""
    host: str = "10.80.87.122"
    port: int = 8848
    username: str = "quant_read"
    password: str = "quant_123456"
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'DolphinDBConfig':
        """从环境变量创建配置"""
        return cls(
            host=os.getenv('DDB_HOST', cls.host),
            port=int(os.getenv('DDB_PORT', cls.port)),
            username=os.getenv('DDB_USER', cls.username),
            password=os.getenv('DDB_PASSWORD', cls.password),
            timeout=int(os.getenv('DDB_TIMEOUT', cls.timeout))
        )

@dataclass
class FactorConfig:
    """因子生成配置"""
    script_path: str = "scripts/factor_script.dos"
    output_dir: str = "data/factors"
    
    # 默认参数
    start_date: str = "2019.03.20"
    end_date: str = "2024.06.30"
    start_time: str = "09:30:00.000"
    end_time: str = "14:57:00.000"
    seconds: int = 30
    portion: float = 0.2
    job_id_prefix: str = "factor_job"

@dataclass
class EvaluationConfig:
    """评估配置"""
    group_num: int = 10
    long_percentile: float = 90.0
    short_percentile: float = 10.0
    trading_cost: float = 0.002
    benchmark_return: float = 0.0  # 基准收益率
    
@dataclass
class SmoothingConfig:
    """平滑配置"""
    enable: bool = True
    rolling_window: int = 5
    methods: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'rolling_mean': {'window': 5},
        'rolling_std': {'window': 5}
    })

@dataclass
class OutputConfig:
    """输出配置"""
    results_dir: str = "results"
    log_dir: str = "logs"
    figure_format: str = "png"
    figure_dpi: int = 300
    save_intermediate: bool = True

@dataclass
class FrameworkConfig:
    """框架总配置"""
    dolphindb: DolphinDBConfig = field(default_factory=DolphinDBConfig)
    factor: FactorConfig = field(default_factory=FactorConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    smoothing: SmoothingConfig = field(default_factory=SmoothingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    
    @classmethod
    def create(cls, **overrides) -> 'FrameworkConfig':
        """创建配置实例，支持参数覆盖"""
        config = cls()
        
        # 应用覆盖参数
        for key, value in overrides.items():
            if hasattr(config, key):
                current_attr = getattr(config, key)
                # 检查是否是嵌套配置对象（有__dataclass_fields__属性）
                if hasattr(current_attr, '__dataclass_fields__') and isinstance(value, dict):
                    # 处理嵌套配置
                    for nested_key, nested_value in value.items():
                        if hasattr(current_attr, nested_key):
                            setattr(current_attr, nested_key, nested_value)
                else:
                    setattr(config, key, value)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'dolphindb': {
                'host': self.dolphindb.host,
                'port': self.dolphindb.port,
                'username': self.dolphindb.username,
                'password': self.dolphindb.password,
                'timeout': self.dolphindb.timeout
            },
            'factor': {
                'script_path': self.factor.script_path,
                'output_dir': self.factor.output_dir,
                'start_date': self.factor.start_date,
                'end_date': self.factor.end_date,
                'start_time': self.factor.start_time,
                'end_time': self.factor.end_time,
                'seconds': self.factor.seconds,
                'portion': self.factor.portion,
                'job_id_prefix': self.factor.job_id_prefix
            },
            'evaluation': {
                'group_num': self.evaluation.group_num,
                'long_percentile': self.evaluation.long_percentile,
                'short_percentile': self.evaluation.short_percentile,
                'trading_cost': self.evaluation.trading_cost,
                'benchmark_return': self.evaluation.benchmark_return
            },
            'smoothing': {
                'enable': self.smoothing.enable,
                'rolling_window': self.smoothing.rolling_window,
                'methods': self.smoothing.methods
            },
            'output': {
                'results_dir': self.output.results_dir,
                'log_dir': self.output.log_dir,
                'figure_format': self.output.figure_format,
                'figure_dpi': self.output.figure_dpi,
                'save_intermediate': self.output.save_intermediate
            }
        }
    
    def ensure_directories(self):
        """确保所有必要的目录存在"""
        directories = [
            self.factor.output_dir,
            self.output.results_dir,
            self.output.log_dir,
            os.path.join(self.output.results_dir, 'figures'),
            os.path.join(self.output.results_dir, 'data')
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

# 全局默认配置实例
DEFAULT_CONFIG = FrameworkConfig.create()

def get_config(**overrides) -> FrameworkConfig:
    """获取配置实例"""
    if overrides:
        return FrameworkConfig.create(**overrides)
    return DEFAULT_CONFIG

