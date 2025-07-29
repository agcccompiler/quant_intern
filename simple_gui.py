#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化GUI启动脚本

专门为macOS优化，避免Tkinter兼容性问题
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

def simple_gui():
    """简化版GUI"""
    root = tk.Tk()
    root.title("因子回测框架 - 简化版")
    root.geometry("600x400")
    
    # 主标题
    title_label = tk.Label(root, text="🚀 因子回测框架 v2.0", 
                          font=("Arial", 16, "bold"))
    title_label.pack(pady=20)
    
    # 说明文字
    info_text = """
📊 批量回测功能已就绪！

由于GUI文件对话框在macOS上存在兼容性问题，
建议使用以下方式进行批量回测：

🎯 推荐方式：
"""
    info_label = tk.Label(root, text=info_text, font=("Arial", 12), justify="left")
    info_label.pack(pady=10)
    
    # 按钮区域
    button_frame = tk.Frame(root)
    button_frame.pack(pady=20)
    
    def run_demo():
        """运行演示"""
        try:
            messagebox.showinfo("启动演示", "正在启动批量回测演示...\n请稍等，系统将自动创建示例数据并运行完整的批量回测")
            
            # 直接在当前进程中运行演示，避免subprocess问题
            import pandas as pd
            import numpy as np
            from datetime import datetime
            
            # 导入框架
            sys.path.insert(0, os.path.dirname(current_dir))
            from factor_backtest_framework import FactorBacktestPipeline, FrameworkConfig
            
            # 创建示例数据
            dates = pd.date_range('2024-01-01', periods=40, freq='D')
            stocks = ['000001.SZ', '000002.SZ', '000858.SZ', '600000.SH', '600036.SH']
            
            # 生成因子数据
            np.random.seed(42)
            factor_data = pd.DataFrame(index=dates, columns=stocks)
            for stock in stocks:
                trend = np.linspace(-0.03, 0.03, len(dates))
                noise = np.random.randn(len(dates)) * 0.015
                factor_data[stock] = trend + noise
            factor_data.index.name = 'day_date'
            
            # 生成收益率数据
            np.random.seed(123)
            returns_data = pd.DataFrame(index=dates, columns=stocks)
            for stock in stocks:
                lagged_factor = factor_data[stock].shift(1).fillna(0)
                market_return = np.random.randn(len(dates)) * 0.008
                returns_data[stock] = 0.3 * lagged_factor + 0.7 * market_return
            returns_data.index.name = 'day_date'
            
            # 保存临时数据
            temp_dir = os.path.join(current_dir, "temp_demo")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            returns_path = os.path.join(temp_dir, "demo_returns.csv")
            returns_data.reset_index().to_csv(returns_path, index=False)
            
            # 运行批量回测
            config = FrameworkConfig.create(evaluation={'group_num': 5})
            pipeline = FactorBacktestPipeline(config)
            pipeline.factor_data = factor_data  # 直接设置因子数据
            
            print("🚀 开始GUI批量回测演示...")
            results = pipeline.batch_backtest(
                return_file_path=returns_path,
                save_results=True
            )
            
            # 显示结果
            best_combo = max([r for r in results['results'] if 'error' not in r], 
                           key=lambda x: x['metrics']['ICIR'])
            
            result_msg = f"""批量回测完成！

🏆 最佳组合: {best_combo['combination_name']}
📊 ICIR: {best_combo['metrics']['ICIR']:.4f}
📈 超额收益: {best_combo['metrics']['excess_return']:.4f}

测试了 {len(results['results'])} 种参数组合
详细结果已保存到 results/ 目录

这就是批量回测的完整功能！"""
            
            messagebox.showinfo("演示完成", result_msg)
            
            # 清理临时文件
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
        except Exception as e:
            messagebox.showerror("错误", f"演示运行失败: {str(e)}\n\n可能的解决方案:\n1. 使用命令行: python quick_batch_demo.py\n2. 使用编程接口运行批量回测")
    
    def run_command_line():
        """显示命令行用法"""
        cmd_text = """
命令行批量回测用法：

1. 准备收益率数据文件 (支持.csv, .csv.xz, .csv.gz, .zip)

2. 运行批量回测：
   python -m factor_backtest_framework.main --return-file your_data.csv.xz --batch

3. 或者运行演示：
   python quick_batch_demo.py

4. 编程接口：
   from factor_backtest_framework import FactorBacktestPipeline
   pipeline = FactorBacktestPipeline()
   results = pipeline.batch_backtest('your_data.csv.xz')
        """
        messagebox.showinfo("命令行用法", cmd_text)
    
    def try_full_gui():
        """尝试启动完整GUI"""
        try:
            from factor_backtest_framework.gui import FactorBacktestGUI
            root.destroy()
            app = FactorBacktestGUI()
            app.run()
        except Exception as e:
            messagebox.showerror("GUI错误", 
                               f"完整GUI启动失败: {str(e)}\n\n建议使用演示或命令行方式")
    
    # 按钮
    tk.Button(button_frame, text="🎬 运行批量回测演示", 
              command=run_demo, font=("Arial", 12), 
              bg="#4CAF50", fg="white", padx=20, pady=10).pack(pady=5)
    
    tk.Button(button_frame, text="⌨️ 查看命令行用法", 
              command=run_command_line, font=("Arial", 12), 
              bg="#2196F3", fg="white", padx=20, pady=10).pack(pady=5)
    
    tk.Button(button_frame, text="🖥️ 尝试完整GUI", 
              command=try_full_gui, font=("Arial", 12), 
              bg="#FF9800", fg="white", padx=20, pady=10).pack(pady=5)
    
    # 底部说明
    bottom_text = """
💡 如果完整GUI无法正常工作，建议使用演示或命令行方式
📊 批量回测会自动测试多种参数组合并推荐最佳配置
    """
    bottom_label = tk.Label(root, text=bottom_text, font=("Arial", 10), 
                           fg="gray", justify="center")
    bottom_label.pack(pady=20)
    
    root.mainloop()

def main():
    """主函数"""
    print("🚀 启动简化版GUI界面...")
    print("📊 批量回测功能已就绪！")
    print("🎯 如果完整GUI有问题，可以使用此简化版本")
    print("=" * 50)
    
    try:
        simple_gui()
    except Exception as e:
        print(f"❌ GUI启动失败: {str(e)}")
        print("\n🔄 尝试使用命令行演示:")
        print("python quick_batch_demo.py")

if __name__ == "__main__":
    main() 