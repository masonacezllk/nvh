@echo off
echo 正在启动NVH小程序...
echo 激活Anaconda虚拟环境streamlit...
call conda activate streamlit

echo Streamlit服务器将在浏览器中打开
echo 如果浏览器没有自动打开，请访问: http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo.

streamlit run "0_🚗_登录.py" --server.port 5000

pause
