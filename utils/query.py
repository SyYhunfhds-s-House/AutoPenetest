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
    query_string = get_query_string(fields=fields, query_params=query_params)
    params = {
        'qbase64': query_string,
        'size': size,
        'page': page,
        'key': _key,
        'fields': ','.join(fields)
    }
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
    test_query({
        'domain': 'baidu.com'
    })
    