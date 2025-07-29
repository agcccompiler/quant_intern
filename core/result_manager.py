# core/result_manager.py
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt

class ResultManager:
    """结果管理器 - 负责保存回测结果、参数和图片"""
    
    def __init__(self, results_dir: str = "results"):
        """
        初始化结果管理器
        
        Args:
            results_dir: 结果保存根目录
        """
        self.results_dir = results_dir
        self.csv_dir = os.path.join(results_dir, "csv")
        self.images_dir = os.path.join(results_dir, "images")
        
        # 确保目录存在
        os.makedirs(self.csv_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        # 当前会话信息
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_file = os.path.join(self.csv_dir, "backtest_results.csv")
        
    def save_backtest_results(self, 
                            parameters: Dict[str, Any],
                            evaluation_results: Dict[str, Any],
                            image_path: Optional[str] = None) -> str:
        """
        保存完整的回测结果到CSV文件
        
        Args:
            parameters: 所有输入参数（DolphinDB参数、平滑参数等）
            evaluation_results: 评估结果（ICIR、收益率等）
            image_path: 图片保存路径（相对路径）
            
        Returns:
            保存的CSV文件路径
        """
        # 准备结果记录
        result_record = {
            'session_id': self.session_id,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'image_path': image_path if image_path else ""
        }
        
        # 添加参数信息
        result_record.update({f"param_{k}": v for k, v in parameters.items()})
        
        # 添加评估结果
        result_record.update(evaluation_results)
        
        # 如果结果文件不存在，创建新文件
        if not os.path.exists(self.results_file):
            results_df = pd.DataFrame([result_record])
        else:
            # 读取现有文件并添加新结果
            existing_df = pd.read_csv(self.results_file)
            results_df = pd.concat([existing_df, pd.DataFrame([result_record])], 
                                 ignore_index=True)
        
        # 保存结果
        results_df.to_csv(self.results_file, index=False)
        print(f"回测结果已保存到: {self.results_file}")
        
        return self.results_file
    
    def save_figure(self, fig, title: str = "factor_analysis") -> str:
        """
        保存matplotlib图片
        
        Args:
            fig: matplotlib图形对象
            title: 图片标题，用于文件名
            
        Returns:
            保存的图片路径（相对路径）
        """
        # 生成文件名
        filename = f"{title}_{self.session_id}.png"
        full_path = os.path.join(self.images_dir, filename)
        
        # 保存图片
        fig.savefig(full_path, dpi=300, bbox_inches='tight')
        print(f"图片已保存到: {full_path}")
        
        # 返回相对路径（用于CSV记录）
        return os.path.join("images", filename)
    
    def save_factor_data(self, factor_df: pd.DataFrame, 
                        filename: Optional[str] = None) -> str:
        """
        保存因子数据到CSV
        
        Args:
            factor_df: 因子数据DataFrame
            filename: 可选的文件名，不提供则自动生成
            
        Returns:
            保存的文件路径
        """
        if filename is None:
            filename = f"factor_data_{self.session_id}.csv"
        
        full_path = os.path.join(self.csv_dir, filename)
        factor_df.to_csv(full_path)
        print(f"因子数据已保存到: {full_path}")
        
        return full_path
    
    def save_smoothed_factor_data(self, factor_df: pd.DataFrame, 
                                 filename: Optional[str] = None) -> str:
        """
        保存平滑后的因子数据到CSV
        
        Args:
            factor_df: 平滑后的因子数据DataFrame
            filename: 可选的文件名，不提供则自动生成
            
        Returns:
            保存的文件路径
        """
        if filename is None:
            filename = f"smoothed_factor_data_{self.session_id}.csv"
        
        full_path = os.path.join(self.csv_dir, filename)
        factor_df.to_csv(full_path)
        print(f"平滑因子数据已保存到: {full_path}")
        
        return full_path
    
    def save_parameters(self, parameters: Dict[str, Any], 
                       filename: Optional[str] = None) -> str:
        """
        单独保存参数配置到JSON文件
        
        Args:
            parameters: 参数字典
            filename: 可选的文件名
            
        Returns:
            保存的文件路径
        """
        if filename is None:
            filename = f"parameters_{self.session_id}.json"
        
        full_path = os.path.join(self.results_dir, filename)
        
        # 确保所有参数都是JSON可序列化的
        serializable_params = {}
        for k, v in parameters.items():
            if isinstance(v, (str, int, float, bool, list, dict, type(None))):
                serializable_params[k] = v
            else:
                serializable_params[k] = str(v)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_params, f, indent=4, ensure_ascii=False)
        
        print(f"参数配置已保存到: {full_path}")
        return full_path
    
    def load_previous_results(self) -> pd.DataFrame:
        """
        加载之前的回测结果
        
        Returns:
            历史结果DataFrame，如果文件不存在则返回空DataFrame
        """
        if os.path.exists(self.results_file):
            return pd.read_csv(self.results_file)
        else:
            return pd.DataFrame()
    
    def get_best_result(self, metric: str = "ICIR") -> Optional[Dict[str, Any]]:
        """
        获取历史最佳结果
        
        Args:
            metric: 用于比较的指标名称
            
        Returns:
            最佳结果记录，如果没有历史数据则返回None
        """
        results_df = self.load_previous_results()
        
        if results_df.empty or metric not in results_df.columns:
            return None
        
        # 找到指标最大的记录
        best_idx = results_df[metric].idxmax()
        return results_df.iloc[best_idx].to_dict()
    
    def get_session_id(self) -> str:
        """获取当前会话ID"""
        return self.session_id
    
    def cleanup_old_files(self, days_threshold: int = 30):
        """
        清理旧文件（可选功能）
        
        Args:
            days_threshold: 保留天数阈值
        """
        # 这里可以实现清理逻辑，删除超过指定天数的文件
        pass
