from .core import logger, load_config
from pathlib import Path
from functools import lru_cache # 缓存函数结果以提高性能
from typing import Optional
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

'''
# 获取项目根目录
# 如果没有.gitignore文件，则无法定位项目根目录
project_root_path = find_project_root()
if project_root_path is None:
    logger.error("Could not locate project root")
    raise RuntimeError("Could not locate project root")
# 获取nuclei CLI参数配置文件路径
nuclei_cli_params_path = project_root_path / "nuclei_cli_params.yml"
if not nuclei_cli_params_path.exists():
    logger.error(f"Nuclei CLI parameters file {nuclei_cli_params_path} does not exist.")
    raise FileNotFoundError(f"Nuclei CLI parameters file {nuclei_cli_params_path} does not exist.")
# 读取nuclei CLI参数配置文件
with open(nuclei_cli_params_path, 'r', encoding='utf-8') as f:
    nuclei_cli_params = safe_load(f)
if nuclei_cli_params is None or not isinstance(nuclei_cli_params, dict) or nuclei_cli_params == {}:
    logger.error("Nuclei CLI parameters file is empty")
    raise RuntimeError("Nuclei CLI parameters file is empty")
'''
def _basic_generate_nuclei_command(
    project_name: str, # 输出路径
    specified_template_path: str = '', 
    urls: list = None,
    severity: list = None) -> str:
    """
    生成nuclei命令行指令
    :param project_name: 项目名称，用于输出路径
    :param specified_template_path: 指定的模板路径(如./nuclei-templates); 具体的子模板路径在配置文件中指定
    :param urls: 要扫描的URL列表
    :param severity: 指定的威胁等级
    """
    if urls is None:
        logger.error("URLs list cannot be None")
        raise ValueError("URLs list cannot be None")
    
    config = load_config()
    nuclei_config = config.get('toolkit', {}).get('nuclei', {})
    
    exe_path = nuclei_config.get('exe')
    template_dir = nuclei_config.get('template_dir')
    
    if not exe_path or not template_dir:
        logger.error("Nuclei executable path or template directory is not configured.")
        raise RuntimeError("Nuclei configuration is incomplete.")
    # 加入模板路径
    command = f"{exe_path}"
    template_mode = config['modes']['nuclei']['templates']
    for idx, template in enumerate(template_mode):
        print(f"[{idx + 1}] {template}")
    specified_idx = input(f"请选择要使用的模板编号 (1-{len(template_mode)}): ")
    try:
        specified_template_path = template_mode[int(specified_idx)-1]
    except IndexError:
        logger.error("Invalid index selected.")
        raise ValueError("Invalid index selected.")
    template_path = Path(template_dir) / specified_template_path
    if not template_path.exists():
        logger.error(f"Template path {template_path} does not exist.")
        raise FileNotFoundError(f"Template path {template_path} does not exist.")
    command += f" -t {template_path}"  # -t 参数指定模板路径
    # 加入威胁等级
    if severity is None:
        severity = nuclei_config.get('severity', [])
    if severity is not None or severity != []:
        command += f" -s {','.join(severity)}"
    # 加入输出路径
    output_path = Path(config['basedir']['result']) / Path(project_name)
    output_path.mkdir(parents=True, exist_ok=True)
    output_filetype_config: dict[str, bool] = config['nuclei']['output']
    for output_type, enabled in output_filetype_config.items():
        if enabled:
            command += f" -{output_type} {output_path}"
    # 加入URLs
    if len(urls) == 1:
        command += f" -u {urls[0]}"
    else:
        command += " -u ".join(urls) # 用-u分别添加多个URL
    # 加入速率
    rate_config = config['nuclei']['limit-rate']
    for setting, value in rate_config.items():
        command += f" -{setting} {value}"
    return command

if __name__ == "__main__":
    project_name = "test123"
    specified_template_path = "http/cves"
    urls = ["http://example.com"]
    severity = ["high"]
    try:
        command = _basic_generate_nuclei_command(project_name, specified_template_path, urls, severity)
        print(f"Generated Nuclei command: \n{command}")
    except Exception as e:
        logger.error(f"Error generating Nuclei command: {e}")