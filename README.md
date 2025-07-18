# Automatic Bug Penetesting Tool

![Security](https://img.shields.io/badge/Security-Penetration%20Testing-blue)
![Python](https://img.shields.io/badge/Python-3.8+-blue)

一个自动化安全测试工具，集成了FOFA资产收集、HTTP探活和Nuclei漏洞扫描功能。

## 功能特性

- **资产收集**：通过FOFA API查询目标资产
- **资产探活**：使用HTTPX验证资产可用性
- **漏洞扫描**：集成Nuclei进行自动化漏洞检测
- **数据持久化**：使用Parquet格式存储中间结果
- **命令行界面**：支持~~灵活~~的参数配置

## 安装指南

### 前置要求
- Python 3.8+
- Nuclei安装并配置模板目录
- FOFA API账号

### 安装步骤
1. 克隆仓库：
```bash
git clone https://github.com/your-repo/automatic-bug-penetesting.git
cd automatic-bug-penetesting
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置`config.yml`：
```bash
cp config.yml.example config.yml
```

## 使用说明

基本用法：
```bash
python src/main.py -p PROJECT_NAME -d example.com
```

完整参数：
```bash
python src/main.py -h
```

示例扫描：
```bash
python src/main.py -p test_project -d example.com -s nginx -t /path/to/nuclei-templates
```

## 配置说明

编辑`config.yml`文件配置：
- FOFA API密钥
- Nuclei模板路径
- 扫描参数
- 日志设置

## 依赖项

- colorama==0.4.6
- httpx==0.27.0
- loguru==0.7.3
- pandas==2.2.3
- pyarrow==19.0.1
- PyYAML==6.0.2
- tqdm==4.66.4

## 许可证

[The UnLicense 反授权协议](LICENSE.md)