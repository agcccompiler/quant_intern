# core/factor_generator.py
import subprocess
import os
import tempfile
import dolphindb as ddb
import pandas as pd

class FactorGenerator:
    def __init__(self, script_path: str, output_path: str, params: dict):
        self.script_path = script_path
        self.output_path = output_path
        self.params = params

    def generate_factor(self):
        # 读取 DolphinDB 脚本
        with open(self.script_path, 'r', encoding='utf-8') as f:
            script = f.read()

        # 替换参数
        for key, value in self.params.items():
            script = script.replace(f'{{{key}}}', str(value))

        # 创建临时脚本文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dos', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(script)
            tmp_script_path = tmp_file.name

        try:
            # 连接DolphinDB服务器
            s = ddb.session()
            try:
                s.connect(
                    "10.80.87.122", 
                    8848, 
                    "quant_read", 
                    "quant_123456"
                )
            except Exception as e:
                print("连接DolphinDB服务器时发生错误：", e)
                raise

            # 读取脚本内容
            with open(tmp_script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            # 执行脚本
            try:
                result = s.run(script_content)
            except Exception as e:
                print(f"在DolphinDB服务器上执行脚本时出错: {e}")
                raise

            # 保存输出结果（假设返回DataFrame或可转为csv）
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            if isinstance(result, pd.DataFrame):
                result.to_csv(self.output_path, index=False)
            else: 
                # 若不是DataFrame，直接保存为文本
                with open(self.output_path, 'w', encoding='utf-8') as f:
                    f.write(str(result)) 

            print(f"因子生成完成，结果保存至: {self.output_path}")
        except Exception as e:
            print(f"执行 DolphinDB 脚本时出错: {e}")
            raise
        finally:
            # 清理临时文件
            if os.path.exists(tmp_script_path):
                os.remove(tmp_script_path)
