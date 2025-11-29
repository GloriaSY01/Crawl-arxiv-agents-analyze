@echo off
chcp 65001 >nul
echo ========================================
echo   ArXiv Intelligent Q&A System
echo ========================================
echo.

REM 设置API配置
set BASE_URL=https://yunwu.ai/v1
set API_KEY=sk-5N0wwebNZWT1DkAMVkRTbjMrfRSKlO0q4crzwLwcoPhrL043

echo Starting Web UI mode...
echo.

python main.py --base_url "%BASE_URL%" --api_key "%API_KEY%"

echo.
pause
