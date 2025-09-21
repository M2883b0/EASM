# -*- coding: utf-8 -*-
"""
nuclei扫描器服务，负责调用nuclei命令行工具进行资产发现和枚举
"""
import subprocess
import json
import os
import uuid
import threading
import queue
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import tempfile

from model.asset_model import Target, ScanResult, ScanStatus
from config import current_config

class NucleiScanner:
    """nuclei扫描器类，封装了调用nuclei命令行工具的功能"""
    
    def __init__(self):
        """初始化扫描器"""
        self.scan_jobs = {}
        self.scan_queue = queue.Queue()
        self.max_concurrent_scans = current_config.MAX_CONCURRENT_SCANS
        self.active_scans = 0
        self.lock = threading.Lock()
        
        # 创建结果存储目录
        os.makedirs(current_config.RESULTS_DIR, exist_ok=True)
        os.makedirs(current_config.TEMP_DIR, exist_ok=True)
        
        # 启动扫描工作线程
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
    
    def _worker(self):
        """工作线程，负责从队列中获取扫描任务并执行"""
        while True:
            if self.active_scans < self.max_concurrent_scans:
                try:
                    # 非阻塞方式获取队列中的任务
                    scan_id, targets, templates, verbose, timeout = self.scan_queue.get(block=False)
                    
                    with self.lock:
                        self.active_scans += 1
                    
                    # 启动扫描线程
                    scan_thread = threading.Thread(
                        target=self._scan, 
                        args=(scan_id, targets, templates, verbose, timeout)
                    )
                    scan_thread.daemon = True
                    scan_thread.start()
                    
                    # 标记任务为完成
                    self.scan_queue.task_done()
                except queue.Empty:
                    # 队列为空，等待一段时间再尝试
                    time.sleep(1)
            else:
                # 达到最大并发数，等待一段时间再尝试
                time.sleep(1)
    
    def _prepare_target_file(self, targets: List[Target]) -> str:
        """准备目标文件"""
        target_list = []
        for target in targets:
            if target.url:
                target_list.append(str(target.url))
            elif target.domain:
                target_list.append(target.domain)
            elif target.ip:
                if target.port:
                    target_list.append(f"{target.ip}:{target.port}")
                else:
                    target_list.append(target.ip)
        
        # 创建临时文件
        fd, path = tempfile.mkstemp(dir=current_config.TEMP_DIR, suffix=".txt")
        with os.fdopen(fd, 'w') as f:
            f.write('\n'.join(target_list))
        
        return path
    
    def _scan(self, scan_id: str, targets: List[Target], templates: Optional[List[str]], 
              verbose: bool, timeout: Optional[int]) -> None:
        """执行nuclei扫描"""
        try:
            # 更新扫描状态为运行中
            with self.lock:
                self.scan_jobs[scan_id] = {
                    "status": "running",
                    "progress": 0,
                    "completed": 0,
                    "total": len(targets),
                    "start_time": datetime.now(),
                    "results": [],
                    "error": None
                }
            
            # 准备目标文件
            target_file = self._prepare_target_file(targets)
            
            # 构建nuclei命令 - 移除Windows不支持的/dev/stdout参数
            cmd = [current_config.NUCLEI_PATH, "-l", target_file, "-json"]
            
            # 添加模板参数
            if templates:
                cmd.extend(["-t", ",".join(templates)])
            
            # 添加详细参数
            if verbose:
                cmd.append("-v")
            
            # 设置超时时间
            scan_timeout = timeout or current_config.SCAN_TIMEOUT
            
            # 执行命令并收集结果
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8'
                )
            except FileNotFoundError:
                # 如果找不到nuclei可执行文件，提供更详细的错误信息
                with self.lock:
                    self.scan_jobs[scan_id]["error"] = f"找不到nuclei可执行文件。请确保nuclei已安装并添加到系统PATH中，或在config.py中正确配置NUCLEI_PATH。当前配置的路径: {current_config.NUCLEI_PATH}"
                    self.scan_jobs[scan_id]["status"] = "failed"
                return
            except Exception as e:
                with self.lock:
                    self.scan_jobs[scan_id]["error"] = f"启动nuclei进程失败: {str(e)}"
                    self.scan_jobs[scan_id]["status"] = "failed"
                return

            # 读取输出
            results = []
            completed_count = 0

            try:
                # 使用communicate并设置超时
                stdout, stderr = process.communicate(timeout=scan_timeout)
                
                # 检查是否有错误
                if process.returncode != 0:
                    # 确保错误信息不为空
                    error_output = stderr if stderr else "(无错误输出)"
                    error_msg = f"nuclei扫描失败，返回码: {process.returncode}。错误信息: {error_output}"
                    with self.lock:
                        self.scan_jobs[scan_id]["error"] = error_msg
                        self.scan_jobs[scan_id]["status"] = "failed"
                else:
                    # 解析JSON输出
                    for line in stdout.strip().split('\n'):
                        if line.strip():
                            try:
                                result = json.loads(line)
                                results.append(result)
                                completed_count += 1
                                 
                                # 更新进度
                                with self.lock:
                                    self.scan_jobs[scan_id]["completed"] = completed_count
                                    self.scan_jobs[scan_id]["progress"] = min(100, int(completed_count / len(targets) * 100))
                                    self.scan_jobs[scan_id]["results"].append(result)
                            except json.JSONDecodeError:
                                # 忽略无法解析的行
                                pass
                     
                    # 扫描完成
                    with self.lock:
                        self.scan_jobs[scan_id]["status"] = "completed"
                        self.scan_jobs[scan_id]["progress"] = 100
                        self.scan_jobs[scan_id]["end_time"] = datetime.now()
                         
                        # 保存结果到文件
                        result_file = os.path.join(current_config.RESULTS_DIR, f"{scan_id}.json")
                        with open(result_file, 'w', encoding='utf-8') as f:
                            json.dump(self.scan_jobs[scan_id]["results"], f, ensure_ascii=False, indent=2)
            except subprocess.TimeoutExpired:
                # 超时处理
                process.kill()
                with self.lock:
                    self.scan_jobs[scan_id]["error"] = f"扫描超时，已超过{scan_timeout}秒"
                    self.scan_jobs[scan_id]["status"] = "failed"
            finally:
                # 清理临时文件
                if os.path.exists(target_file):
                    os.remove(target_file)
        except Exception as e:
            # 处理其他异常
            with self.lock:
                self.scan_jobs[scan_id]["error"] = str(e)
                self.scan_jobs[scan_id]["status"] = "failed"
        finally:
            with self.lock:
                self.active_scans -= 1
    
    def start_scan(self, targets: List[Target], templates: Optional[List[str]] = None, 
                  verbose: bool = False, timeout: Optional[int] = None) -> str:
        """开始扫描任务"""
        # 生成扫描ID
        scan_id = str(uuid.uuid4())
        
        # 将扫描任务加入队列
        self.scan_queue.put((scan_id, targets, templates, verbose, timeout))
        
        # 初始化扫描任务状态
        with self.lock:
            self.scan_jobs[scan_id] = {
                "status": "pending",
                "progress": 0,
                "completed": 0,
                "total": len(targets),
                "start_time": None,
                "end_time": None,
                "results": [],
                "error": None
            }
        
        return scan_id
    
    def get_scan_status(self, scan_id: str) -> Optional[ScanStatus]:
        """获取扫描任务状态"""
        with self.lock:
            if scan_id not in self.scan_jobs:
                return None
            
            job = self.scan_jobs[scan_id]
            
            # 确保所有必要的键都存在
            return ScanStatus(
                scan_id=scan_id,
                status=job.get("status", "unknown"),
                progress=job.get("progress", 0),
                completed=job.get("completed", 0),
                total=job.get("total", 0),
                error=job.get("error"),
                start_time=job.get("start_time"),
                end_time=job.get("end_time")
            )
    
    def get_scan_results(self, scan_id: str) -> Optional[List[Dict]]:
        """获取扫描结果"""
        with self.lock:
            if scan_id not in self.scan_jobs:
                return None
            
            job = self.scan_jobs[scan_id]
            if job["status"] != "completed":
                return None
            
            return job["results"]
    
    def export_results(self, scan_id: str, export_format: str) -> Optional[str]:
        """导出扫描结果"""
        with self.lock:
            if scan_id not in self.scan_jobs:
                return None
            
            job = self.scan_jobs[scan_id]
            if job["status"] != "completed":
                return None
            
            # 获取结果文件路径
            result_file = os.path.join(current_config.RESULTS_DIR, f"{scan_id}.json")
            if not os.path.exists(result_file):
                return None
            
            # 读取结果
            with open(result_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # 根据格式导出
            if export_format == "json":
                # JSON格式直接返回原文件路径
                return result_file
            elif export_format == "excel":
                # 导出为Excel文件
                import pandas as pd
                
                # 准备Excel数据
                excel_data = []
                for result in results:
                    excel_row = {
                        "Target": result.get("host", ""),
                        "Type": result.get("type", ""),
                        "Severity": result.get("severity", ""),
                        "Template": result.get("template-id", ""),
                        "Description": result.get("info", {}).get("description", ""),
                        "Match": result.get("matched-at", "")
                    }
                    excel_data.append(excel_row)
                
                # 创建DataFrame并导出
                df = pd.DataFrame(excel_data)
                excel_file = os.path.join(current_config.RESULTS_DIR, f"{scan_id}.xlsx")
                df.to_excel(excel_file, index=False)
                
                return excel_file
            elif export_format == "csv":
                # 导出为CSV文件
                import pandas as pd
                
                # 准备CSV数据
                csv_data = []
                for result in results:
                    csv_row = {
                        "Target": result.get("host", ""),
                        "Type": result.get("type", ""),
                        "Severity": result.get("severity", ""),
                        "Template": result.get("template-id", ""),
                        "Description": result.get("info", {}).get("description", ""),
                        "Match": result.get("matched-at", "")
                    }
                    csv_data.append(csv_row)
                
                # 创建DataFrame并导出
                df = pd.DataFrame(csv_data)
                csv_file = os.path.join(current_config.RESULTS_DIR, f"{scan_id}.csv")
                df.to_csv(csv_file, index=False, encoding='utf-8')
                
                return csv_file
            else:
                return None

# 创建全局扫描器实例
nuclei_scanner = NucleiScanner()