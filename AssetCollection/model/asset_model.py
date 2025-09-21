# -*- coding: utf-8 -*-
"""
资产模型文件，定义资产相关的数据结构
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Union
from datetime import datetime

class Target(BaseModel):
    """扫描目标模型"""
    # IP地址
    ip: Optional[str] = Field(None, example="192.168.1.1")
    # 域名
    domain: Optional[str] = Field(None, example="example.com")
    # 端口
    port: Optional[int] = Field(None, example=80)
    # URL
    url: Optional[HttpUrl] = Field(None, example="http://example.com")

class ScanRequest(BaseModel):
    """扫描请求模型"""
    # 扫描目标列表
    targets: List[Target] = Field(..., example=[{"domain": "example.com"}])
    # nuclei模板列表（可选）
    templates: Optional[List[str]] = Field(None, example=["http/tech-detect"])
    # 扫描超时时间（秒，可选）
    timeout: Optional[int] = Field(None, example=3600)
    # 是否输出详细结果
    verbose: bool = Field(False, example=False)

class ScanResult(BaseModel):
    """扫描结果模型"""
    # 扫描ID
    scan_id: str
    # 扫描目标
    target: str
    # 发现的资产类型
    asset_type: str
    # 扫描结果详情
    details: dict
    # 扫描时间
    scan_time: datetime
    # 扫描状态
    status: str  # "success", "failed", "running"

class ScanStatus(BaseModel):
    """扫描状态模型"""
    # 扫描ID
    scan_id: str
    # 扫描状态
    status: str  # "pending", "running", "completed", "failed"
    # 进度百分比
    progress: int
    # 已完成任务数
    completed: int
    # 总任务数
    total: int
    # 错误信息（如果有）
    error: Optional[str] = None
    # 开始时间
    start_time: Optional[datetime] = None
    # 结束时间
    end_time: Optional[datetime] = None

class ScanResponse(BaseModel):
    """扫描响应模型"""
    # 扫描ID
    scan_id: str
    # 扫描状态
    status: str
    # 消息
    message: str
    # 结果URL（如果已完成）
    results_url: Optional[str] = None

class ExportRequest(BaseModel):
    """导出请求模型"""
    # 扫描ID
    scan_id: str
    # 导出格式（支持excel, json, csv）
    format: str = Field(..., example="excel", pattern="^(excel|json|csv)$")