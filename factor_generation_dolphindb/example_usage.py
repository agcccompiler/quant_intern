"""
DolphinDB 脚本处理器使用示例
"""

from dolphindb import DolphinDBScriptProcessor


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===\n")
    
    # 创建处理器并加载脚本
    processor = DolphinDBScriptProcessor("../dolphindb_factor/crowd_factor.dos")
    
    # 显示脚本信息
    processor.print_script_info()
    
    # 设置参数
    params = {
        "job_id": "factor_test_001",
        "start_date": "2024.01.01",
        "end_date": "2024.01.31",
        "start_time": "09:30:00",
        "end_time": "15:00:00",
        "portion": 0.1,
        "bucket_seconds": 30,
        "number_of_data": 512
    }
    processor.set_parameters(params)
    
    # 查看渲染后的脚本
    rendered = processor.render_script()
    print("\n渲染后的脚本（前500字符）:")
    print(rendered[:500] + "...")


def example_interactive_input():
    """交互式输入示例"""
    print("\n=== 交互式输入示例 ===\n")
    
    processor = DolphinDBScriptProcessor("../dolphindb_factor/crowd_factor.dos")
    
    # 交互式输入参数
    processor.set_parameters_interactive()
    
    # 保存参数
    processor.save_parameters("crowd_factor_params.json")


def example_batch_processing():
    """批量处理多个脚本示例"""
    print("\n=== 批量处理示例 ===\n")
    
    # 假设有多个脚本和对应的参数
    scripts = [
        {
            "path": "../dolphindb_factor/crowd_factor.dos",
            "params": {
                "job_id": "batch_test_001",
                "start_date": "2024.01.01",
                "end_date": "2024.01.31",
                "start_time": "09:30:00",
                "end_time": "15:00:00",
                "portion": 0.1,
                "bucket_seconds": 30,
                "number_of_data": 512
            }
        },
        # 可以添加更多脚本
    ]
    
    for script_config in scripts:
        processor = DolphinDBScriptProcessor(script_config["path"])
        processor.set_parameters(script_config["params"])
        
        # 渲染并保存
        rendered = processor.render_script()
        output_path = f"rendered_{script_config['params']['job_id']}.dos"
        with open(output_path, 'w') as f:
            f.write(rendered)
        print(f"处理完成: {script_config['path']} -> {output_path}")


def example_parameter_validation():
    """参数验证示例"""
    print("\n=== 参数验证示例 ===\n")
    
    processor = DolphinDBScriptProcessor("../dolphindb_factor/crowd_factor.dos")
    
    # 只设置部分参数
    partial_params = {
        "job_id": "test_001",
        "start_date": "2024.01.01",
        # 故意缺少其他参数
    }
    processor.set_parameters(partial_params)
    
    # 尝试验证（会失败）
    if not processor.validate_parameters():
        print("参数不完整，需要设置所有必需参数")
        
        # 显示缺失的参数
        missing = [k for k, v in processor.parameters.items() if v is None]
        print(f"缺失的参数: {missing}")


def example_custom_script():
    """处理自定义脚本示例"""
    print("\n=== 自定义脚本示例 ===\n")
    
    # 创建一个简单的测试脚本
    test_script = """
    // 测试脚本
    def test_function() {
        start = {start_value}
        end = {end_value}
        step = {step_size}
        
        result = []
        for (i = start; i <= end; i += step) {
            result.append(i * {multiplier})
        }
        return result
    }
    
    // 执行函数
    output = test_function()
    """
    
    # 保存测试脚本
    with open("test_script.dos", 'w') as f:
        f.write(test_script)
    
    # 处理脚本
    processor = DolphinDBScriptProcessor("test_script.dos")
    processor.print_script_info()
    
    # 设置参数
    processor.set_parameters({
        "start_value": 1,
        "end_value": 10,
        "step_size": 2,
        "multiplier": 3
    })
    
    # 显示渲染结果
    print("\n渲染后的脚本:")
    print(processor.render_script())
    
    # 清理
    import os
    os.remove("test_script.dos")


if __name__ == "__main__":
    # 运行各种示例
    example_basic_usage()
    # example_interactive_input()  # 需要用户输入
    example_batch_processing()
    example_parameter_validation()
    example_custom_script()