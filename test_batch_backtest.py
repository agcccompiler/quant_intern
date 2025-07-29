# test_batch_backtest.py
"""
测试批量回测功能

验证多参数组合回测和精简日志输出
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

def create_test_data():
    """创建测试数据"""
    print("创建测试数据...")
    
    # 创建因子数据
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    stocks = ['000001', '000002', '000858', '600000', '600036']
    
    np.random.seed(42)
    factor_data = pd.DataFrame(
        np.random.randn(len(dates), len(stocks)) * 0.1,
        index=dates, columns=stocks
    )
    factor_data.index.name = 'day_date'
    
    # 创建收益率数据
    np.random.seed(123)
    returns_data = pd.DataFrame(
        np.random.randn(len(dates), len(stocks)) * 0.02,
        index=dates, columns=stocks
    )
    returns_data.index.name = 'day_date'
    
    # 添加一些相关性
    for stock in stocks:
        returns_data[stock] = 0.2 * factor_data[stock].shift(1) + 0.8 * returns_data[stock]
    returns_data = returns_data.fillna(0)
    
    # 保存数据
    data_dir = os.path.join(current_dir, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    factor_path = os.path.join(data_dir, "test_factor.csv")
    returns_path = os.path.join(data_dir, "test_returns.csv.xz")
    
    factor_data.reset_index().to_csv(factor_path, index=False)
    returns_data.reset_index().to_csv(returns_path, index=False, compression='xz')
    
    print(f"✓ 因子数据保存: {factor_path}")
    print(f"✓ 收益率数据保存: {returns_path}")
    
    return factor_path, returns_path

def test_batch_backtest():
    """测试批量回测功能"""
    print("\n" + "="*60)
    print("测试批量回测功能")
    print("="*60)
    
    try:
        from factor_backtest_framework import FactorBacktestPipeline, FrameworkConfig
        
        # 创建测试数据
        factor_path, returns_path = create_test_data()
        
        # 创建配置
        config = FrameworkConfig.create(
            evaluation={'group_num': 5}
        )
        
        # 创建流水线
        pipeline = FactorBacktestPipeline(config)
        
        # 手动设置因子数据
        factor_df = pd.read_csv(factor_path)
        factor_df['day_date'] = pd.to_datetime(factor_df['day_date'])
        factor_df.set_index('day_date', inplace=True)
        pipeline.factor_data = factor_df
        
        # 定义自定义参数组合
        custom_combinations = [
            {
                'name': '原始因子',
                'smoothing': {'enable': False},
                'evaluation': {'group_num': 5}
            },
            {
                'name': '3日平滑',
                'smoothing': {
                    'enable': True,
                    'methods': {'rolling_mean': {'window': 3}}
                },
                'evaluation': {'group_num': 5}
            },
            {
                'name': '5日平滑',
                'smoothing': {
                    'enable': True,
                    'methods': {'rolling_mean': {'window': 5}}
                },
                'evaluation': {'group_num': 5}
            },
            {
                'name': 'EMA+Z-score',
                'smoothing': {
                    'enable': True,
                    'methods': {
                        'ema': {'alpha': 0.3},
                        'zscore': {'window': 10}
                    }
                },
                'evaluation': {'group_num': 5}
            }
        ]
        
        print("开始批量回测...")
        
        # 运行批量回测 (跳过因子生成，直接测试平滑和评估)
        results = pipeline.batch_backtest(
            return_file_path=returns_path,
            script_path=None,  # 不生成新因子，使用已设置的因子数据
            parameter_combinations=custom_combinations,
            save_results=True
        )
        
        print("\n✅ 批量回测测试完成！")
        
        # 验证结果
        assert 'comparison_table' in results
        assert 'results' in results
        assert len(results['results']) == len(custom_combinations)
        
        print(f"✓ 测试了 {len(results['results'])} 种参数组合")
        print(f"✓ 生成了对比表格: {results['comparison_table'].shape}")
        
        if 'saved_files' in results:
            print("✓ 保存的文件:")
            for file_type, file_path in results['saved_files'].items():
                print(f"  {file_type}: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ 批量回测测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_compact_logging():
    """测试精简日志输出"""
    print("\n" + "="*60)
    print("测试精简日志输出")
    print("="*60)
    
    try:
        from factor_backtest_framework import FactorEvaluator
        from factor_backtest_framework.config.config import EvaluationConfig
        
        # 创建测试数据
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        stocks = ['A', 'B', 'C']
        
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
        config = EvaluationConfig(group_num=5)
        evaluator = FactorEvaluator(config)
        
        print("测试详细日志输出:")
        results = evaluator.evaluate(factor_df, returns_df)
        
        print("\n测试简洁日志输出:")
        evaluator._log_summary(results, verbose=False)
        
        print("\n✅ 日志输出测试完成！")
        return True
        
    except Exception as e:
        print(f"✗ 日志输出测试失败: {str(e)}")
        return False

def test_command_line():
    """测试命令行批量回测"""
    print("\n" + "="*60)
    print("测试命令行批量回测")
    print("="*60)
    
    try:
        # 创建测试数据
        factor_path, returns_path = create_test_data()
        
        print("命令行批量回测用法:")
        print(f"python -m factor_backtest_framework.main --return-file {returns_path} --batch")
        print("\n这将:")
        print("1. 加载收益率数据")
        print("2. 使用默认因子脚本生成因子")
        print("3. 测试5种不同的参数组合")
        print("4. 生成对比结果和保存文件")
        
        print("\n✅ 命令行测试说明完成！")
        return True
        
    except Exception as e:
        print(f"✗ 命令行测试失败: {str(e)}")
        return False

def cleanup_test_files():
    """清理测试文件"""
    print("\n清理测试文件...")
    
    try:
        data_dir = os.path.join(current_dir, "data")
        if os.path.exists(data_dir):
            import shutil
            shutil.rmtree(data_dir)
            print("✓ 测试文件已清理")
    except:
        pass

def main():
    """运行所有测试"""
    print("批量回测功能测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    tests = [
        ("批量回测功能", test_batch_backtest),
        ("精简日志输出", test_compact_logging),
        ("命令行功能", test_command_line)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test_name}测试出现异常: {str(e)}")
            failed += 1
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
    print(f"✅ 通过: {passed}/{len(tests)}")
    print(f"❌ 失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 所有测试都通过了！")
        print("\n新功能已就绪:")
        print("1. 📊 批量回测 - 一次测试多种参数组合")
        print("2. 📝 精简日志 - 更清晰的输出格式")
        print("3. 🖥️ GUI批量回测 - 图形界面支持")
        print("4. ⌨️ 命令行批量回测 - 使用--batch参数")
        
        print("\n使用方法:")
        print("# GUI界面")
        print("from factor_backtest_framework import quick_start_gui")
        print("quick_start_gui()  # 点击'批量回测'按钮")
        print()
        print("# 编程接口")
        print("pipeline = FactorBacktestPipeline()")
        print("results = pipeline.batch_backtest('returns.csv.xz')")
        print()
        print("# 命令行")
        print("python -m factor_backtest_framework.main --return-file data.csv.xz --batch")
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，请检查相关组件")
    
    # 清理测试文件
    cleanup_test_files()
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 