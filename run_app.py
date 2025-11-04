#!/usr/bin/env python3
"""
Streamlit应用启动脚本
用于启动NVH小程序
"""

import subprocess
import sys
import os

def main():
    """
    启动Streamlit应用
    """
    try:
        # 检查当前目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"当前工作目录: {current_dir}")
        
        # 检查登录文件是否存在
        login_file = "0_🚗_登录.py"
        if not os.path.exists(login_file):
            print(f"错误: 找不到登录文件 {login_file}")
            print("请确保在正确的目录中运行此脚本")
            return
        
        print("正在启动NVH小程序...")
        print("Streamlit服务器将在浏览器中打开")
        print("如果浏览器没有自动打开，请访问: http://localhost:5000")
        print("按 Ctrl+C 停止服务器")
        
        # 运行Streamlit命令
        cmd = [sys.executable, "-m", "streamlit", "run", login_file, "--server.port", "5000"]
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        print("请确保已安装Streamlit: pip install streamlit")

if __name__ == "__main__":
    main()
