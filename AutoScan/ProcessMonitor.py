#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
进程监控模块

该模块提供跨平台的进程监控功能，支持Windows和Linux操作系统
主要用于监控指定名称的进程是否在运行，可用于等待某个进程执行完成

使用示例:
    monitor = ProcessMonitor("process_name")
    status = monitor.main()  # 当进程结束时返回1
"""

import psutil
import subprocess
import platform
import time


class ProcessMonitor():
    """
    进程监控类
    用于监控指定名称的进程是否在运行
    支持Windows和Linux两种操作系统
    """
    
    def __init__(self, processname):
        """
        初始化ProcessMonitor实例
        
        参数:
            processname (str): 要监控的进程名称
        """
        self.processname = processname
        
    def main(self):
        """
        主方法，启动进程监控
        
        返回:
            int: 当监控的进程结束时返回1
        """
        status = self.check_system()
        return status
        
    def check_system(self):
        """
        检查当前操作系统类型，调用相应的监控方法
        
        返回:
            int: 当监控的进程结束时返回1
        """
        plat = platform.system().lower()
        if plat == 'windows':
            return self.win_process()
        elif plat == 'linux':
            return self.linux_process()

    def win_process(self):
        """
        Windows系统下的进程监控实现
        通过psutil模块获取进程列表并监控指定进程
        
        返回:
            int: 当监控的进程结束时返回1
        """
        # print("[+]这是windows系统")
        while True:
            start_pl = psutil.pids()
            time.sleep(1)
            for pid in start_pl:
                if self.processname not in psutil.Process(pid).name():  # 看我们监控的进程名是否在进程列表里
                    # print("[+]程序执行完毕")
                    return 1  # 进程执行完毕

    # linux进程监控
    def linux_process(self):
        """
        Linux系统下的进程监控实现
        通过ps命令获取进程列表并监控指定进程
        
        返回:
            int: 当监控的进程结束时返回1
        """
        # print("[+]这是linux系统")
        while True:
            cmd = "ps -aux | grep {} ".format(self.processname) + "| grep -v grep | awk '{print $2}'"
            start_rsp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            time.sleep(1)
            end_rsp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            if len(start_rsp.stdout.read().strip()) != 0:
                # print("[+]程序正在执行中...")
                if len(end_rsp.stdout.read().strip()) == 0:
                    # print("[+]程序执行完毕")
                    return 1





