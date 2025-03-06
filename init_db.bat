@echo off
echo === 行政管理系统数据库初始化工具 ===
echo.

REM 检查是否存在虚拟环境
if exist .venv\Scripts\activate.bat (
    echo 正在激活虚拟环境...
    call .venv\Scripts\activate.bat
) else (
    echo 警告: 未找到虚拟环境，将使用系统Python环境
)

REM 设置Flask环境变量
set FLASK_APP=app

REM 运行初始化脚本
echo 正在运行初始化脚本...
python init_db.py

echo.
echo 按任意键退出...
pause > nul 