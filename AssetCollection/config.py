# -*- coding: utf-8 -*-
"""
配置文件，存储项目的配置信息
"""

# 项目基础配置
class Config:
    # 项目名称
    PROJECT_NAME = "AssetCollection"
    # 项目版本
    PROJECT_VERSION = "1.0.0"
    # API路径前缀
    API_PREFIX = "/api/v1"
    # 服务端口
    SERVER_PORT = 8000
    # 服务主机
    SERVER_HOST = "0.0.0.0"
    
    # nuclei配置
    # nuclei可执行文件路径（默认使用系统路径中的nuclei）
    NUCLEI_PATH = "nuclei"
    # nuclei模板目录（默认使用nuclei内置模板）
    NUCLEI_TEMPLATE_DIR = None
    # 扫描超时时间（秒）
    SCAN_TIMEOUT = 3600
    
    # 结果存储配置
    # 结果存储目录
    RESULTS_DIR = "results"
    # 临时文件目录
    TEMP_DIR = "temp"
    
    # 并发配置
    # 最大并发扫描数
    MAX_CONCURRENT_SCANS = 5

# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True
    # 开发环境下可以修改相关配置

# 生产环境配置
class ProductionConfig(Config):
    DEBUG = False
    # 生产环境下可以修改相关配置

# 默认使用开发环境配置
current_config = DevelopmentConfig()