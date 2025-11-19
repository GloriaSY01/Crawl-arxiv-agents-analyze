@echo off
chcp 65001 >nul
echo ========================================
echo    ArXiv 论文爬虫和分析系统
echo ========================================
echo.
echo 正在启动 Streamlit 应用...
echo.

streamlit run streamlit_app.py

pause
