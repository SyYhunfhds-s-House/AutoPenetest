from abc import ABC, abstractmethod
from typing import Any, Optional, Literal
from base64 import b64encode
from functools import lru_cache
from pathlib import Path
import json
import pyarrow as pa
import pyarrow.parquet as pq

@lru_cache(maxsize=None)
def find_project_root(start: Optional[Path] = None) -> Optional[Path]:
    """
    根据 .gitignore 寻找项目根目录。
    :param start: 起始目录，默认 Path.cwd()
    :return: 含 .gitignore 的目录 Path，或 None
    """
    start = start or Path.cwd()
    for path in (start, *start.parents):   # 当前目录 + 所有上层目录
        if (path / '.gitignore').is_file():
            return path
    return None

TAMP_DIR = 'temp'
if find_project_root() is not None:
    TAMP_DIR = find_project_root() / TAMP_DIR 
    # 这里会有蜜汁语法报错，不需要理会
TAMP_DIR = Path(TAMP_DIR)
TAMP_DIR.mkdir(exist_ok=True)

# 资产扫描器，自定义增加扫描域
class AssetScanner(ABC):
    pass

def get_query_string(fields: list, query_params: dict):
    """
    生成查询字符串。

    Args:
        fields (list): 需要包含在查询字符串中的字段列表。
        query_params (dict): 查询参数，字典的键表示字段名，值表示对应的值。

    Returns:
        bytes: 生成的查询字符串的Base64编码字节串。

    Raises:
        无

    """
    # 检查fields是否与query_params的键有交集，若有交集
    # 则交集部分的键的值，与其键按如下格式进行合成：f'{key}="{value}"'
    # 所有这些合成字符串再使用AND进行连接，最后返回一个完整的查询字符串
    if not fields or not query_params:
        return b64encode("".encode())
    query_strings = []
    for key, value in query_params.items():
        if key in fields:
            query_strings.append(f'{key}="{value}"')
    return b64encode(" && ".join(query_strings).encode())

def assets_filter(project_name:str | Path, res: dict | str, fields: list):
    """
    清洗资产数据并临时缓存为Parquet文件。

    Args:
        project_name (str | Path): 项目名称或路径，用于创建临时缓存目录。
        res (dict | str): 资产数据，字典或JSON字符串格式，需包含'results'键。
        fields (list): 需要保留的字段列表。

    Returns:
        Path: Parquet文件的路径。
        None: 如果数据格式错误或res['error']为True。

    处理流程：
        1. 检查res类型并转换为dict。
        2. 若res['error']为True或格式不符则返回None。
        3. 按fields清洗数据，生成资产列表。
        4. 将资产列表保存为Parquet文件，路径为项目临时目录下。
    """
    # 若res['error']为True，则返回None
    if isinstance(res, str):
        res = json.loads(res)
    if not isinstance(res, dict):
        return None # 如果res在强制转化缺省处理后仍然不是dict类型，则返回None
    if res.get('error'):
        return None
    
    global TAMP_DIR
    TAMP_DIR = TAMP_DIR / Path(project_name)
    TAMP_DIR.mkdir(exist_ok=True)
    
    raw_assets = res.get('results', []).copy()
    del res
    assets = [
        dict(zip(fields, asset))
        for asset in raw_assets
    ]
    table = pa.table({field: [asset.get(field) for asset in assets] for field in fields})
    # 给表格增加一个列"is_alive" # 默认值为True
    table = table.append_column('is_alive', pa.array([True] * len(table)))
    # 对表格按link列进行去重
    _df = table.to_pandas()
    _df = _df.drop_duplicates(subset=['link'])
    table = pa.Table.from_pandas(_df)
    del _df
    TAMP_DIR = TAMP_DIR / f"raw_assets.parquet"
    pq.write_table(table, TAMP_DIR)

    return TAMP_DIR

if __name__ == '__main__':
    left = ['1', '2', '3']
    right = [1, 2, 3]
    # 将两个列表按顺序分别打包成键值对的键和值，然后转换成字典
    print(dict(zip(left, right)))

