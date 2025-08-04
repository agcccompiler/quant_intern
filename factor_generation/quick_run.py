#!/usr/bin/env python3
"""
DolphinDB 脚本快速运行工具
用法: python quick_run.py <脚本路径> [参数JSON文件]
"""

import sys
import json
from pathlib import Path
from dolphindb import DolphinDBScriptProcessor


def main():
    if len(sys.argv) < 2:
        print("用法: python quick_run.py <脚本路径> [参数JSON文件]")
        print("\n示例:")
        print("  python quick_run.py ../dolphindb_factor/crowd_factor.dos")
        print("  python quick_run.py ../dolphindb_factor/crowd_factor.dos params.json")
        sys.exit(1)
    
    script_path = sys.argv[1]
    params_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 检查脚本文件是否存在
    if not Path(script_path).exists():
        print(f"错误: 脚本文件 '{script_path}' 不存在")
        sys.exit(1)
    
    # 创建处理器
    processor = DolphinDBScriptProcessor(script_path)
    
    print(f"\n正在处理脚本: {script_path}")
    print("=" * 60)
    
    # 显示需要的参数
    required_params = processor.get_required_parameters()
    print(f"\n需要的参数: {', '.join(required_params)}")
    
    # 加载或输入参数
    if params_file and Path(params_file).exists():
        # 从文件加载参数
        print(f"\n从文件加载参数: {params_file}")
        processor.load_parameters(params_file)
    else:
        # 交互式输入参数
        print("\n请输入参数值:")
        print("-" * 40)
        processor.set_parameters_interactive()
        
        # 询问是否保存参数
        save = input("\n是否保存参数到文件? (y/n): ").lower()
        if save == 'y':
            filename = input("输入保存文件名 (默认: params.json): ") or "params.json"
            processor.save_parameters(filename)
    
    # 显示当前参数
    print("\n当前参数值:")
    print("-" * 40)
    for param, value in processor.parameters.items():
        print(f"  {param}: {value}")
    
    # 询问是否查看渲染后的脚本
    preview = input("\n是否预览渲染后的脚本? (y/n): ").lower()
    if preview == 'y':
        rendered = processor.render_script()
        print("\n渲染后的脚本:")
        print("=" * 60)
        print(rendered)
        print("=" * 60)
    
    # 询问是否保存渲染后的脚本
    save_rendered = input("\n是否保存渲染后的脚本? (y/n): ").lower()
    if save_rendered == 'y':
        base_path = Path(script_path)
        output_path = base_path.parent / f"{base_path.stem}_rendered{base_path.suffix}"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(processor.render_script())
        print(f"渲染后的脚本已保存到: {output_path}")
    
    # 询问是否执行脚本
    execute = input("\n是否执行脚本? (需要 DolphinDB 服务器运行) (y/n): ").lower()
    if execute == 'y':
        # 获取连接参数
        print("\nDolphinDB 连接参数:")
        host = input("  服务器地址 (默认: localhost): ") or "localhost"
        port = input("  端口 (默认: 8848): ") or "8848"
        username = input("  用户名 (默认: admin): ") or "admin"
        password = input("  密码 (默认: 123456): ") or "123456"
        
        # 更新连接参数
        processor.host = host
        processor.port = int(port)
        processor.username = username
        processor.password = password
        
        try:
            print("\n正在执行脚本...")
            result = processor.execute_script()
            print(f"\n执行成功! 结果类型: {type(result)}")
            if result is not None:
                print(f"结果预览: {str(result)[:200]}...")
        except Exception as e:
            print(f"\n执行失败: {e}")
        finally:
            processor.disconnect()
    
    print("\n处理完成!")


if __name__ == "__main__":
    main()