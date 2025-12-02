@echo off
chcp 65001 >nul
echo ========================================
echo   ArXiv Intelligent Q&A System
echo ========================================
echo.

REM 设置API配置
set BASE_URL=...your api base url...
set API_KEY=...your api key...
echo Starting Web UI mode...
echo.

python main.py --base_url "%BASE_URL%" --api_key "%API_KEY%"

echo.
pause
