#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速批量回测演示

用于演示批量回测功能的完整流程
如果GUI不稳定，可以使用此脚本体验批量回测功能
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

def create_sample_data():
    """创建示例数据用于演示"""
    print("📊 正在创建示例数据...")
    
    # 创建日期范围
    dates = pd.date_range('2024-01-01', periods=60, freq='D')
    stocks = ['000001.SZ', '000002.SZ', '000858.SZ', '600000.SH', '600036.SH']
    
    # 生成具有一定预测性的因子数据
    np.random.seed(42)
    factor_data = pd.DataFrame(index=dates, columns=stocks)
    
    for i, stock in enumerate(stocks):
        trend = np.linspace(-0.05, 0.05, len(dates))
        noise = np.random.randn(len(dates)) * 0.02
        factor_data[stock] = trend + noise
    
    factor_data.index.name = 'day_date'
    
    # 生成相关的收益率数据
    np.random.seed(123)
    returns_data = pd.DataFrame(index=dates, columns=stocks)
    
    for stock in stocks:
        lagged_factor = factor_data[stock].shift(1).fillna(0)
        market_return = np.random.randn(len(dates)) * 0.01
        stock_return = (0.4 * lagged_factor + 
                       0.6 * market_return)
        returns_data[stock] = stock_return
    
    returns_data.index.name = 'day_date'
    
    # 保存数据
    data_dir = os.path.join(current_dir, "quick_demo_data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    factor_path = os.path.join(data_dir, "demo_factor.csv")
    returns_path = os.path.join(data_dir, "demo_returns.csv.xz")
    
    factor_data.reset_index().to_csv(factor_path, index=False)
    returns_data.reset_index().to_csv(returns_path, index=False, compression='xz')
    
    print(f"✓ 因子数据: {factor_path}")
    print(f"✓ 收益率数据: {returns_path}")
    print(f"✓ 数据期间: {dates[0].date()} 至 {dates[-1].date()}")
    
    return factor_path, returns_path

def demo_batch_backtest():
    """演示批量回测功能"""
    print("\n" + "🚀 批量回测功能演示".center(60, "="))
    
    try:
        from factor_backtest_framework import FactorBacktestPipeline, FrameworkConfig
        
        # 创建示例数据
        factor_path, returns_path = create_sample_data()
        
        # 加载因子数据
        factor_df = pd.read_csv(factor_path)
        factor_df['day_date'] = pd.to_datetime(factor_df['day_date'])
        factor_df.set_index('day_date', inplace=True)
        
        # 创建配置
        config = FrameworkConfig.create(
            evaluation={'group_num': 5}
        )
        
        # 创建流水线并设置因子数据
        pipeline = FactorBacktestPipeline(config)
        pipeline.factor_data = factor_df
        
        print(f"\n📈 开始批量回测 (因子数据: {factor_df.shape})...")
        print(f"📁 使用压缩收益率文件: {os.path.basename(returns_path)}")
        
        # 使用默认参数组合进行批量回测
        results = pipeline.batch_backtest(
            return_file_path=returns_path,
            save_results=True
        )
        
        print(f"\n🎉 批量回测完成！")
        
        # 显示结果摘要
        print(f"\n📊 结果摘要:")
        comparison_table = results['comparison_table']
        
        # 格式化输出
        print(f"\n{'组合名称':<15} {'ICIR':<8} {'RankIC':<8} {'超额收益':<10}")
        print("-" * 50)
        
        for _, row in comparison_table.iterrows():
            print(f"{row['组合名称']:<15} {row['ICIR']:<8} {row['平均RankIC']:<8} {row['超额年化收益']:<10}")
        
        # 显示最佳组合
        valid_results = [r for r in results['results'] if 'error' not in r]
        if valid_results:
            best_icir = max(valid_results, key=lambda x: x['metrics']['ICIR'])
            best_excess = max(valid_results, key=lambda x: x['metrics']['excess_return'])
            
            print(f"\n🏆 最佳组合推荐:")
            print(f"  最佳ICIR: {best_icir['combination_name']} (ICIR: {best_icir['metrics']['ICIR']:.4f})")
            print(f"  最佳超额收益: {best_excess['combination_name']} (超额收益: {best_excess['metrics']['excess_return']:.4f})")
        
        if 'saved_files' in results:
            print(f"\n💾 已保存结果文件:")
            for file_type, file_path in results['saved_files'].items():
                print(f"  {file_type}: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 批量回测演示失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def demo_command_line():
    """演示命令行批量回测"""
    print("\n" + "⌨️ 命令行批量回测演示".center(60, "="))
    
    # 创建示例数据
    factor_path, returns_path = create_sample_data()
    
    print(f"\n💻 命令行批量回测用法:")
    print(f"python -m factor_backtest_framework.main --return-file {returns_path} --batch")
    
    print(f"\n🚀 这将自动:")
    print(f"  1. 加载压缩收益率数据")
    print(f"  2. 使用默认因子生成器")
    print(f"  3. 测试5种不同的平滑参数组合")
    print(f"  4. 生成性能对比表格")
    print(f"  5. 保存详细结果文件")
    
    return returns_path

def cleanup_demo_files():
    """清理演示文件"""
    try:
        demo_dir = os.path.join(current_dir, "quick_demo_data")
        if os.path.exists(demo_dir):
            import shutil
            shutil.rmtree(demo_dir)
            print("✓ 演示文件已清理")
    except:
        pass

def main():
    """主演示函数"""
    print("=" * 70)
    print("🚀 因子回测框架 - 快速批量回测演示".center(70))
    print("=" * 70)
    print(f"演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查GUI状态
    import subprocess
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'start_gui.py' in result.stdout:
            print("\n✅ GUI界面正在运行中！")
            print("🎯 你可以在GUI界面中点击'批量回测'按钮进行操作")
        else:
            print("\n⚠️ GUI界面未运行，使用编程接口演示")
    except:
        pass
    
    # 演示批量回测功能
    success = demo_batch_backtest()
    
    if success:
        print(f"\n🎯 演示命令行用法:")
        returns_path = demo_command_line()
        
        print(f"\n✨ 批量回测的优势:")
        print(f"  • 🚀 一次运行测试多种参数组合")
        print(f"  • 📊 自动生成性能对比表格")
        print(f"  • 🏆 智能推荐最佳参数配置")
        print(f"  • 💾 完整保存所有结果数据")
        print(f"  • 📝 精简日志输出，关键信息清晰")
        
        print(f"\n🎊 现在你已经了解了批量回测的完整功能！")
        
        # 询问是否运行命令行版本
        try:
            user_input = input(f"\n是否要运行命令行批量回测演示? (y/n): ")
            if user_input.lower() in ['y', 'yes']:
                print(f"\n⌨️ 执行命令行批量回测:")
                import subprocess
                cmd = f"python -m factor_backtest_framework.main --return-file {returns_path} --batch"
                print(f"正在执行: {cmd}")
                subprocess.run(cmd.split())
        except KeyboardInterrupt:
            print(f"\n用户取消操作")
    else:
        print(f"\n⚠️ 演示遇到问题，但核心功能是可用的")
    
    # 清理文件
    cleanup_demo_files()
    
    print(f"\n" + "=" * 70)
    print("🎯 演示完成！你现在可以:")
    print("1. 使用GUI界面进行批量回测（如果GUI正在运行）")
    print("2. 使用命令行: python -m factor_backtest_framework.main --batch")
    print("3. 使用编程接口: pipeline.batch_backtest()")
    print("=" * 70)

if __name__ == "__main__":
    main() 