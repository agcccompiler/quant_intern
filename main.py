# main.py
"""
因子回测框架主流水线

整合因子生成、平滑、评估和结果管理的完整流程
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

try:
    from .config.config import FrameworkConfig, get_config
    from .core.factor_generator import FactorGenerator
    from .core.factor_evaluator import FactorEvaluator  
    from .core.factor_smoother import FactorSmoother
except ImportError:
    from factor_backtest_framework.config.config import FrameworkConfig, get_config
    from factor_backtest_framework.core.factor_generator import FactorGenerator
    from factor_backtest_framework.core.factor_evaluator import FactorEvaluator  
    from factor_backtest_framework.core.factor_smoother import FactorSmoother

class FactorBacktestPipeline:
    """因子回测主流水线"""
    
    def __init__(self, config: Optional[FrameworkConfig] = None):
        """
        初始化流水线
        
        Args:
            config: 框架配置
        """
        self.config = config or get_config()
        self.config.ensure_directories()
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(self.config.output.log_dir, 'pipeline.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.generator = FactorGenerator(self.config.dolphindb)
        self.evaluator = FactorEvaluator(self.config.evaluation)
        self.smoother = FactorSmoother(self.config.smoothing)
        
        # 存储数据
        self.factor_data = None
        self.smoothed_data = None
        self.evaluation_results = None
        
        self.logger.info("因子回测流水线初始化完成")
    
    def _load_data_file(self, file_path: str) -> pd.DataFrame:
        """
        加载数据文件，支持多种压缩格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            DataFrame: 加载的数据
        """
        import lzma
        import gzip
        import zipfile
        import io
        
        file_path = str(file_path)
        self.logger.info(f"检测文件格式: {file_path}")
        
        try:
            # 根据文件扩展名判断压缩格式
            if file_path.endswith('.xz'):
                self.logger.info("检测到.xz压缩格式")
                with lzma.open(file_path, 'rt', encoding='utf-8') as f:
                    df = pd.read_csv(f)
            elif file_path.endswith('.gz'):
                self.logger.info("检测到.gz压缩格式")
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    df = pd.read_csv(f)
            elif file_path.endswith('.zip'):
                self.logger.info("检测到.zip压缩格式")
                with zipfile.ZipFile(file_path, 'r') as zip_file:
                    # 获取zip文件中的第一个CSV文件
                    csv_files = [name for name in zip_file.namelist() if name.endswith('.csv')]
                    if not csv_files:
                        raise ValueError("ZIP文件中未找到CSV文件")
                    csv_filename = csv_files[0]
                    self.logger.info(f"从ZIP文件中读取: {csv_filename}")
                    with zip_file.open(csv_filename) as f:
                        df = pd.read_csv(io.TextIOWrapper(f, encoding='utf-8'))
            elif file_path.endswith('.csv'):
                self.logger.info("检测到标准CSV格式")
                df = pd.read_csv(file_path)
            else:
                # 尝试直接读取，让pandas自动检测
                self.logger.info("尝试自动检测文件格式")
                df = pd.read_csv(file_path)
            
            self.logger.info(f"数据加载成功 - 形状: {df.shape}")
            return df
            
        except Exception as e:
            self.logger.error(f"文件加载失败: {str(e)}")
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
            for encoding in encodings:
                try:
                    self.logger.info(f"尝试使用编码: {encoding}")
                    if file_path.endswith('.xz'):
                        with lzma.open(file_path, 'rt', encoding=encoding) as f:
                            df = pd.read_csv(f)
                    elif file_path.endswith('.gz'):
                        with gzip.open(file_path, 'rt', encoding=encoding) as f:
                            df = pd.read_csv(f)
                    else:
                        df = pd.read_csv(file_path, encoding=encoding)
                    
                    self.logger.info(f"使用编码 {encoding} 加载成功 - 形状: {df.shape}")
                    return df
                except:
                    continue
            
            raise ValueError(f"无法加载文件: {file_path}")
    
    def generate_factor(self, 
                       script_path: Optional[str] = None,
                       params: Optional[Dict[str, Any]] = None,
                       output_filename: Optional[str] = None) -> pd.DataFrame:
        """
        生成因子数据
        
        Args:
            script_path: DolphinDB脚本路径
            params: 脚本参数
            output_filename: 输出文件名
            
        Returns:
            因子DataFrame
        """
        if script_path is None:
            script_path = self.config.factor.script_path
        
        if params is None:
            params = {
                'start_date': self.config.factor.start_date,
                'end_date': self.config.factor.end_date,
                'start_time': self.config.factor.start_time,
                'end_time': self.config.factor.end_time,
                'seconds': self.config.factor.seconds,
                'portion': self.config.factor.portion,
                'job_id': f"{self.config.factor.job_id_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        
        output_path = None
        if output_filename:
            output_path = os.path.join(self.config.factor.output_dir, output_filename)
        
        self.logger.info("开始生成因子数据...")
        self.factor_data = self.generator.generate(script_path, params, output_path)
        
        return self.factor_data
    
    def smooth_factor(self, 
                     factor_df: Optional[pd.DataFrame] = None,
                     methods: Optional[Dict[str, Dict[str, Any]]] = None) -> pd.DataFrame:
        """
        平滑因子数据
        
        Args:
            factor_df: 因子数据，不提供则使用已生成的数据
            methods: 平滑方法配置
            
        Returns:
            平滑后的因子DataFrame
        """
        if factor_df is None:
            if self.factor_data is None:
                raise ValueError("未找到因子数据，请先生成因子")
            factor_df = self.factor_data
        
        self.logger.info("开始因子平滑...")
        self.smoothed_data = self.smoother.smooth(factor_df, methods)
        
        return self.smoothed_data
    
    def evaluate_factor(self, 
                       factor_df: Optional[pd.DataFrame] = None,
                       returns_df: Optional[pd.DataFrame] = None,
                       return_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        评估因子表现
        
        Args:
            factor_df: 因子数据，不提供则使用平滑后或原始数据
            returns_df: 收益率数据
            return_file_path: 收益率文件路径
            
        Returns:
            评估结果字典
        """
        if factor_df is None:
            if self.smoothed_data is not None:
                factor_df = self.smoothed_data
            elif self.factor_data is not None:
                factor_df = self.factor_data
            else:
                raise ValueError("未找到因子数据")
        
        # 如果因子数据是长格式，转换为宽格式
        if 'code' in factor_df.columns and 'day_date' in factor_df.columns:
            factor_df = factor_df.pivot(index='day_date', columns='code', values='factor')
        
        # 加载收益率数据
        if returns_df is None:
            if return_file_path is None:
                raise ValueError("必须提供收益率数据或文件路径")
            
            self.logger.info(f"加载收益率数据: {return_file_path}")
            returns_df = self._load_data_file(return_file_path)
            
            # 确保日期列设置为索引
            if 'day_date' in returns_df.columns:
                returns_df['day_date'] = pd.to_datetime(returns_df['day_date'])
                returns_df.set_index('day_date', inplace=True)
            elif returns_df.index.name != 'day_date':
                # 尝试将第一列作为日期索引
                returns_df.index = pd.to_datetime(returns_df.index)
                if returns_df.index.name is None:
                    returns_df.index.name = 'day_date'
        
        self.logger.info("开始因子评估...")
        self.evaluation_results = self.evaluator.evaluate(factor_df, returns_df)
        
        return self.evaluation_results
    
    def create_visualization(self, 
                           evaluation_results: Optional[Dict[str, Any]] = None,
                           save_path: Optional[str] = None) -> plt.Figure:
        """
        创建可视化图表
        
        Args:
            evaluation_results: 评估结果，不提供则使用已计算的结果
            save_path: 图片保存路径
            
        Returns:
            matplotlib图形对象
        """
        if evaluation_results is None:
            if self.evaluation_results is None:
                raise ValueError("未找到评估结果，请先运行因子评估")
            evaluation_results = self.evaluation_results
        
        self.logger.info("创建可视化图表...")
        fig = self.evaluator.create_chart(evaluation_results)
        
        # 保存图片
        if save_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = os.path.join(
                self.config.output.results_dir, 
                'figures', 
                f'factor_analysis_{timestamp}.{self.config.output.figure_format}'
            )
        
        fig.savefig(
            save_path, 
            format=self.config.output.figure_format,
            dpi=self.config.output.figure_dpi,
            bbox_inches='tight'
        )
        self.logger.info(f"图表已保存: {save_path}")
        
        return fig
    
    def save_results(self, 
                    evaluation_results: Optional[Dict[str, Any]] = None,
                    include_factor_data: bool = True) -> Dict[str, str]:
        """
        保存所有结果
        
        Args:
            evaluation_results: 评估结果
            include_factor_data: 是否保存因子数据
            
        Returns:
            保存的文件路径字典
        """
        if evaluation_results is None:
            evaluation_results = self.evaluation_results
        
        if evaluation_results is None:
            raise ValueError("未找到评估结果")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_files = {}
        
        # 保存评估结果
        results_file = os.path.join(
            self.config.output.results_dir, 
            'data',
            f'evaluation_results_{timestamp}.csv'
        )
        
        # 转换为DataFrame保存
        results_data = []
        for key, value in evaluation_results.items():
            if not isinstance(value, (pd.Series, pd.DataFrame, dict)):
                results_data.append({'metric': key, 'value': value})
        
        if results_data:
            results_df = pd.DataFrame(results_data)
            results_df.to_csv(results_file, index=False)
            saved_files['results'] = results_file
        
        # 保存分组收益率
        if 'group_returns' in evaluation_results:
            group_file = os.path.join(
                self.config.output.results_dir,
                'data', 
                f'group_returns_{timestamp}.csv'
            )
            group_df = pd.DataFrame({
                'group': range(1, len(evaluation_results['group_returns']) + 1),
                'return': evaluation_results['group_returns']
            })
            group_df.to_csv(group_file, index=False)
            saved_files['group_returns'] = group_file
        
        # 保存时间序列数据
        if 'rank_ic_series' in evaluation_results:
            ic_file = os.path.join(
                self.config.output.results_dir,
                'data',
                f'ic_series_{timestamp}.csv'
            )
            ic_df = pd.DataFrame({
                'date': evaluation_results['rank_ic_series'].index,
                'rank_ic': evaluation_results['rank_ic_series'].values
            })
            ic_df.to_csv(ic_file, index=False)
            saved_files['ic_series'] = ic_file
        
        # 保存因子数据
        if include_factor_data:
            if self.smoothed_data is not None:
                smoothed_file = os.path.join(
                    self.config.output.results_dir,
                    'data',
                    f'smoothed_factor_{timestamp}.csv'
                )
                self.smoothed_data.to_csv(smoothed_file, index=False)
                saved_files['smoothed_factor'] = smoothed_file
            
            if self.factor_data is not None:
                factor_file = os.path.join(
                    self.config.output.results_dir,
                    'data',
                    f'raw_factor_{timestamp}.csv'
                )
                self.factor_data.to_csv(factor_file, index=False)
                saved_files['raw_factor'] = factor_file
        
        self.logger.info(f"结果已保存 - 文件数: {len(saved_files)}")
        for file_type, file_path in saved_files.items():
            self.logger.info(f"  {file_type}: {file_path}")
        
        return saved_files
    
    def run_full_pipeline(self, 
                         return_file_path: str,
                         script_path: Optional[str] = None,
                         script_params: Optional[Dict[str, Any]] = None,
                         smoothing_methods: Optional[Dict[str, Dict[str, Any]]] = None,
                         save_results: bool = True) -> Dict[str, Any]:
        """
        运行完整的回测流水线
        
        Args:
            return_file_path: 收益率文件路径
            script_path: DolphinDB脚本路径
            script_params: 脚本参数
            smoothing_methods: 平滑方法配置
            save_results: 是否保存结果
            
        Returns:
            完整的回测结果
        """
        self.logger.info("开始运行完整回测流水线...")
        
        try:
            # 1. 生成因子
            factor_df = self.generate_factor(script_path, script_params)
            
            # 2. 平滑因子
            if self.config.smoothing.enable:
                smoothed_df = self.smooth_factor(factor_df, smoothing_methods)
            else:
                smoothed_df = factor_df
            
            # 3. 评估因子
            evaluation_results = self.evaluate_factor(smoothed_df, return_file_path=return_file_path)
            
            # 4. 创建可视化
            fig = self.create_visualization(evaluation_results)
            
            # 5. 保存结果
            if save_results:
                saved_files = self.save_results(evaluation_results)
                evaluation_results['saved_files'] = saved_files
            
            # 6. 汇总结果
            pipeline_results = {
                'pipeline_config': self.config.to_dict(),
                'factor_data_shape': factor_df.shape if factor_df is not None else None,
                'smoothed_data_shape': smoothed_df.shape if smoothed_df is not None else None,
                'evaluation_results': evaluation_results,
                'execution_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.logger.info("完整回测流水线执行完成")
            return pipeline_results
            
        except Exception as e:
            self.logger.error(f"回测流水线执行失败: {str(e)}")
            raise
    
    def get_summary(self) -> Dict[str, Any]:
        """获取流水线执行摘要"""
        summary = {
            'factor_data_available': self.factor_data is not None,
            'smoothed_data_available': self.smoothed_data is not None,
            'evaluation_completed': self.evaluation_results is not None
        }
        
        if self.factor_data is not None:
            summary['factor_data_shape'] = self.factor_data.shape
        
        if self.smoothed_data is not None:
            summary['smoothed_data_shape'] = self.smoothed_data.shape
        
        if self.evaluation_results is not None:
            summary['key_metrics'] = {
                'ICIR': self.evaluation_results.get('ICIR'),
                'average_rank_IC': self.evaluation_results.get('average_rank_IC'),
                'long_short_return': self.evaluation_results.get('long_short_return'),
                'excess_return': self.evaluation_results.get('excess_return')
            }
        
        return summary
    
    def batch_backtest(self, 
                      return_file_path: str,
                      script_path: Optional[str] = None,
                      script_params: Optional[Dict[str, Any]] = None,
                      parameter_combinations: Optional[List[Dict[str, Any]]] = None,
                      save_results: bool = True) -> Dict[str, Any]:
        """
        批量回测：对同一因子数据尝试多种参数组合
        
        Args:
            return_file_path: 收益率文件路径
            script_path: DolphinDB脚本路径
            script_params: DolphinDB脚本参数
            parameter_combinations: 参数组合列表，每个元素包含smoothing和evaluation配置
            save_results: 是否保存结果
            
        Returns:
            批量回测结果字典
        """
        self.logger.info("="*60)
        self.logger.info("开始批量回测")
        self.logger.info("="*60)
        
        # 默认参数组合
        if parameter_combinations is None:
            parameter_combinations = [
                {
                    'name': '无平滑',
                    'smoothing': {'enable': False},
                    'evaluation': {'group_num': 10}
                },
                {
                    'name': '5日均值',
                    'smoothing': {
                        'enable': True,
                        'methods': {'rolling_mean': {'window': 5}}
                    },
                    'evaluation': {'group_num': 10}
                },
                {
                    'name': '10日均值',
                    'smoothing': {
                        'enable': True,
                        'methods': {'rolling_mean': {'window': 10}}
                    },
                    'evaluation': {'group_num': 10}
                },
                {
                    'name': '5日均值+Z-score',
                    'smoothing': {
                        'enable': True,
                        'methods': {
                            'rolling_mean': {'window': 5},
                            'zscore': {'window': 20}
                        }
                    },
                    'evaluation': {'group_num': 10}
                },
                {
                    'name': 'EMA平滑',
                    'smoothing': {
                        'enable': True,
                        'methods': {'ema': {'alpha': 0.3}}
                    },
                    'evaluation': {'group_num': 10}
                }
            ]
        
        # 生成因子数据（只生成一次）
        if script_path is not None:
            self.logger.info("生成基础因子数据...")
            base_factor_df = self.generate_factor(script_path, script_params)
            if base_factor_df is None:
                raise ValueError("因子生成失败")
        else:
            # 使用已有的因子数据
            if self.factor_data is None:
                raise ValueError("未提供脚本路径且没有预加载的因子数据")
            base_factor_df = self.factor_data.copy()
            self.logger.info(f"使用预加载的因子数据 - 形状: {base_factor_df.shape}")
        
        # 批量回测结果
        batch_results = {
            'configurations': parameter_combinations,
            'results': [],
            'comparison_table': None,
            'execution_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.logger.info(f"将测试 {len(parameter_combinations)} 种参数组合")
        
        # 对每种参数组合进行回测
        for i, combo in enumerate(parameter_combinations, 1):
            combo_name = combo.get('name', f'组合{i}')
            self.logger.info(f"\n[{i}/{len(parameter_combinations)}] 测试组合: {combo_name}")
            
            try:
                # 更新配置
                temp_config = self.config
                if 'smoothing' in combo:
                    # 更新平滑配置
                    for key, value in combo['smoothing'].items():
                        setattr(temp_config.smoothing, key, value)
                
                if 'evaluation' in combo:
                    # 更新评估配置
                    for key, value in combo['evaluation'].items():
                        setattr(temp_config.evaluation, key, value)
                
                # 重新初始化评估器和平滑器
                self.evaluator = FactorEvaluator(temp_config.evaluation)
                self.smoother = FactorSmoother(temp_config.smoothing)
                
                # 应用平滑
                if temp_config.smoothing.enable:
                    smoothed_df = self.smoother.smooth(base_factor_df)
                else:
                    smoothed_df = base_factor_df.copy()
                
                # 评估因子 - 需要先加载收益率数据
                returns_df = self._load_data_file(return_file_path)
                if 'day_date' in returns_df.columns:
                    returns_df['day_date'] = pd.to_datetime(returns_df['day_date'])
                    returns_df.set_index('day_date', inplace=True)
                
                evaluation_results = self.evaluator.evaluate(smoothed_df, returns_df)
                
                # 使用简洁日志模式
                self.evaluator._log_summary(evaluation_results, verbose=False)
                
                # 保存结果
                combo_result = {
                    'combination_name': combo_name,
                    'parameters': combo,
                    'metrics': {
                        'ICIR': evaluation_results['ICIR'],
                        'average_rank_IC': evaluation_results['average_rank_IC'],
                        'long_short_return': evaluation_results['long_short_return'],
                        'excess_return': evaluation_results['excess_return'],
                        'long_short_turnover': evaluation_results['long_short_turnover'],
                        'sharpe_ratio': evaluation_results.get('sharpe_ratio', 0.0),
                        'max_drawdown': evaluation_results.get('max_drawdown', 0.0)
                    },
                    'full_results': evaluation_results
                }
                
                batch_results['results'].append(combo_result)
                
            except Exception as e:
                self.logger.error(f"组合 {combo_name} 测试失败: {str(e)}")
                combo_result = {
                    'combination_name': combo_name,
                    'parameters': combo,
                    'error': str(e)
                }
                batch_results['results'].append(combo_result)
        
        # 生成对比表格
        batch_results['comparison_table'] = self._create_comparison_table(batch_results['results'])
        
        # 保存批量结果
        if save_results:
            saved_files = self._save_batch_results(batch_results)
            batch_results['saved_files'] = saved_files
        
        # 显示汇总结果
        self._display_batch_summary(batch_results)
        
        return batch_results
    
    def _create_comparison_table(self, results: List[Dict[str, Any]]) -> pd.DataFrame:
        """创建参数组合对比表格"""
        comparison_data = []
        
        for result in results:
            if 'error' not in result:
                metrics = result['metrics']
                row = {
                    '组合名称': result['combination_name'],
                    'ICIR': f"{metrics['ICIR']:.4f}",
                    '平均RankIC': f"{metrics['average_rank_IC']:.4f}",
                    '多空年化收益': f"{metrics['long_short_return']:.4f}",
                    '超额年化收益': f"{metrics['excess_return']:.4f}",
                    '多空换手率': f"{metrics['long_short_turnover']:.4f}",
                    '夏普比率': f"{metrics['sharpe_ratio']:.4f}",
                    '最大回撤': f"{metrics['max_drawdown']:.4f}"
                }
                comparison_data.append(row)
            else:
                row = {
                    '组合名称': result['combination_name'],
                    'ICIR': 'ERROR',
                    '平均RankIC': 'ERROR',
                    '多空年化收益': 'ERROR',
                    '超额年化收益': 'ERROR',
                    '多空换手率': 'ERROR',
                    '夏普比率': 'ERROR',
                    '最大回撤': 'ERROR'
                }
                comparison_data.append(row)
        
        return pd.DataFrame(comparison_data)
    
    def _save_batch_results(self, batch_results: Dict[str, Any]) -> Dict[str, str]:
        """保存批量回测结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_files = {}
        
        # 保存对比表格
        comparison_path = os.path.join(
            self.config.output.results_dir, 'data',
            f'batch_comparison_{timestamp}.csv'
        )
        batch_results['comparison_table'].to_csv(comparison_path, index=False, encoding='utf-8-sig')
        saved_files['comparison_table'] = comparison_path
        
        # 保存详细结果
        import json
        detailed_path = os.path.join(
            self.config.output.results_dir, 'data',
            f'batch_detailed_{timestamp}.json'
        )
        
        # 序列化结果（排除不可序列化的对象）
        serializable_results = {
            'configurations': batch_results['configurations'],
            'execution_time': batch_results['execution_time'],
            'summary': []
        }
        
        for result in batch_results['results']:
            if 'error' not in result:
                summary_item = {
                    'combination_name': result['combination_name'],
                    'parameters': result['parameters'],
                    'metrics': result['metrics']
                }
                serializable_results['summary'].append(summary_item)
        
        with open(detailed_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        saved_files['detailed_results'] = detailed_path
        
        return saved_files
    
    def _display_batch_summary(self, batch_results: Dict[str, Any]):
        """显示批量测试汇总"""
        self.logger.info("\n" + "="*60)
        self.logger.info("批量回测结果汇总")
        self.logger.info("="*60)
        
        comparison_table = batch_results['comparison_table']
        
        # 显示表格
        self.logger.info("\n参数组合对比:")
        for _, row in comparison_table.iterrows():
            self.logger.info(f"[{row['组合名称']}] ICIR: {row['ICIR']} | RankIC: {row['平均RankIC']} | "
                           f"多空收益: {row['多空年化收益']} | 超额收益: {row['超额年化收益']}")
        
        # 找出最佳组合
        valid_results = [r for r in batch_results['results'] if 'error' not in r]
        if valid_results:
            best_icir = max(valid_results, key=lambda x: x['metrics']['ICIR'])
            best_excess = max(valid_results, key=lambda x: x['metrics']['excess_return'])
            
            self.logger.info(f"\n🏆 最佳ICIR组合: {best_icir['combination_name']} (ICIR: {best_icir['metrics']['ICIR']:.4f})")
            self.logger.info(f"🎯 最佳超额收益组合: {best_excess['combination_name']} (超额收益: {best_excess['metrics']['excess_return']:.4f})")
        
        self.logger.info("="*60)

def main():
    """命令行入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='因子回测框架')
    parser.add_argument('--return-file', required=True, 
                        help='收益率数据文件路径 (支持.csv, .csv.xz, .csv.gz, .zip等格式)')
    parser.add_argument('--script-path', help='DolphinDB脚本路径')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--batch', action='store_true', 
                        help='启用批量回测模式，测试多种参数组合')
    
    args = parser.parse_args()
    
    # 创建配置
    config = get_config()
    if args.script_path:
        config.factor.script_path = args.script_path
    
    # 创建流水线
    pipeline = FactorBacktestPipeline(config)
    
    if args.batch:
        # 批量回测模式
        print("="*60)
        print("启动批量回测模式")
        print("="*60)
        
        results = pipeline.batch_backtest(
            return_file_path=args.return_file,
            script_path=args.script_path
        )
        
        print("="*60)
        print("批量回测完成！")
        print("="*60)
        
        # 显示最佳结果
        valid_results = [r for r in results['results'] if 'error' not in r]
        if valid_results:
            best_result = max(valid_results, key=lambda x: x['metrics']['ICIR'])
            print(f"🏆 最佳组合: {best_result['combination_name']}")
            print(f"   ICIR: {best_result['metrics']['ICIR']:.4f}")
            print(f"   超额年化收益: {best_result['metrics']['excess_return']:.4f}")
        
        if 'saved_files' in results:
            print("\n保存的文件:")
            for file_type, file_path in results['saved_files'].items():
                print(f"  {file_type}: {file_path}")
    else:
        # 单次回测模式
        results = pipeline.run_full_pipeline(args.return_file)
        
        print("="*60)
        print("回测完成！主要结果:")
        print("="*60)
        
        eval_results = results['evaluation_results']
        print(f"ICIR: {eval_results['ICIR']:.4f}")
        print(f"平均Rank IC: {eval_results['average_rank_IC']:.4f}")
        print(f"多空年化收益: {eval_results['long_short_return']:.4f}")
        print(f"超额年化收益: {eval_results['excess_return']:.4f}")
        
        if 'saved_files' in eval_results:
            print("\n保存的文件:")
            for file_type, file_path in eval_results['saved_files'].items():
                print(f"  {file_type}: {file_path}")

if __name__ == "__main__":
    main()
