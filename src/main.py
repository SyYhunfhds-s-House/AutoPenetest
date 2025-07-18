from pathlib import Path

from pandas import DataFrame
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
    argpaerser = argparse.ArgumentParser()
    # 设置项目名称
    argpaerser.add_argument(
        '-p', '--project', type=str, required=True, help='Project name | 项目名称'
    )
    # 类fofa查询语法 # 由于架构问题, 下面的参数都只能指定一个
    # 查询域名 domain
    argpaerser.add_argument(
        '-d', '--domain', type=str, default='', help='Domain to search(support only one domain) | 指定搜索域名(单次运行只可以搜索一个域名) \
            e.g.: --domain example.com'
    )
    # 查询服务器类型 server
    argpaerser.add_argument(
        '-s', '--server', type=str, default='', help='Server type to search | 指定搜索服务器类型 \
            e.g.: --server nginx'
    )
    # 查询资产端口
    argpaerser.add_argument(
        '-po', '--port', type=str, default="80,443", help='Port to search | 指定搜索端口(多个端口请使用逗号分隔) \
            e.g.: --port 443'
    )
    
    # fofa查询参数
    # fofa查询超时时间 timeout # 超出这个时间即视为网络连接不稳定导致的掉线
    argpaerser.add_argument(
        '--timeout', type=int, default=30, help='Timeout for fofa query | fofa查询超时时间 \ ')
    # fofa查询条数 size
    argpaerser.add_argument(
        '-si', '--size', type=int, default=100, help='Size of the result set | fofa查询条数 \ '
    )
    
    # nuclei运行参数
    # 模板主路径 # 没有完整包含nuclei的所有参数，所以有需要的话需要自己改一下模板路径
    argpaerser.add_argument(
        # 使用template_dir而不是template是为了和后面的路径拼接配合
        '-t', '--template-dir', type=str, default='', help='Template path | 指定模板路径 \
            e.g.: --template-dir /home/user/nuclei-templates'
            # 显式指定名称
    )
    '''# 导出的文件类型, 允许值范围为["markdown-export", "json-export"]
    # 配合nuclei设置
    argpaerser.add_argument(
        '-e', '--export', type=str, choices=["markdown-export", "json-export"], default="markdown-export", help='Export format | 指定导出格式 \
            e.g.: --export markdown-export'
    )'''
    return argpaerser

# TODO 检查并清洗参数
def check_and_filter_args(args: argparse.Namespace):
    
    # TODO 实现参数检查逻辑
    project_name = args.project

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
    template_dir = scan_settings.get('template_dir')
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
    if len(raw_urls) == 0:
        logger.error(f"{Fore.RED}未发现可用资产, 可能是网络连接异常")
        exit(1)
    
    alive_table = alive_check_batch(
        project_name=project_name,
        urls=raw_urls,
        # max_workers=config['thread']['max'],
        # filter_status_code=config['filter']['status_code']
        # 上面两个配置都在config.yml里写好了
    ) # 返回一个pyarrow的Table对象
    logger.info(f'{Fore.GREEN}资产探活完成')
    
    '''
    下面的这一坨try-catch是一开始没考虑到缓存读取的问题, 所以加了try-catch
    现在的逻辑是: 如果alive_table是从本地读取的缓存, 那么在下面的数据处理中必然报错
    报错之后catch异常，然后对去活失败的结果进行去除空行的处理
    '''
    
    try:
        # 合并探活结果和原始资产数据
        alive_assets = merge_tables(
            small_table=alive_table, big_table=raw_assets
            )
        # print(type(alive_assets))

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

            '''
            这一通操作下来我都有点分不清alive_assets是pa.Table还是DataFrame了
            print看了一下，一直都是pa.Table
            '''
        # print(type(alive_assets))    
        logger.info(f"{Fore.GREEN}已过滤不活跃的资产")
    
        # 保存探活结果到本地
        cache_dir = Path(cache_parquet_path).parent
        alive_assets_path = cache_dir / f"alive_assets.parquet"
        pq.write_table(alive_assets, alive_assets_path)
        logger.debug(f"{Fore.GREEN}探活结果已缓存到: {alive_assets_path}")
    except Exception as e:
        logger.error(f"{Fore.RED}处理探活结果时发生错误: {e}")
        logger.debug(f"{Fore.YELLOW}探活结果可能是从本地读取的缓存, 无需进行数据处理")
        # print(type(alive_assets))
        # 去除表格的null行
        alive_assets_df : DataFrame = alive_assets.to_pandas()
        alive_assets_df = alive_assets_df.dropna(how='all').reset_index(drop=True)
        alive_assets = pa.Table.from_pandas(alive_assets_df)
        logger.debug(f"{Fore.GREEN}已去除表格中的空行")
        logger.info(f'{Fore.GREEN}已合并资产结果; 已过滤不活跃的资产')
        del alive_assets_df
        
        
    nuclei_command = _basic_generate_nuclei_command(
        project_name=project_name,
        specified_template_path=template_dir,
        urls=alive_assets['link'].to_pylist(),
        severity=config['nuclei']['severity']
    )
    logger.debug(f'{Fore.GREEN}生成Nuclei命令行指令成功')
    
    print(f"{Fore.CYAN}生成的Nuclei命令行指令: \n{nuclei_command}")
    return nuclei_command

def _test_main():
    config = load_config()
    project_name = "default_project123"
    scan_settings = {
        'timeout': 30,
        'size': 10,
        'template_dir': config['nuclei']['template_dir']
    }
    asset_params = {
        'domain': ['google.com'],
        'port': '443',
        'server': 'nginx'
    }
    cache_parquet = main(
        project_name=project_name,
        scan_settings=scan_settings,
        asset_params=asset_params
    )

if __name__ == "__main__":
    _test_main()
    '''args = get_argparser().parse_args()
    from rich.console import Console
    console = Console()
    console.print(args)'''
    
    # print(cache_parquet[:10])