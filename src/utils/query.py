from core import *

import requests
import json

import pyarrow as pa
import pyarrow.parquet as pq

_config = load_config()

fofa_api = _config['api']['fofa']
fields = _config['fields']

_api = fofa_api['url']
_key = fofa_api['key']
_endpoint = fofa_api['endpoint']

def test_query(query_params: dict, size: int=10, page: int = 1):
    query_string = get_query_string(fields=fields, query_params=query_params)
    params = {
        'qbase64': query_string,
        'size': size,
        'page': page,
        'key': _key,
        'fields': ','.join(fields)
    }
    # print(params)
    res = requests.get(
        url=f'{_api}{_endpoint}',
        params=params,
    )
    dict_res = json.loads(res.text)
    # from rich.console import Console
    # console = Console()
    # console.print(dict_res)
    
    temp_dir = assets_filter(project_name='test', res=dict_res, fields=fields)
    filtered_assets = pq.read_table(temp_dir)
    # console.print(filtered_assets)

# 资产扫描模块
def asset_query_fofa(
    project_name: str, # 项目名称
                     query_params: dict, 
                     size: int=10, page: int = 1,
                     timeout: int = 10
                     ): 
    """
    使用FOFA API进行资产查询，并将结果临时缓存为Parquet文件。

    Args:
        project_name (str): 项目名称，用于区分缓存目录。
        query_params (dict): 查询参数，键值对形式。
        size (int, optional): 查询返回的资产数量，默认10。
        page (int, optional): 查询页码，默认1。
        timeout (int, optional): 请求超时时间（秒），默认10。

    Returns:
        Path: Parquet文件的路径，包含清洗后的资产数据。
        None: 查询或数据处理失败时返回None。

    处理流程：
        1. 构造查询字符串并请求FOFA API。
        2. 捕获异常并记录日志。
        3. 清洗返回数据并保存为Parquet文件。
        4. 返回Parquet文件路径。
    """
    query_string = get_query_string(fields=fields, query_params=query_params)
    params = {
        'qbase64': query_string,
        'size': size,
        'page': page,
        'key': _key,
        'fields': ','.join(fields)
    }
    logger.info(f"正在进行{project_name}的资产查询任务")
    logger.debug(f"查询参数为{query_params}, 返回值列表为{fields},查询条数为{size}")
    try:
        res = requests.get(
            url=f'{_api}{_endpoint}',
            params=params,
            timeout=timeout
        )
        dict_res = json.loads(res.text)
    except TimeoutError:
        logger.warning(("网络连接超时，请检查网络状况; 若单次查询数据过大，请适当减少查询数据或延长请求时间"))
        exit(1)
    except Exception as e:
        logger.error(e)
        exit(1)
    
    temp_filepath = assets_filter(project_name=project_name, res=dict_res, fields=fields)
    return temp_filepath
    
if __name__ == '__main__':
    from rich.console import Console
    console = Console()
    temp_dir = asset_query_fofa(
        'hello', {
            'domain': 'baidu.com'
        }
    )
    data = pq.read_table(temp_dir)
    print(type(data.select(['link'])))
    console.print(data.select(['link']))
    