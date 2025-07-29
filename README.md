# 因子回测框架 v2.0

> 现代化的量化因子回测框架 - 全新重构版

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/your-repo/factor-backtest-framework)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

## 🚀 框架特色

### 💡 全新架构设计
- **现代化配置管理**: 使用dataclass进行结构化配置
- **简洁的接口设计**: 专注核心功能，去除冗余复杂性
- **模块化组件**: 每个组件职责单一，易于理解和维护

### ⚡ 核心功能
- **DolphinDB高性能因子生成**: 支持参数化脚本执行
- **完整的评估指标体系**: IC/ICIR、分组收益、多空组合等
- **多种因子平滑方法**: 滚动均值、EMA、Z-score等  
- **精美的可视化图表**: 自动生成专业的分析图表
- **直观的GUI操作界面**: 无需编程即可完成回测

## 📦 快速安装

```bash
# 克隆项目
git clone https://github.com/your-repo/factor-backtest-framework.git
cd factor-backtest-framework

# 安装依赖
pip install -r requirements.txt

# 安装DolphinDB客户端（因子生成必需）
pip install dolphindb
```

## 🎯 快速开始

### 方法1: GUI界面（推荐新手）

```python
from factor_backtest_framework import quick_start_gui
quick_start_gui()
```

### 方法2: 编程接口

```python
from factor_backtest_framework import FactorBacktestPipeline

# 创建流水线
pipeline = FactorBacktestPipeline()

# 运行完整回测 (支持多种压缩格式)
results = pipeline.run_full_pipeline('your_returns.csv.xz')  # 支持 .csv, .csv.xz, .csv.gz, .zip

# 查看结果
print(f"ICIR: {results['evaluation_results']['ICIR']:.4f}")
```

### 方法3: 命令行

```bash
# 支持压缩文件格式
python -m factor_backtest_framework.main --return-file returns.csv.xz
python -m factor_backtest_framework.main --return-file returns.csv.gz
python -m factor_backtest_framework.main --return-file returns.zip
```

## 🏗️ 核心组件

### 1. 因子生成器 (FactorGenerator)
```python
from factor_backtest_framework import FactorGenerator
from factor_backtest_framework.config.config import DolphinDBConfig

# 配置DolphinDB连接
config = DolphinDBConfig(host='localhost', port=8848)
generator = FactorGenerator(config)

# 生成因子
params = {
    'start_date': '2019.03.20',
    'end_date': '2019.06.30', 
    'seconds': 30,
    'portion': 0.2
}

factor_df = generator.generate('script.dos', params, 'output.csv')
```

### 2. 因子评估器 (FactorEvaluator)
```python
from factor_backtest_framework import FactorEvaluator
from factor_backtest_framework.config.config import EvaluationConfig

# 配置评估参数
config = EvaluationConfig(group_num=10, long_percentile=90)
evaluator = FactorEvaluator(config)

# 执行评估
results = evaluator.evaluate(factor_df, returns_df)

# 创建图表
fig = evaluator.create_chart(results)
```

### 3. 因子平滑器 (FactorSmoother)
```python
from factor_backtest_framework import FactorSmoother

# 创建平滑器
smoother = FactorSmoother()

# 应用平滑
smoothed_df = smoother.rolling_mean(factor_df, window=5)

# 多种方法组合
methods = {
    'rolling_mean': {'window': 5},
    'zscore': {'window': 20}
}
result = smoother.smooth(factor_df, methods)
```

## ⚙️ 配置管理

### 创建自定义配置
```python
from factor_backtest_framework.config.config import FrameworkConfig

config = FrameworkConfig.create(
    dolphindb={
        'host': '10.80.87.122',
        'port': 8848,
        'username': 'your_user',
        'password': 'your_password'
    },
    factor={
        'start_date': '2019.03.20',
        'end_date': '2024.06.30',
        'seconds': 30,
        'portion': 0.2
    },
    evaluation={
        'group_num': 10,
        'long_percentile': 90,
        'short_percentile': 10
    },
    smoothing={
        'enable': True,
        'rolling_window': 5,
        'methods': {
            'rolling_mean': {'window': 5},
            'ema': {'alpha': 0.3}
        }
    }
)
```

## 📁 数据文件支持

### 支持的文件格式
框架支持多种数据文件格式，包括压缩文件：

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| 标准CSV | `.csv` | 普通CSV文件 |
| GZIP压缩 | `.csv.gz` | GZIP压缩的CSV文件 |
| XZ压缩 | `.csv.xz` | XZ压缩的CSV文件（推荐） |
| ZIP压缩 | `.zip` | ZIP压缩包中的CSV文件 |

### 使用示例
```python
# 自动检测并加载不同格式的文件
pipeline = FactorBacktestPipeline()

# 标准CSV
results1 = pipeline.run_full_pipeline('returns.csv')

# XZ压缩文件（推荐，压缩比高）
results2 = pipeline.run_full_pipeline('returns.csv.xz')  

# GZIP压缩文件  
results3 = pipeline.run_full_pipeline('returns.csv.gz')

# ZIP压缩文件
results4 = pipeline.run_full_pipeline('returns.zip')
```

### 编码支持
框架会自动尝试以下编码格式：
- UTF-8 (默认)
- GBK (中文支持)
- GB2312
- Latin1

## 📊 输出结果

### 评估指标
- **ICIR**: 信息比率
- **平均Rank IC**: 平均排序相关系数
- **分组收益率**: 10组年化收益率
- **多空收益**: 多空组合年化收益
- **超额收益**: 多头相对基准的超额收益
- **换手率**: 投资组合换手率

### 可视化图表
- 分组年化收益率柱状图
- 多头超额净值曲线
- 多空净值走势
- 累计Rank IC趋势

### 结果文件
```
results/
├── data/
│   ├── evaluation_results_20240315_143022.csv
│   ├── group_returns_20240315_143022.csv
│   ├── ic_series_20240315_143022.csv
│   ├── smoothed_factor_20240315_143022.csv
│   └── raw_factor_20240315_143022.csv
└── figures/
    └── factor_analysis_20240315_143022.png
```

## 🎨 DolphinDB脚本格式

框架支持参数化的DolphinDB脚本，使用 `{参数名}` 格式：

```dolphindb
// factor_script.dos
def calc_my_factor(data, period) {
    // 因子计算逻辑
    return factor_values
}

def factor_job() {
    tab = loadTable('dfs://database', "table")
    
    result = select calc_my_factor(price, {seconds}) as factor
             from tab 
             where date(datetime) between {start_date} : {end_date}
             and time(datetime) between {start_time} : {end_time}
             group by code, date(datetime) as day_date
             order by day_date, code
    
    return result
}

// 执行并返回结果
job_id = submitJobEx("{job_id}", "factor_calc", 4, 128, factor_job)
result = getJobReturn(job_id, true)
result
```

支持的参数：
- `{start_date}` / `{end_date}`: 开始/结束日期
- `{start_time}` / `{end_time}`: 开始/结束时间  
- `{seconds}`: 时间桶大小
- `{portion}`: 信号占比
- `{job_id}`: 作业ID

## 📚 使用示例

查看 `example_usage.py` 获取完整的使用示例：

```bash
python example_usage.py
```

示例包括：
1. GUI界面使用
2. 编程接口使用
3. 单独使用各组件
4. 配置管理
5. 数据格式处理
6. 错误处理
7. 命令行使用

## 🔧 系统要求

- **Python**: 3.7+
- **操作系统**: Windows/macOS/Linux
- **内存**: 建议4GB+
- **DolphinDB**: 因子生成需要连接DolphinDB服务器

### 依赖包
```
pandas >= 1.3.0
numpy >= 1.20.0
matplotlib >= 3.3.0
dolphindb >= 1.30.0
```

## 📈 性能特点

- **高效数据处理**: 基于pandas优化的数据操作
- **内存友好**: 流式处理大数据集
- **并行计算**: 支持多核CPU加速
- **缓存机制**: 智能缓存中间结果

## 🛠️ 开发指南

### 项目结构
```
factor_backtest_framework/
├── config/                 # 配置管理
│   └── config.py
├── core/                   # 核心组件
│   ├── factor_generator.py
│   ├── factor_evaluator.py
│   └── factor_smoother.py
├── main.py                 # 主流水线
├── gui.py                  # GUI界面
├── example_usage.py        # 使用示例
└── README.md              # 文档
```

### 扩展开发
```python
# 自定义评估指标
class CustomEvaluator(FactorEvaluator):
    def custom_metric(self, factor_df, returns_df):
        # 自定义计算逻辑
        return metric_value

# 自定义平滑方法  
class CustomSmoother(FactorSmoother):
    def custom_smooth(self, factor_df, **params):
        # 自定义平滑逻辑
        return smoothed_df
```

## 📄 版本历史

### v2.0.0 (2024-03-15)
- 🔥 **全新重构**: 现代化架构设计
- ✨ **新特性**: dataclass配置管理
- 🚀 **性能优化**: 简化核心组件
- 🎨 **界面升级**: 更直观的GUI设计
- 📚 **文档完善**: 全新的使用指南

### v1.0.0 (2024-01-20)
- 🎉 初始版本发布
- 基础因子回测功能
- GUI界面支持

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📞 联系我们

- **作者**: JinchengGuo
- **邮箱**: your.email@example.com
- **项目地址**: https://github.com/your-repo/factor-backtest-framework

## 📜 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star！⭐**

Made with ❤️ by JinchengGuo

</div> 