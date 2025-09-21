# -*- coding: utf-8 -*-
"""
资产控制器，实现资产发现和枚举的RESTful API接口
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse
from typing import List, Optional

from model.asset_model import ScanRequest, ScanResponse, ScanStatus, ExportRequest
from service.nuclei_scanner import nuclei_scanner
from config import current_config

# 创建路由
router = APIRouter(prefix=current_config.API_PREFIX)

@router.post("/scan", response_model=ScanResponse, tags=["资产扫描"])
async def start_scan(scan_request: ScanRequest):
    """
    启动资产扫描任务
    
    - **targets**: 扫描目标列表，可以包含IP、域名、端口或URL
    - **templates**: 可选，指定使用的nuclei模板
    - **timeout**: 可选，扫描超时时间（秒）
    - **verbose**: 是否输出详细结果
    
    返回扫描ID，可用于查询扫描状态和结果
    """
    try:
        # 检查目标是否为空
        if not scan_request.targets:
            raise HTTPException(status_code=400, detail="扫描目标不能为空")
        
        # 启动扫描任务
        scan_id = nuclei_scanner.start_scan(
            targets=scan_request.targets,
            templates=scan_request.templates,
            verbose=scan_request.verbose,
            timeout=scan_request.timeout
        )
        
        # 返回扫描响应
        return ScanResponse(
            scan_id=scan_id,
            status="pending",
            message="扫描任务已提交，请使用扫描ID查询状态和结果"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动扫描失败: {str(e)}")

@router.get("/scan/{scan_id}/status", response_model=ScanStatus, tags=["扫描状态查询"])
async def get_scan_status(scan_id: str):
    """
    查询扫描任务状态
    
    - **scan_id**: 扫描任务ID
    
    返回扫描任务的当前状态和进度
    """
    try:
        # 获取扫描状态
        status = nuclei_scanner.get_scan_status(scan_id)
        
        # 检查扫描任务是否存在
        if status is None:
            raise HTTPException(status_code=404, detail=f"未找到扫描任务: {scan_id}")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询扫描状态失败: {str(e)}")

@router.get("/scan/{scan_id}/results", tags=["扫描结果查询"])
async def get_scan_results(scan_id: str):
    """
    获取扫描结果
    
    - **scan_id**: 扫描任务ID
    
    返回扫描结果的原始JSON数据
    """
    try:
        # 获取扫描结果
        results = nuclei_scanner.get_scan_results(scan_id)
        
        # 检查扫描任务是否存在
        if results is None:
            # 检查扫描任务是否存在
            status = nuclei_scanner.get_scan_status(scan_id)
            if status is None:
                raise HTTPException(status_code=404, detail=f"未找到扫描任务: {scan_id}")
            else:
                # 扫描任务存在但未完成
                raise HTTPException(status_code=400, detail=f"扫描任务尚未完成，当前状态: {status.status}")
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取扫描结果失败: {str(e)}")

@router.post("/scan/export", tags=["结果导出"])
async def export_scan_results(export_request: ExportRequest, response: Response):
    """
    导出扫描结果
    
    - **scan_id**: 扫描任务ID
    - **format**: 导出格式，支持excel、json、csv
    
    返回导出的文件
    """
    try:
        # 导出扫描结果
        file_path = nuclei_scanner.export_results(
            scan_id=export_request.scan_id,
            export_format=export_request.format
        )
        
        # 检查导出是否成功
        if file_path is None:
            # 检查扫描任务是否存在
            status = nuclei_scanner.get_scan_status(export_request.scan_id)
            if status is None:
                raise HTTPException(status_code=404, detail=f"未找到扫描任务: {export_request.scan_id}")
            elif status.status != "completed":
                raise HTTPException(status_code=400, detail=f"扫描任务尚未完成，当前状态: {status.status}")
            else:
                raise HTTPException(status_code=500, detail="导出扫描结果失败")
        
        # 设置响应头
        if export_request.format == "excel":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"{export_request.scan_id}.xlsx"
        elif export_request.format == "json":
            media_type = "application/json"
            filename = f"{export_request.scan_id}.json"
        elif export_request.format == "csv":
            media_type = "text/csv"
            filename = f"{export_request.scan_id}.csv"
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
        
        # 返回文件
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出扫描结果失败: {str(e)}")

@router.get("/health", tags=["健康检查"])
async def health_check():
    """
    健康检查接口
    
    用于检查服务是否正常运行
    """
    return {
        "status": "ok",
        "project": current_config.PROJECT_NAME,
        "version": current_config.PROJECT_VERSION
    }