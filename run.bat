@echo off
REM run.bat - Windows启动脚本
echo 正在启动Quark File Manager...
echo 端口: 5180

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请安装Python 3.8+
    pause
    exit /b 1
)

REM 安装依赖
pip install -r requirements.txt

REM 启动服务器
python server.py

pause