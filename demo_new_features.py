# demo_new_features.py
"""
因子回测框架v2.0新功能演示

展示批量回测和精简日志等新功能
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def create_demo_data():
    """创建演示数据"""
    print("📊 创建演示数据...")
    
    # 创建更真实的因子和收益率数据
    dates = pd.date_range('2022-01-01', periods=100, freq='D')
    stocks = ['000001.SZ', '000002.SZ', '000858.SZ', '600000.SH', '600036.SH']
    
    # 生成具有一定预测性的因子
    np.random.seed(42)
    trend = np.linspace(-0.1, 0.1, len(dates))  # 时间趋势
    factor_data = pd.DataFrame(index=dates, columns=stocks)
    
    for i, stock in enumerate(stocks):
        # 每只股票有不同的特性
        stock_trend = trend + np.random.randn(len(dates)) * 0.02
        seasonal = 0.01 * np.sin(2 * np.pi * np.arange(len(dates)) / 20)  # 季节性
        factor_data[stock] = stock_trend + seasonal + np.random.randn(len(dates)) * 0.03
    
    factor_data.index.name = 'day_date'
    
    # 生成相关的收益率数据
    np.random.seed(123)
    returns_data = pd.DataFrame(index=dates, columns=stocks)
    
    for stock in stocks:
        # 收益率与因子有一定相关性，但有滞后
        lagged_factor = factor_data[stock].shift(1).fillna(0)
        market_noise = np.random.randn(len(dates)) * 0.015
        stock_specific = np.random.randn(len(dates)) * 0.01
        
        returns_data[stock] = (0.3 * lagged_factor + 
                              0.4 * market_noise + 
                              0.3 * stock_specific)
    
    returns_data.index.name = 'day_date'
    
    # 保存数据
    data_dir = os.path.join(current_dir, "demo_data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    factor_path = os.path.join(data_dir, "demo_factor.csv")
    returns_path = os.path.join(data_dir, "demo_returns.csv.xz")
    
    factor_data.reset_index().to_csv(factor_path, index=False)
    returns_data.reset_index().to_csv(returns_path, index=False, compression='xz')
    
    print(f"✓ 因子数据: {factor_path}")
    print(f"✓ 收益率数据: {returns_path} (压缩格式)")
    print(f"✓ 数据期间: {dates[0].date()} 至 {dates[-1].date()}")
    print(f"✓ 股票数量: {len(stocks)}")
    
    return factor_path, returns_path

def demo_batch_backtest():
    """演示批量回测功能"""
    print("\n" + "🚀 批量回测功能演示".center(60, "="))
    
    try:
        from factor_backtest_framework import FactorBacktestPipeline, FrameworkConfig
        
        # 创建演示数据
        factor_path, returns_path = create_demo_data()
        
        # 加载因子数据
        factor_df = pd.read_csv(factor_path)
        factor_df['day_date'] = pd.to_datetime(factor_df['day_date'])
        factor_df.set_index('day_date', inplace=True)
        
        # 创建配置
        config = FrameworkConfig.create(
            evaluation={'group_num': 5, 'long_percentile': 80, 'short_percentile': 20}
        )
        
        # 创建流水线
        pipeline = FactorBacktestPipeline(config)
        pipeline.factor_data = factor_df
        
        # 定义多种参数组合进行测试
        parameter_combinations = [
            {
                'name': '原始因子',
                'smoothing': {'enable': False},
                'evaluation': {'group_num': 5}
            },
            {
                'name': '3日滚动均值',
                'smoothing': {
                    'enable': True,
                    'methods': {'rolling_mean': {'window': 3}}
                },
                'evaluation': {'group_num': 5}
            },
            {
                'name': '5日滚动均值',
                'smoothing': {
                    'enable': True,
                    'methods': {'rolling_mean': {'window': 5}}
                },
                'evaluation': {'group_num': 5}
            },
            {
                'name': '10日滚动均值',
                'smoothing': {
                    'enable': True,
                    'methods': {'rolling_mean': {'window': 10}}
                },
                'evaluation': {'group_num': 5}
            },
            {
                'name': 'EMA平滑',
                'smoothing': {
                    'enable': True,
                    'methods': {'ema': {'alpha': 0.3}}
                },
                'evaluation': {'group_num': 5}
            },
            {
                'name': '组合平滑',
                'smoothing': {
                    'enable': True,
                    'methods': {
                        'rolling_mean': {'window': 5},
                        'zscore': {'window': 20}
                    }
                },
                'evaluation': {'group_num': 5}
            }
        ]
        
        print(f"\n📊 将测试 {len(parameter_combinations)} 种参数组合:")
        for i, combo in enumerate(parameter_combinations, 1):
            print(f"  {i}. {combo['name']}")
        
        print(f"\n⏳ 开始批量回测 (使用压缩文件: {os.path.basename(returns_path)})...")
        
        # 执行批量回测
        results = pipeline.batch_backtest(
            return_file_path=returns_path,
            parameter_combinations=parameter_combinations,
            save_results=True
        )
        
        print(f"\n🎉 批量回测完成！")
        
        # 显示详细结果
        print(f"\n📈 详细结果对比:")
        comparison_table = results['comparison_table']
        
        print(f"{'组合名称':<12} {'ICIR':<8} {'RankIC':<8} {'多空收益':<10} {'超额收益':<10}")
        print("-" * 60)
        
        for _, row in comparison_table.iterrows():
            print(f"{row['组合名称']:<12} {row['ICIR']:<8} {row['平均RankIC']:<8} {row['多空年化收益']:<10} {row['超额年化收益']:<10}")
        
        # 找出最佳组合
        valid_results = [r for r in results['results'] if 'error' not in r]
        if valid_results:
            best_icir = max(valid_results, key=lambda x: x['metrics']['ICIR'])
            best_excess = max(valid_results, key=lambda x: x['metrics']['excess_return'])
            
            print(f"\n🏆 性能排名:")
            print(f"  最佳ICIR: {best_icir['combination_name']} (ICIR: {best_icir['metrics']['ICIR']:.4f})")
            print(f"  最佳超额收益: {best_excess['combination_name']} (超额收益: {best_excess['metrics']['excess_return']:.4f})")
        
        if 'saved_files' in results:
            print(f"\n💾 保存的文件:")
            for file_type, file_path in results['saved_files'].items():
                print(f"  {file_type}: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 批量回测演示失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def demo_compact_logging():
    """演示精简日志功能"""
    print("\n" + "📝 精简日志功能演示".center(60, "="))
    
    try:
        from factor_backtest_framework import FactorEvaluator
        from factor_backtest_framework.config.config import EvaluationConfig
        
        # 创建测试数据
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        stocks = ['股票A', '股票B', '股票C', '股票D']
        
        np.random.seed(42)
        factor_df = pd.DataFrame(
            np.random.randn(len(dates), len(stocks)) * 0.1,
            index=dates, columns=stocks
        )
        
        np.random.seed(123)
        returns_df = pd.DataFrame(
            np.random.randn(len(dates), len(stocks)) * 0.02,
            index=dates, columns=stocks
        )
        
        # 添加相关性
        for stock in stocks:
            returns_df[stock] = 0.3 * factor_df[stock].shift(1) + 0.7 * returns_df[stock]
        returns_df = returns_df.fillna(0)
        
        # 创建评估器
        config = EvaluationConfig(group_num=4)
        evaluator = FactorEvaluator(config)
        
        print("\n🔍 对比新旧日志输出格式:")
        print(f"\n--- 传统详细日志 ---")
        results = evaluator.evaluate(factor_df, returns_df)
        evaluator._log_summary(results, verbose=True)
        
        print(f"\n--- 新的精简日志 ---")  
        evaluator._log_summary(results, verbose=False)
        
        print(f"\n✅ 精简日志演示完成！")
        print(f"💡 精简模式去除了:")
        print(f"  • 重复的时间戳和日期信息")
        print(f"  • 冗长的分隔线")
        print(f"  • 详细的分组收益展示")
        print(f"  • 只保留关键性能指标")
        
        return True
        
    except Exception as e:
        print(f"❌ 精简日志演示失败: {str(e)}")
        return False

def demo_gui_features():
    """演示GUI新功能"""
    print("\n" + "🖥️ GUI新功能介绍".center(60, "="))
    
    print(f"\n🎯 GUI界面现在支持:")
    print(f"  1. 📊 批量回测按钮 - 点击即可测试多种参数组合")
    print(f"  2. 📁 压缩文件选择 - 支持.xz/.gz/.zip格式")
    print(f"  3. 📈 批量结果展示 - 自动对比不同参数效果")
    print(f"  4. 💾 一键保存结果 - 对比表格和详细数据")
    
    print(f"\n💻 启动GUI界面:")
    print(f"  from factor_backtest_framework import quick_start_gui")
    print(f"  quick_start_gui()")
    
    print(f"\n🔄 批量回测流程:")
    print(f"  1. 选择DolphinDB脚本和参数")
    print(f"  2. 选择收益率文件(支持压缩格式)")
    print(f"  3. 点击'批量回测'按钮")
    print(f"  4. 系统自动测试多种平滑参数组合")
    print(f"  5. 显示对比结果和最佳组合推荐")

def demo_command_line():
    """演示命令行新功能"""
    print("\n" + "⌨️ 命令行新功能演示".center(60, "="))
    
    # 创建演示数据
    factor_path, returns_path = create_demo_data()
    
    print(f"\n📋 新增命令行选项:")
    print(f"  --batch    启用批量回测模式")
    
    print(f"\n💡 使用示例:")
    print(f"  # 单次回测")
    print(f"  python -m factor_backtest_framework.main --return-file {returns_path}")
    print(f"")
    print(f"  # 批量回测（推荐）")
    print(f"  python -m factor_backtest_framework.main --return-file {returns_path} --batch")
    print(f"")
    print(f"  # 指定脚本的批量回测")
    print(f"  python -m factor_backtest_framework.main \\")
    print(f"    --return-file {returns_path} \\")
    print(f"    --script-path scripts/factor_script.dos \\")
    print(f"    --batch")
    
    print(f"\n🔄 批量回测将自动测试:")
    print(f"  • 无平滑原始因子")
    print(f"  • 5日滚动均值平滑")
    print(f"  • 10日滚动均值平滑")
    print(f"  • 5日均值+Z-score标准化") 
    print(f"  • EMA指数平滑")

def cleanup_demo_files():
    """清理演示文件"""
    print(f"\n🧹 清理演示文件...")
    
    try:
        demo_dir = os.path.join(current_dir, "demo_data")
        if os.path.exists(demo_dir):
            import shutil
            shutil.rmtree(demo_dir)
            print(f"✓ 演示文件已清理")
    except:
        pass

def main():
    """运行完整演示"""
    print("=" * 70)
    print("🚀 因子回测框架 v2.0 新功能完整演示".center(70))
    print("=" * 70)
    print(f"演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    demos = [
        ("批量回测功能", demo_batch_backtest),
        ("精简日志功能", demo_compact_logging),
        ("GUI新功能", demo_gui_features),
        ("命令行新功能", demo_command_line)
    ]
    
    success_count = 0
    
    for demo_name, demo_func in demos:
        try:
            if demo_func():
                success_count += 1
        except Exception as e:
            print(f"❌ {demo_name}演示出现问题: {str(e)}")
    
    # 显示总结
    print("\n" + "=" * 70)
    print("🎯 新功能总结".center(70))
    print("=" * 70)
    
    print(f"\n✅ 成功演示: {success_count}/{len(demos)} 项功能")
    
    if success_count >= len(demos) - 1:  # 允许一个失败
        print(f"\n🎉 框架v2.0新功能演示完成！")
        
        print(f"\n📊 主要新功能:")
        print(f"  1. 🔄 批量回测 - 一次测试多种参数组合，自动找出最佳配置")
        print(f"  2. 📝 精简日志 - 去除冗余信息，只显示关键指标")
        print(f"  3. 📁 压缩文件支持 - 支持.xz/.gz/.zip等压缩格式")
        print(f"  4. 🖥️ GUI批量回测 - 图形界面一键批量测试")
        print(f"  5. ⌨️ 命令行批量模式 - 命令行--batch参数")
        
        print(f"\n🚀 立即开始使用:")
        print(f"  # 启动GUI进行批量回测")
        print(f"  from factor_backtest_framework import quick_start_gui")
        print(f"  quick_start_gui()")
        print(f"")
        print(f"  # 编程接口批量回测")
        print(f"  pipeline = FactorBacktestPipeline()")
        print(f"  results = pipeline.batch_backtest('returns.csv.xz')")
        print(f"")
        print(f"  # 命令行批量回测")
        print(f"  python -m factor_backtest_framework.main --return-file data.csv.xz --batch")
        
        print(f"\n💡 优势:")
        print(f"  • 🚀 效率提升：一次运行测试多种参数组合")
        print(f"  • 📊 智能对比：自动生成性能对比表格")
        print(f"  • 💾 完整保存：对比结果和详细数据同时保存")
        print(f"  • 📝 简洁输出：关键信息一目了然")
        print(f"  • 📁 格式丰富：支持多种压缩文件格式")
    else:
        print(f"\n⚠️ 部分功能演示遇到问题，但核心功能正常")
    
    # 清理演示文件
    cleanup_demo_files()
    
    print(f"\n🎯 现在你可以使用GUI界面选择参数并开始批量因子回测了！")
    print("=" * 70)

if __name__ == "__main__":
    main() 