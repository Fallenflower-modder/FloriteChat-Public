import os
import sys
import threading
import subprocess
import time

"""
完整服务器启动脚本

此脚本同时启动HTTP服务器和WebSocket服务器，使用独立的线程运行HTTP服务器，
并直接运行WebSocket服务器主程序。
"""

def start_http_server():
    """启动HTTP服务器提供静态文件服务"""
    try:
        # 使用Python的内置http.server模块
        import http.server
        import socketserver
        
        # 设置端口
        PORT = 8000
        
        # 创建处理器
        handler = http.server.SimpleHTTPRequestHandler
        
        # 使用ThreadingTCPServer支持多线程并发处理
        with socketserver.ThreadingTCPServer(("", PORT), handler) as httpd:
            # 启用地址重用，避免端口占用问题
            httpd.allow_reuse_address = True
            print(f"HTTP服务器已启动，监听端口 {PORT}")
            print("服务器已配置为多线程模式，支持并发请求")
            httpd.serve_forever()
    except Exception as e:
        print(f"HTTP服务器启动失败: {e}")

def start_full_server():
    """启动完整的聊天服务器（HTTP + WebSocket）"""
    print("正在启动 FloriteChat 完整服务器...")
    
    # 启动HTTP服务器线程
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # 等待HTTP服务器启动
    time.sleep(1)
    
    # 启动WebSocket服务器
    print("启动WebSocket服务器...")
    
    try:
        # 直接运行主服务器文件
        server_path = os.path.join('src', 'server', 'server.py')
        
        # 检查虚拟环境
        venv_activated = 'VIRTUAL_ENV' in os.environ or 'venv' in sys.prefix
        
        if venv_activated:
            # 使用已激活的虚拟环境
            python_exe = sys.executable
        else:
            # 尝试使用venv中的Python
            venv_python = os.path.join('venv', 'Scripts', 'python.exe')
            if os.path.exists(venv_python):
                python_exe = venv_python
            else:
                python_exe = 'python'
        
        print(f"使用Python: {python_exe}")
        print("\n使用说明:")
        print("1. 打开浏览器，访问: http://localhost:8000/src/client/login.html")
        print("2. 输入用户名和密码并选择服务器地址 (ws://localhost:8766)")
        print("3. 开始聊天!")
        print("\n按 Ctrl+C 停止服务器")
        
        # 运行WebSocket服务器
        subprocess.run([python_exe, server_path])
        
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
    except Exception as e:
        print(f"启动服务器时出错: {e}")

if __name__ == "__main__":
    start_full_server()
