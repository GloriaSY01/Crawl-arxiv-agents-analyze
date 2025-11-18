@echo off
REM ArXiv论文智能分析系统 - Windows快速启动脚本
REM 使用方法：双击此文件即可启动

echo ========================================
echo  ArXiv论文智能分析系统
echo  单篇论文深度问答功能已就绪
echo ========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

echo [1/3] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo [2/3] 启动系统...
echo 提示: 浏览器将自动打开 http://localhost:8501
echo.

REM 启动系统
python main.py ^
    --base_url "https://yunwu.ai/v1" ^
    --api_key "sk-5N0wwebNZWT1DkAMVkRTbjMrfRSKlO0q4crzwLwcoPhrL043"

pause
