# 资产收集微服务 (AssetCollection)

一个基于Python和nuclei的资产发现和枚举微服务，提供RESTful API接口，支持多种输出格式，包括Excel。

## 功能特点

- 支持多种资产输入：IP、域名、端口、URL
- 使用nuclei进行资产发现和枚举
- 提供实时扫描进度查询
- 支持多种结果输出格式：JSON、Excel、CSV
- 并发扫描支持
- 基于FastAPI的RESTful API接口
- 完整的API文档（Swagger UI和ReDoc）

## 环境要求

- Python 3.8+
- nuclei工具（需要安装并添加到系统PATH中）

## 安装步骤

1. 克隆项目代码

```bash
# 进入项目目录
e: && cd e:\learn\easm\AssetCollection
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 安装nuclei工具

请参考[nuclei官方文档](https://nuclei.projectdiscovery.io/)进行安装。

## 使用方法

### 启动服务

```bash
python main.py
```

服务将在 http://0.0.0.0:8000 启动

### API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要API端点

1. **启动扫描**
   - POST `/api/v1/scan`
   - 提交资产扫描任务

2. **查询扫描状态**
   - GET `/api/v1/scan/{scan_id}/status`
   - 查询扫描任务的实时进度

3. **获取扫描结果**
   - GET `/api/v1/scan/{scan_id}/results`
   - 获取扫描结果的原始数据

4. **导出扫描结果**
   - POST `/api/v1/scan/export`
   - 导出扫描结果为Excel、JSON或CSV格式

5. **健康检查**
   - GET `/api/v1/health`
   - 检查服务是否正常运行

### 配置说明

配置文件位于 `config.py`，主要配置项包括：

- `SERVER_HOST`: 服务主机（默认：0.0.0.0）
- `SERVER_PORT`: 服务端口（默认：8000）
- `NUCLEI_PATH`: nuclei可执行文件路径（默认：nuclei，使用系统PATH中的nuclei）
- `SCAN_TIMEOUT`: 扫描超时时间（秒，默认：3600）
- `MAX_CONCURRENT_SCANS`: 最大并发扫描数（默认：5）
- `RESULTS_DIR`: 结果存储目录（默认：results）
- `TEMP_DIR`: 临时文件目录（默认：temp）

## 示例请求

### 启动扫描

```json
POST /api/v1/scan
Content-Type: application/json

{
  "targets": [
    {"domain": "example.com"},
    {"ip": "192.168.1.1"},
    {"ip": "192.168.1.2", "port": 8080}
  ],
  "templates": ["http/tech-detect"],
  "verbose": true
}
```

### 导出结果

```json
POST /api/v1/scan/export
Content-Type: application/json

{
  "scan_id": "your-scan-id-here",
  "format": "excel"
}
```

## 注意事项

1. 请确保nuclei工具已正确安装并添加到系统PATH中
2. 大规模扫描可能会消耗较多系统资源，请根据实际情况调整并发数
3. 扫描结果将保存在 `results` 目录下
4. 临时文件将保存在 `temp` 目录下，扫描完成后会自动清理

## License

MIT