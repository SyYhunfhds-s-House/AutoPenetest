from sympy import im
from utils import *
import argparse
import httpx
# 导入pa和pq
import pyarrow as pa
import pyarrow.parquet as pq

config = load_config()

# TODO 根据main函数编写命令行参数
def get_argparser():
    pass

def check_args(args: argparse.Namespace):
    """
    检查命令行参数的有效性。

    Args:
        args (argparse.Namespace): 命令行参数对象。

    Returns:
        bool: 如果参数有效返回True，否则返回False。
    """
    # TODO 实现参数检查逻辑
    return True

# TODO 编写程序主入口
# 程序主入口
def main(
    project_name: str, # 项目名称
    scan_settings: dict, # 扫描设置
    asset_params: dict, # 资产查询(对应fofa语法)参数
    # 直接把argparse的参数打包传进来
):
    
    size = scan_settings.get('size', 100)
    page = scan_settings.get('page', 1)
    timeout = scan_settings.get('timeout', 10)
    
    cache_parquet_path = asset_query_fofa(
        project_name=project_name,
        query_params=asset_params,
        size=size,
        page=page,
        timeout=timeout
    )
    
    return cache_parquet_path

if __name__ == "__main__":
    project_name = "default_project"
    asset_params = {
        'domain': 'baidu.com',
        'port': '443',
        'server': 'nginx'
    }
    cache_parquet_path = main(
        project_name=project_name,
        scan_settings={},
        asset_params=asset_params
    )
    print(f"资产查询结果已缓存到: {cache_parquet_path}")
    table = pq.read_table(cache_parquet_path)
    print(table[:10])