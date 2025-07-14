from core import *

import requests
import json

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
    print(params)
    res = requests.get(
        url=f'{_api}{_endpoint}',
        params=params,
    )
    list_res = json.loads(res.text)
    from rich.console import Console
    console = Console()
    console.print(list_res)
    
if __name__ == '__main__':
    test_query({
        'domain': 'baidu.com'
    })