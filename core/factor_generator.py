# core/factor_generator.py
"""
因子生成器 - DolphinDB脚本执行器

简洁的接口，专注于DolphinDB脚本执行和因子数据生成
"""

import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import logging

try:
    import dolphindb as ddb
    DDB_AVAILABLE = True
except ImportError:
    DDB_AVAILABLE = False

try:
    from ..config.config import DolphinDBConfig
except ImportError:
    from factor_backtest_framework.config.config import DolphinDBConfig

class FactorGenerator:
    """因子生成器"""
    
    def __init__(self, ddb_config: Optional[DolphinDBConfig] = None):
        """
        初始化因子生成器
        
        Args:
            ddb_config: DolphinDB连接配置
        """
        if not DDB_AVAILABLE:
            raise ImportError("DolphinDB库未安装: pip install dolphindb")
        
        self.ddb_config = ddb_config or DolphinDBConfig()
        self.session = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> ddb.session:
        """建立DolphinDB连接"""
        if self.session is None:
            self.session = ddb.session()
            self.session.connect(
                host=self.ddb_config.host,
                port=self.ddb_config.port,
                userid=self.ddb_config.username,
                password=self.ddb_config.password
            )
            # 测试连接
            self.session.run("1+1")
            self.logger.info(f"已连接到DolphinDB: {self.ddb_config.host}:{self.ddb_config.port}")
        
        return self.session
    
    def disconnect(self):
        """断开连接"""
        if self.session:
            self.session.close()
            self.session = None
            self.logger.info("已断开DolphinDB连接")
    
    def generate(self, 
                script_path: str, 
                params: Dict[str, Any],
                output_path: Optional[str] = None) -> pd.DataFrame:
        """
        执行DolphinDB脚本生成因子
        
        Args:
            script_path: 脚本文件路径
            params: 脚本参数
            output_path: 输出文件路径（可选）
            
        Returns:
            因子DataFrame
        """
        # 读取脚本
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # 替换参数
        for key, value in params.items():
            placeholder = f'{{{key}}}'
            script_content = script_content.replace(placeholder, str(value))
        
        # 执行脚本
        session = self.connect()
        try:
            self.logger.info("开始执行DolphinDB脚本...")
            result = session.run(script_content)
            
            # 转换为DataFrame
            if hasattr(result, 'toDF'):
                df = result.toDF()
            elif isinstance(result, pd.DataFrame):
                df = result
            else:
                df = pd.DataFrame(result)
            
            self.logger.info(f"因子生成完成，数据形状: {df.shape}")
            
            # 保存文件
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                df.to_csv(output_path, index=False)
                self.logger.info(f"因子数据已保存: {output_path}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"因子生成失败: {str(e)}")
            raise
        finally:
            self.disconnect()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
