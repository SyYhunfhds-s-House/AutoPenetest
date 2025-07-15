from query import _config, asset_query_fofa # 为了过类型检查
from query import *
from tqdm import tqdm
import httpx
# 导入线程池
from concurrent.futures import ThreadPoolExecutor, as_completed
# 导入SSL证书验证异常
from ssl import SSLError, SSLCertVerificationError
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
# 导入必要的模块
from pathlib import Path
import json
from typing import Union, Any, Optional, Literal
import pyarrow as pa
import pyarrow.parquet as pq


max_workers = _config['thread']['max']
# 全局禁用SSL验证报错
disable_warnings(InsecureRequestWarning)

# TODO 联动query.py，编写资产探活模块
def alive_check(
    url: str,
    filter_status_code: list = [200, 301, 302], # 过滤状态, 默认[200, 301, 302]
    index: int = -1, # 任务序号, 备用, 默认-1
):
    try:
        res = httpx.get(url=url)
    except SSLCertVerificationError:
        return index, False # 禁用了还能报错那只能放着不管了
    
    if res.status_code in filter_status_code:
        return index, True
    return index, False

# TODO 整合单元函数，使用线程池分批进行扫描
def alive_check_batch(
    project_temp: str | Path, # 缓存文件路径
    urls: list[str],
    max_workers: int = max_workers,
):
    pass
