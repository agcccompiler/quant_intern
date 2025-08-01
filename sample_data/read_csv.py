import pandas as pd
import os

def read_csv_head1000(input_path):
    # 判断文件是否存在
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    # 读取前1000行
    try:
        df = pd.read_csv(input_path, nrows=1000)
    except Exception as e:
        raise RuntimeError(f"读取文件失败: {e}")

    return df
    print(f"已将前1000行保存到: {output_path}")

if __name__ == "__main__":
    factor_path = "data/JinchengGuo_20190320_20200320_0p1_30_093000000_145700000_801740.csv"
    result_factor = read_csv_head1000(factor_path)
    print(result_factor)
    print(result_factor.dtypes)  # 输出result_data的表结构（各列名及类型）

    return_path = "data/return_allA_T2_T1_vwap_rq_20100101_20241231.csv.xz"
    result_return = read_csv_head1000(return_path)
    print(result_return)
    print(result_return.dtypes)  # 输出result_data的表结构（各列名及类型）

