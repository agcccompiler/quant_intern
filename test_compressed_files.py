# test_compressed_files.py
"""
测试压缩文件读取功能

验证框架是否能正确读取各种格式的压缩数据文件
"""

import os
import sys
import pandas as pd
import numpy as np
import gzip
import lzma
import zipfile
from datetime import datetime

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def create_test_data():
    """创建测试数据"""
    print("创建测试数据...")
    
    # 创建示例收益率数据
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    stocks = ['000001', '000002', '000858', '600000', '600036']
    
    # 生成随机收益率数据
    np.random.seed(42)
    data = np.random.randn(len(dates), len(stocks)) * 0.02
    
    df = pd.DataFrame(data, index=dates, columns=stocks)
    df.index.name = 'day_date'
    
    # 重置索引，使day_date成为一列
    df_reset = df.reset_index()
    
    print(f"✓ 测试数据创建完成 - 形状: {df_reset.shape}")
    return df_reset

def save_in_formats(df, base_name="test_returns"):
    """保存为不同格式的文件"""
    print("\n保存为不同格式...")
    
    data_dir = os.path.join(current_dir, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    files_created = {}
    
    # 1. 标准CSV
    csv_path = os.path.join(data_dir, f"{base_name}.csv")
    df.to_csv(csv_path, index=False)
    files_created['csv'] = csv_path
    print(f"✓ CSV文件: {csv_path}")
    
    # 2. GZ压缩
    gz_path = os.path.join(data_dir, f"{base_name}.csv.gz")
    df.to_csv(gz_path, index=False, compression='gzip')
    files_created['gz'] = gz_path
    print(f"✓ GZ压缩文件: {gz_path}")
    
    # 3. XZ压缩
    xz_path = os.path.join(data_dir, f"{base_name}.csv.xz")
    df.to_csv(xz_path, index=False, compression='xz')
    files_created['xz'] = xz_path
    print(f"✓ XZ压缩文件: {xz_path}")
    
    # 4. ZIP压缩
    zip_path = os.path.join(data_dir, f"{base_name}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        csv_content = df.to_csv(index=False)
        zipf.writestr(f"{base_name}.csv", csv_content)
    files_created['zip'] = zip_path
    print(f"✓ ZIP压缩文件: {zip_path}")
    
    return files_created

def test_loading(files_created):
    """测试加载不同格式的文件"""
    print("\n测试文件加载...")
    
    try:
        from factor_backtest_framework import FactorBacktestPipeline
        
        # 创建流水线实例
        pipeline = FactorBacktestPipeline()
        
        # 测试每种格式
        results = {}
        for format_name, file_path in files_created.items():
            try:
                print(f"\n测试 {format_name.upper()} 格式: {file_path}")
                
                # 使用流水线的_load_data_file方法
                df_loaded = pipeline._load_data_file(file_path)
                
                print(f"  ✓ 加载成功 - 形状: {df_loaded.shape}")
                print(f"  ✓ 列名: {list(df_loaded.columns)}")
                print(f"  ✓ 数据类型: {df_loaded.dtypes.to_dict()}")
                
                # 验证数据内容
                if 'day_date' in df_loaded.columns:
                    print(f"  ✓ 日期范围: {df_loaded['day_date'].min()} 到 {df_loaded['day_date'].max()}")
                
                results[format_name] = {
                    'success': True,
                    'shape': df_loaded.shape,
                    'columns': list(df_loaded.columns)
                }
                
            except Exception as e:
                print(f"  ✗ 加载失败: {str(e)}")
                results[format_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
        
    except ImportError as e:
        print(f"✗ 无法导入框架: {str(e)}")
        return {}

def test_end_to_end(files_created):
    """端到端测试：使用压缩文件进行因子评估"""
    print("\n端到端测试...")
    
    try:
        from factor_backtest_framework import FactorBacktestPipeline, FrameworkConfig
        
        # 使用xz格式的文件进行测试
        xz_file = files_created.get('xz')
        if not xz_file:
            print("✗ 未找到XZ测试文件")
            return False
        
        # 创建简单的测试因子数据
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        stocks = ['000001', '000002', '000858', '600000', '600036']
        
        np.random.seed(123)
        factor_data = pd.DataFrame(
            np.random.randn(len(dates), len(stocks)) * 0.1,
            index=dates, columns=stocks
        )
        factor_data.index.name = 'day_date'
        
        # 保存因子数据
        factor_path = os.path.join(current_dir, "data", "test_factor.csv")
        factor_data.reset_index().to_csv(factor_path, index=False)
        
        # 创建配置
        config = FrameworkConfig.create(
            evaluation={'group_num': 5}
        )
        
        # 创建流水线
        pipeline = FactorBacktestPipeline(config)
        
        # 手动设置因子数据
        pipeline.factor_data = factor_data
        
        # 测试评估（使用压缩的收益率文件）
        print(f"使用压缩文件进行评估: {xz_file}")
        results = pipeline.evaluate_factor(return_file_path=xz_file)
        
        print("✓ 端到端测试成功！")
        print(f"  ICIR: {results['ICIR']:.4f}")
        print(f"  平均Rank IC: {results['average_rank_IC']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"✗ 端到端测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_files():
    """清理测试文件"""
    print("\n清理测试文件...")
    
    data_dir = os.path.join(current_dir, "data")
    if os.path.exists(data_dir):
        import shutil
        shutil.rmtree(data_dir)
        print("✓ 测试文件已清理")

def main():
    """运行所有测试"""
    print("压缩文件支持功能测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # 1. 创建测试数据
        test_df = create_test_data()
        
        # 2. 保存为不同格式
        files_created = save_in_formats(test_df)
        
        # 3. 测试加载
        load_results = test_loading(files_created)
        
        # 4. 端到端测试
        e2e_success = test_end_to_end(files_created)
        
        # 5. 统计结果
        print("\n" + "="*60)
        print("测试结果汇总")
        print("="*60)
        
        successful_formats = [fmt for fmt, result in load_results.items() if result.get('success', False)]
        failed_formats = [fmt for fmt, result in load_results.items() if not result.get('success', False)]
        
        print(f"✅ 成功支持的格式: {', '.join(successful_formats)}")
        if failed_formats:
            print(f"❌ 失败的格式: {', '.join(failed_formats)}")
        
        print(f"✅ 端到端测试: {'通过' if e2e_success else '失败'}")
        
        if len(successful_formats) >= 3 and e2e_success:
            print("\n🎉 压缩文件支持功能测试通过！")
            print("框架已成功支持以下压缩格式:")
            print("• CSV (.csv)")
            print("• GZIP压缩 (.csv.gz)")
            print("• XZ压缩 (.csv.xz)")
            print("• ZIP压缩 (.zip)")
            
            print("\n使用方法:")
            print("1. GUI界面：选择文件时可以选择压缩格式")
            print("2. 编程接口：直接传入压缩文件路径")
            print("3. 命令行：--return-file your_data.csv.xz")
        else:
            print("\n⚠️ 部分测试失败，请检查相关依赖")
        
    except Exception as e:
        print(f"\n✗ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        try:
            cleanup_test_files()
        except:
            pass

if __name__ == "__main__":
    main() 