@echo off
chcp 65001 >nul
echo ========================================
echo    ArXiv 论文爬虫和分析系统
echo ========================================
echo.
echo 正在启动系统...
echo.

python main.py --base_url "https://yunwu.ai/v1" --api_key "sk-5N0wwebNZWT1DkAMVkRTbjMrfRSKlO0q4crzwLwcoPhrL043"

pause
