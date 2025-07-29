#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子回测框架GUI启动脚本

简化的启动方式，避免导入和初始化问题
"""

import os
import sys

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

def main():
    """启动GUI界面"""
    try:
        print("🚀 正在启动因子回测框架GUI界面...")
        print("📊 批量回测功能已就绪！")
        print("🎯 请在界面中点击'批量回测'按钮测试多种参数组合")
        print("=" * 60)
        
        # 导入必要的模块
        from factor_backtest_framework.gui import FactorBacktestGUI
        
        # 创建并启动GUI
        app = FactorBacktestGUI()
        app.run()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保在正确的目录下运行此脚本")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("尝试其他启动方式...")
        sys.exit(1)

if __name__ == "__main__":
    main() 