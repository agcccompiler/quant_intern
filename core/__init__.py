# core/__init__.py
"""
因子回测框架核心模块

包含因子生成、评估、平滑的核心功能
"""

from .factor_generator import FactorGenerator
from .factor_evaluator import FactorEvaluator
from .factor_smoother import FactorSmoother

__all__ = [
    'FactorGenerator',
    'FactorEvaluator', 
    'FactorSmoother'
]
