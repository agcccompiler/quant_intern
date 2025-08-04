# DolphinDB 脚本动态参数处理系统

这个系统可以自动识别 DolphinDB 脚本中的参数，并提供方便的接口进行参数输入和脚本执行。

## 功能特点

- 🔍 自动识别脚本中的 `{parameter}` 格式参数
- ⌨️ 支持交互式参数输入
- 📄 支持从 JSON 文件加载/保存参数
- 🔄 实时渲染脚本，预览替换后的内容
- 🚀 直接执行渲染后的脚本（需要 DolphinDB 服务器）
- 💾 保存渲染后的脚本文件

## 文件说明

- `dolphindb.py` - 核心处理器类 `DolphinDBScriptProcessor`
- `quick_run.py` - 命令行快速运行工具
- `example_usage.py` - 各种使用示例
- `crowd_factor_params_template.json` - crowd_factor.dos 的参数模板

## 快速开始

### 1. 安装依赖

```bash
pip install dolphindb
```

### 2. 基本使用

```python
from dolphindb import DolphinDBScriptProcessor

# 创建处理器并加载脚本
processor = DolphinDBScriptProcessor("../dolphindb_factor/crowd_factor.dos")

# 查看需要的参数
print(processor.get_required_parameters())

# 设置参数
params = {
    "job_id": "test_001",
    "start_date": "2024.01.01",
    "end_date": "2024.01.31",
    "start_time": "09:30:00",
    "end_time": "15:00:00",
    "portion": 0.1,
    "bucket_seconds": 30,
    "number_of_data": 512
}
processor.set_parameters(params)

# 渲染脚本
rendered_script = processor.render_script()

# 执行脚本（需要 DolphinDB 服务器）
# result = processor.execute_script()
```

### 3. 使用命令行工具

交互式输入参数：
```bash
python quick_run.py ../dolphindb_factor/crowd_factor.dos
```

使用参数文件：
```bash
python quick_run.py ../dolphindb_factor/crowd_factor.dos crowd_factor_params_template.json
```

## 高级用法

### 交互式参数输入

```python
processor = DolphinDBScriptProcessor("script.dos")
processor.set_parameters_interactive()
```

### 保存和加载参数

```python
# 保存参数
processor.save_parameters("my_params.json")

# 加载参数
processor.load_parameters("my_params.json")
```

### 批量处理多个脚本

```python
scripts = [
    {"path": "script1.dos", "params": {...}},
    {"path": "script2.dos", "params": {...}},
]

for config in scripts:
    processor = DolphinDBScriptProcessor(config["path"])
    processor.set_parameters(config["params"])
    processor.execute_script()
```

### 自定义 DolphinDB 连接

```python
processor = DolphinDBScriptProcessor(
    script_path="script.dos",
    host="192.168.1.100",
    port=8848,
    username="admin",
    password="your_password"
)
```

## 参数格式说明

脚本中的参数使用 `{parameter_name}` 格式，例如：

```sql
select * from table 
where date between {start_date} : {end_date}
  and value > {threshold}
```

系统会自动识别 `start_date`、`end_date` 和 `threshold` 作为需要输入的参数。

## 注意事项

1. 参数值会根据类型自动处理：
   - 字符串会自动加引号
   - 数字会直接替换
   
2. 日期格式建议使用 DolphinDB 支持的格式，如 "2024.01.01"

3. 执行脚本需要确保 DolphinDB 服务器正在运行

## 示例脚本参数

crowd_factor.dos 需要的参数：
- `job_id` - 作业 ID
- `start_date` - 开始日期 (格式: YYYY.MM.DD)
- `end_date` - 结束日期 (格式: YYYY.MM.DD)
- `start_time` - 开始时间 (格式: HH:MM:SS)
- `end_time` - 结束时间 (格式: HH:MM:SS)
- `portion` - FFT 强信号占比 (0-1 之间的小数)
- `bucket_seconds` - 时间桶大小（秒）
- `number_of_data` - 数据长度