# -*- coding: utf-8 -*-
"""
主程序文件，初始化FastAPI应用并启动HTTP服务器
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from controller.asset_controller import router
from config import current_config

# 创建FastAPI应用
app = FastAPI(
    title=current_config.PROJECT_NAME,
    description="资产收集微服务 - 使用nuclei进行资产发现和枚举",
    version=current_config.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自定义OpenAPI文档
@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_json():
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

# 注册路由
app.include_router(router)

# 根路径
@app.get("/")
async def root():
    """
    根路径
    
    返回项目基本信息
    """
    return {
        "project": current_config.PROJECT_NAME,
        "version": current_config.PROJECT_VERSION,
        "description": "资产收集微服务 - 使用nuclei进行资产发现和枚举",
        "docs": f"http://{current_config.SERVER_HOST}:{current_config.SERVER_PORT}/docs"
    }

if __name__ == "__main__":
    # 启动UVicorn服务器
    uvicorn.run(
        "main:app",
        host=current_config.SERVER_HOST,
        port=current_config.SERVER_PORT,
        reload=True  # 开发模式下启用自动重载
    )