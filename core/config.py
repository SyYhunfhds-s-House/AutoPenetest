# 向上逐级检索，通过.gitignore定位项目根目录
from pathlib import Path
from typing import Optional
from functools import lru_cache
from yaml import safe_load

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

@lru_cache
def load_config(config_filename="config.yml"):
    project_root = find_project_root()
    if project_root is None:
        raise RuntimeError("Could not locate project root")
    config_filepath = project_root / config_filename
    try:
        with open(config_filepath, 'r') as f:
            res = safe_load(f)
            return res
    except FileNotFoundError:
        raise RuntimeError("Config file not found")
    
    if res is None:
        raise RuntimeError("Config file is empty")


# 示例
if __name__ == "__main__":
    root = find_project_root()
    print(root)
    
    from rich.console import Console
    console = Console()
    config = load_config()
    console.print(config)
