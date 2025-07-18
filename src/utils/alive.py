from .core import *
from .core import logger
from .query import _config, asset_query_fofa # 为了过类型检查
from .query import *
from tqdm import tqdm
import httpx
# 导入线程池
from concurrent.futures import ThreadPoolExecutor, as_completed
# 导入SSL证书验证异常
from ssl import SSLError, SSLCertVerificationError
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
from httpx import ConnectTimeout, ConnectError, ReadTimeout
# 导入必要的模块
from pathlib import Path
import json
from typing import Union, Any, Optional, Literal
import pyarrow as pa
import pyarrow.parquet as pq
# 导入终端颜色文字
from colorama import init, Fore, Back, Style
init(autoreset=True)


max_workers = _config['thread']['max']
filter_status_code: list[int] = _config['filter']['status_code']
# 全局禁用SSL验证报错
disable_warnings(InsecureRequestWarning)

# TODO 编写断点重新探活函数, 自动调用已有缓存的原始资产
pq_cache = _config['pq_cache']
pq_raw_assets_path = pq_cache[0]  # 原始资产数据缓存文件名
pq_alive_assets_path = pq_cache[1]  # 探活资产数据缓存文件
del pq_cache  # 删除pq_cache变量, 避免污染全局命名空间
basedir_temp = _config['basedir']['temp']  # 缓存文件的根路径

def _check_alive_assets_cache(
    project_name: str, # 项目名称
) -> Optional[pa.Table]:
    """
    检查活跃资产缓存是否存在。

    Args:
        project_name (str): 项目名称

    Returns:
        pyarrow.Table: 如果活跃资产缓存存在，则返回读取的活跃资产表；否则返回 None。

    """
    '''pq_raw_assets_path = Path(basedir_temp) / project_name / pq_raw_assets_path
    if not pq_raw_assets_path.exists():
        logger.error(f"{Fore.RED}原始资产缓存不存在, 请先执行原始资产查询")
        raise FileNotFoundError(f"{Fore.RED}{Style.BRIGHT}函数{_check_alive_assets_cache.__name__}为模块私有函数, 请勿直接调用")'''
    global pq_alive_assets_path
    pq_alive_assets_path = Path(basedir_temp) / project_name / pq_alive_assets_path
    if not pq_alive_assets_path.exists():
        return None
    # 如果存在, 则读取并返回
    alive_table = pq.read_table(pq_alive_assets_path)
    if alive_table is None or alive_table.num_rows == 0:
        logger.warning(f"{Fore.YELLOW}活跃资产缓存文件 {pq_alive_assets_path} 存在但条目为空")
        return None
    return alive_table

def alive_check(
    url: str,
    filter_status_code: list[int] = filter_status_code, # 过滤状态, 默认[200, 301, 302]
    # index: int = -1, # 任务序号, 备用, 默认-1
):
    logger.debug(f"{Fore.BLUE}正在检查URL: {url}")
    try:
        res = httpx.get(url=url)
    except SSLCertVerificationError:
        return url, False # 禁用了还能报错那只能放着不管了
    except ConnectTimeout as e:
        logger.warning(f'{Fore.YELLOW}{url}连接超时')
        return url, False
    except ConnectError as e:
        logger.warning(f'{Fore.YELLOW}{url}SSL证书验证失败')
        return url, False
    except ReadTimeout as e:
        logger.error(f"{Fore.YELLOW}{url}读取响应超时, 请忽略该url")
        return url, False
        
    if res.status_code in filter_status_code:
        return url, True
    return url, False

def get_alive_check(**new_params):
    # 将传入的参数合并到alive_check函数中，覆盖原有的默认值
    global alive_check
    pass

def alive_check_batch(
    project_name: str, # 项目名称
    urls: list[str],
    max_workers: int = max_workers,
    **extra_params,
    # filter_status_code: list[int] = [200, 301, 302], # 过滤状态, 默认[200, 301, 302]
) -> pa.Table:
    alive_res = {
        'link': urls,
        'is_alive': [True] * len(urls)  # 默认全部为True,
    }
    logger.info(f"{Fore.CYAN}正在扫描{urls[0]}等{len(urls)}个URL是否存活")
    
    cache_alive_assets = _check_alive_assets_cache(project_name=project_name)
    if cache_alive_assets is not None:
        logger.info(f"{Fore.GREEN}已从缓存中读取到活跃资产数据, 共{cache_alive_assets.num_rows}条")
        return cache_alive_assets
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = list(executor.map(alive_check, urls))
        # 使用map的副作用是阻塞主线程，确保所有任务全部完成才能到下面的for循环
        for url, is_alive in tqdm(futures, desc="Checking URLs", total=len(urls)):
            index = urls.index(url)
            alive_res['is_alive'][index] = is_alive
    
    logger.info(f"{Fore.GREEN}扫描完成, 存活的URL数量: {sum(alive_res['is_alive'])}")
    return pa.table(alive_res)

if __name__ == '__main__':
    urls = [
        "https://xiongzhang.baidu.com", 
        "https://vb6ske.smartapps.baidu.com",
        "https://console.vcp.baidu.com",
        "http://console.vcp.baidu.com",
        "https://finance.pae.baidu.com",
        "https://ada.baidu.com",
        "https://ai.baidu.com",
        "https://tiku.baidu.com",
        "http://list.video.baidu.com",
        "https://list.video.baidu.com"
        ]
    result = alive_check_batch(urls=urls)
    print(result)
    
    