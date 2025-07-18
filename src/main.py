from pathlib import Path
from utils import *
from utils import _basic_generate_nuclei_command # 为了过类型检查
import argparse
import httpx
# 导入pa和pq
import pyarrow as pa
import pyarrow.parquet as pq
# 导入终端文本样式
from colorama import init, Fore, Back, Style
init(autoreset=True)

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
    # 导入fofa进行资产扫描
    cache_parquet_path = asset_query_fofa(
        project_name=project_name,
        query_params=asset_params,
        size=size,
        page=page,
        timeout=timeout
    )
    logger.info(f"{Fore.GREEN}资产查询结果已缓存到: {cache_parquet_path}")
    # 导入httpx进行资产探活
    raw_assets = pq.read_table(cache_parquet_path).to_pandas()
    raw_urls = raw_assets['link'].tolist()
    alive_table = alive_check_batch(
        project_name=project_name,
        urls=raw_urls,
        # max_workers=config['thread']['max'],
        # filter_status_code=config['filter']['status_code']
        # 上面两个配置都在config.yml里写好了
    ) # 返回一个pyarrow的Table对象
    logger.info(f'{Fore.GREEN}资产探活完成')
    # 合并探活结果和原始资产数据
    print(type(alive_table), type(raw_assets))
    alive_assets = merge_tables(
        small_table=alive_table, big_table=raw_assets
        )
    logger.info(f"{Fore.GREEN}已合并探活结果和原始资产数据")
    
    # 根据is_alive列的布尔值删去无法访问的资产的行
    if isinstance(alive_assets, pa.Table):
        # 转换为pandas DataFrame进行过滤
        alive_df = alive_assets.to_pandas()
        alive_df = alive_df[alive_df['is_alive']].reset_index(drop=True)
        alive_assets = pa.Table.from_pandas(alive_df)
        del alive_df
    else:
        alive_assets = alive_assets[alive_assets['is_alive']].reset_index(drop=True)
    
    logger.info(f"{Fore.GREEN}已过滤不活跃的资产")
    
    # 保存探活结果到本地
    cache_dir = Path(cache_parquet_path).parent
    alive_assets_path = cache_dir / f"alive_assets.parquet"
    pq.write_table(alive_assets, alive_assets_path)
    logger.debug(f"{Fore.GREEN}探活结果已缓存到: {alive_assets_path}")
    
    nuclei_command = _basic_generate_nuclei_command(
        project_name=project_name,
        specified_template_path=config['nuclei']['template_dir'],
        urls=alive_assets['link'].to_pylist(),
        severity=config['nuclei']['severity']
    )
    logger.debug(f'{Fore.GREEN}生成Nuclei命令行指令成功')
    
    print(f"{Fore.CYAN}生成的Nuclei命令行指令: \n{nuclei_command}")
    return alive_assets

if __name__ == "__main__":
    project_name = "default_project"
    scan_settings = {
        'timeout': 30,
        'size': 10
    }
    asset_params = {
        'domain': 'baidu.com',
        'port': '443',
        'server': 'nginx'
    }
    cache_parquet = main(
        project_name=project_name,
        scan_settings=scan_settings,
        asset_params=asset_params
    )
    # print(cache_parquet[:10])