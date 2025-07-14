from abc import ABC, abstractmethod
from typing import Any, Optional, Literal
from base64 import b64encode

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
    return b64encode(" AND ".join(query_strings).encode())