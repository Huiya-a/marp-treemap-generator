@echo off
echo ========================================
echo   应用架构图生成器 - 启动中...
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖...
python -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo 正在安装PySide6...
    pip install "PySide6>=6.5.0"
)

python -c "import openpyxl" >nul 2>&1
if errorlevel 1 (
    echo 正在安装openpyxl...
    pip install "openpyxl>=3.1.0"
)

python -c "import numpy" >nul 2>&1
if errorlevel 1 (
    echo 正在安装numpy...
    pip install "numpy>=1.24.0"
)

echo.
echo 依赖检查完成，正在启动应用...
echo.

REM 启动应用（app.py现在在src目录下）
python src\app.py

pause
