# __init__.py
"""
因子回测框架 v2.0

现代化的量化因子回测框架，专注于核心功能：
- DolphinDB因子生成
- 因子平滑处理
- 完整的因子评估
- 可视化结果展示
- GUI界面操作

作者: JinchengGuo
版本: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "JinchengGuo"
__description__ = "Modern factor backtesting framework for quantitative finance"

# 导入核心组件
from .main import FactorBacktestPipeline
from .gui import FactorBacktestGUI
from .core.factor_generator import FactorGenerator
from .core.factor_evaluator import FactorEvaluator
from .core.factor_smoother import FactorSmoother
from .config.config import FrameworkConfig, get_config

# 定义公开API
__all__ = [
    'FactorBacktestPipeline',
    'FactorBacktestGUI',
    'FactorGenerator',
    'FactorEvaluator', 
    'FactorSmoother',
    'FrameworkConfig',
    'get_config'
]

def quick_start_gui():
    """快速启动GUI界面"""
    try:
        app = FactorBacktestGUI()
        app.run()
    except Exception as e:
        print(f"GUI启动失败: {str(e)}")
        raise

def quick_start_pipeline(return_file_path: str, **kwargs):
    """
    快速启动回测流水线
    
    Args:
        return_file_path: 收益率文件路径
        **kwargs: 其他配置参数
        
    Returns:
        回测结果字典
    """
    try:
        config = get_config(**kwargs)
        pipeline = FactorBacktestPipeline(config)
        results = pipeline.run_full_pipeline(return_file_path)
        return results
    except Exception as e:
        print(f"流水线启动失败: {str(e)}")
        raise

def get_info():
    """获取框架信息"""
    return {
        'name': 'Factor Backtest Framework',
        'version': __version__,
        'author': __author__,
        'description': __description__
    }

# 打印框架信息
def print_welcome():
    """打印欢迎信息"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              因子回测框架 v{__version__} - 全新重构版                ║
║                Factor Backtest Framework                      ║
╠══════════════════════════════════════════════════════════════╣
║ 核心特性:                                                      ║
║ • 现代化架构设计                                               ║
║ • DolphinDB高性能因子生成                                      ║
║ • 完整的评估指标体系                                           ║
║ • 多种因子平滑方法                                             ║
║ • 精美的可视化图表                                             ║
║ • 直观的GUI操作界面                                            ║
║ • 多格式文件支持 (CSV/XZ/GZ/ZIP)                              ║
╠══════════════════════════════════════════════════════════════╣
║ 快速开始:                                                      ║
║                                                              ║
║ 1. GUI界面:                                                   ║
║   from factor_backtest_framework import quick_start_gui       ║
║   quick_start_gui()                                           ║
║                                                              ║
║ 2. 编程接口:                                                  ║
║   from factor_backtest_framework import FactorBacktestPipeline║
║   pipeline = FactorBacktestPipeline()                         ║
║   results = pipeline.run_full_pipeline('returns.csv.xz')      ║
║                                                              ║
║ 3. 命令行:                                                    ║
║   python -m factor_backtest_framework.main --return-file ... ║
╚══════════════════════════════════════════════════════════════╝
    """)

# 可选：启动时显示欢迎信息（取消注释启用）
# print_welcome() 