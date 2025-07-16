#TODO 通过YAML重新封装nuclei指令参数，并进行针对性指令生成

from core import logger, load_config
from pathlib import Path

def generate_nuclei_command(
    project_name: str, # 输出路径
    specified_template_path: str, 
    urls: list = None,
    severity: list = None) -> str:
    """
    生成nuclei命令行指令
    :param project_name: 项目名称，用于输出路径
    :param specified_template_path: 指定的模板路径
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
    command = f"{exe_path} -t {Path(template_dir) / specified_template_path}"
    # 加入威胁等级
    if severity is None:
        severity = nuclei_config.get('severity', [])
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
        command = generate_nuclei_command(project_name, specified_template_path, urls, severity)
        print(f"Generated Nuclei command: \n{command}")
    except Exception as e:
        logger.error(f"Error generating Nuclei command: {e}")