# getting factor using dolphindb scripts 

import re
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import dolphindb as ddb


class DolphinDBScriptProcessor:
    """
    DolphinDB 脚本处理器，用于动态捕获和处理脚本参数
    """
    
    def __init__(self, script_path: str = None, host: str = "localhost", 
                 port: int = 8848, username: str = "admin", password: str = "123456"):
        """
        初始化脚本处理器
        
        Args:
            script_path: DolphinDB 脚本文件路径
            host: DolphinDB 服务器地址
            port: DolphinDB 服务器端口
            username: 用户名
            password: 密码
        """
        self.script_path = script_path
        self.script_content = ""
        self.parameters = {}
        self.session = None
        
        # DolphinDB 连接参数
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
        if script_path:
            self.load_script(script_path)
    
    def connect_dolphindb(self):
        """连接到 DolphinDB 服务器"""
        if not self.session:
            self.session = ddb.session()
            self.session.connect(self.host, self.port, self.username, self.password)
        return self.session
    
    def disconnect(self):
        """断开 DolphinDB 连接"""
        if self.session:
            self.session.close()
            self.session = None
    
    def load_script(self, script_path: str):
        """
        加载 DolphinDB 脚本文件
        
        Args:
            script_path: 脚本文件路径
        """
        self.script_path = script_path
        with open(script_path, 'r', encoding='utf-8') as f:
            self.script_content = f.read()
        
        # 提取参数
        self.parameters = self.extract_parameters()
        
    def extract_parameters(self) -> Dict[str, Any]:
        """
        从脚本中提取所有 {parameter} 格式的参数
        
        Returns:
            参数字典，键为参数名，值为None（待用户输入）
        """
        # 使用正则表达式匹配所有 {parameter} 格式的参数
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, self.script_content)
        
        # 去重并创建参数字典
        parameters = {}
        for param in set(matches):
            parameters[param] = None
            
        return parameters
    
    def get_required_parameters(self) -> List[str]:
        """
        获取所有需要的参数列表
        
        Returns:
            参数名列表
        """
        return list(self.parameters.keys())
    
    def set_parameter(self, param_name: str, value: Any):
        """
        设置单个参数的值
        
        Args:
            param_name: 参数名
            value: 参数值
        """
        if param_name in self.parameters:
            self.parameters[param_name] = value
        else:
            raise ValueError(f"参数 '{param_name}' 不存在于脚本中")
    
    def set_parameters(self, params: Dict[str, Any]):
        """
        批量设置参数值
        
        Args:
            params: 参数字典
        """
        for key, value in params.items():
            self.set_parameter(key, value)
    
    def set_parameters_interactive(self):
        """
        交互式设置参数值
        """
        print(f"脚本 '{self.script_path}' 需要以下参数：")
        print("-" * 50)
        
        for param in self.get_required_parameters():
            while True:
                value = input(f"请输入参数 '{param}' 的值: ")
                if value:
                    # 尝试解析为数字
                    try:
                        if '.' in value:
                            self.parameters[param] = float(value)
                        else:
                            self.parameters[param] = int(value)
                    except ValueError:
                        # 如果不是数字，保持为字符串
                        self.parameters[param] = value
                    break
                else:
                    print("参数值不能为空，请重新输入")
    
    def validate_parameters(self) -> bool:
        """
        验证所有参数是否已设置
        
        Returns:
            True 如果所有参数都已设置，否则 False
        """
        missing_params = [k for k, v in self.parameters.items() if v is None]
        if missing_params:
            print(f"以下参数尚未设置: {', '.join(missing_params)}")
            return False
        return True
    
    def render_script(self) -> str:
        """
        使用参数值渲染脚本
        
        Returns:
            渲染后的脚本内容
        """
        if not self.validate_parameters():
            raise ValueError("存在未设置的参数")
        
        rendered_script = self.script_content
        for param, value in self.parameters.items():
            # 根据值的类型决定如何替换
            if isinstance(value, str):
                # 字符串需要加引号
                replacement = f'"{value}"'
            else:
                # 数字直接替换
                replacement = str(value)
            
            rendered_script = rendered_script.replace(f'{{{param}}}', replacement)
        
        return rendered_script
    
    def execute_script(self, save_rendered_script: bool = False, 
                      rendered_script_path: str = None) -> Any:
        """
        执行渲染后的脚本
        
        Args:
            save_rendered_script: 是否保存渲染后的脚本
            rendered_script_path: 渲染后脚本的保存路径
            
        Returns:
            脚本执行结果
        """
        rendered_script = self.render_script()
        
        # 保存渲染后的脚本（可选）
        if save_rendered_script:
            if not rendered_script_path:
                # 默认在原脚本旁边创建渲染后的版本
                base_path = Path(self.script_path)
                rendered_script_path = base_path.parent / f"{base_path.stem}_rendered{base_path.suffix}"
            
            with open(rendered_script_path, 'w', encoding='utf-8') as f:
                f.write(rendered_script)
            print(f"渲染后的脚本已保存到: {rendered_script_path}")
        
        # 连接并执行脚本
        session = self.connect_dolphindb()
        try:
            result = session.run(rendered_script)
            return result
        except Exception as e:
            print(f"脚本执行失败: {e}")
            raise
    
    def save_parameters(self, filepath: str):
        """
        保存参数到 JSON 文件
        
        Args:
            filepath: JSON 文件路径
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.parameters, f, indent=2, ensure_ascii=False)
        print(f"参数已保存到: {filepath}")
    
    def load_parameters(self, filepath: str):
        """
        从 JSON 文件加载参数
        
        Args:
            filepath: JSON 文件路径
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            params = json.load(f)
        self.set_parameters(params)
        print(f"参数已从 {filepath} 加载")
    
    def print_script_info(self):
        """打印脚本信息"""
        print(f"\n脚本路径: {self.script_path}")
        print(f"参数列表: {self.get_required_parameters()}")
        print("\n当前参数值:")
        for param, value in self.parameters.items():
            print(f"  {param}: {value}")


# 使用示例
if __name__ == "__main__":
    # 创建处理器实例
    processor = DolphinDBScriptProcessor()
    
    # 处理 crowd_factor.dos 脚本
    script_path = "dolphindb_factor/crowd_factor.dos"
    processor.load_script(script_path)
    
    # 打印脚本信息
    processor.print_script_info()
    
    # 方式1: 交互式输入参数
    # processor.set_parameters_interactive()
    
    # 方式2: 批量设置参数
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
    
    # 查看渲染后的脚本（不执行）
    # rendered = processor.render_script()
    # print("\n渲染后的脚本预览:")
    # print(rendered[:500] + "...")
    
    # 执行脚本（需要 DolphinDB 服务器运行）
    # try:
    #     result = processor.execute_script(save_rendered_script=True)
    #     print(f"脚本执行成功，结果: {result}")
    # except Exception as e:
    #     print(f"脚本执行失败: {e}")
    
    # 保存参数供后续使用
    # processor.save_parameters("factor_params.json")