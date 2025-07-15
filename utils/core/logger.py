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
        with open(config_filepath, 'r', encoding='utf-8') as f:
            res = safe_load(f)
            return res
    except FileNotFoundError:
        raise RuntimeError("Config file not found")
    
    if res is None:
        raise RuntimeError("Config file is empty")
_config = load_config()

from loguru import logger

# 定义控制台记录器和文件记录器，其中log日志位于项目根目录的logs/路径下
@lru_cache
def setup_logger():
    """
    设置 loguru 日志器，控制台输出和文件输出，日志文件位于项目根目录 logs/ 目录下。
    """
    # 获取项目根目录
    root = find_project_root()
    if root is None:
        raise RuntimeError("Could not locate project root for logger setup")
    logs_dir = root / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "app.log"
    # 移除默认的 loguru 处理器
    logger.remove()
    # 控制台输出
    logger.add(lambda msg: print(msg, end=""), level=_config['log']['level'])
    # 文件输出
    logger.add(str(log_file), rotation="10 MB", retention="10 days", encoding="utf-8", level="INFO")
    return logger

# 初始化日志器
logger = setup_logger()