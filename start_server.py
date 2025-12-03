#!/usr/bin/env python3
"""
FloriteChat 服务器启动脚本
"""

import os
import sys
import subprocess
import time
import threading
import http.server
import socketserver

# 检查Python版本
if sys.version_info < (3, 7):
    print("错误: 需要Python 3.7或更高版本")
    sys.exit(1)

def start_http_server():
    """启动HTTP服务器提供静态文件服务"""
    # 设置HTTP服务器端口
    PORT = 8000
    
    # 切换到项目根目录作为HTTP服务器的工作目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 创建HTTP请求处理器
    Handler = http.server.SimpleHTTPRequestHandler
    
    # 设置为不显示日志信息
    Handler.log_message = lambda self, format, *args: None
    
    # 创建TCP服务器
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"HTTP服务器已启动，监听端口 {PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nHTTP服务器已停止")


def start_server():
    """启动HTTP服务器"""
    print("正在启动 FloriteChat 服务器...")
    
    # 启动HTTP服务器（提供静态文件服务）
    print("HTTP服务器已启动，监听端口 8000")
    print("\n使用说明:")
    print("1. 确保WebSocket服务器已在运行")
    print("2. 打开浏览器，访问: http://localhost:8000/src/client/login.html")
    print("3. 输入昵称并选择服务器地址")
    print("4. 开始聊天!")
    print("\n按 Ctrl+C 停止HTTP服务器")
    
    # 直接启动HTTP服务器（不使用线程，便于控制）
    start_http_server()

if __name__ == "__main__":
    start_server()