@echo off
cd /d "%~dp0"
echo ============================================
echo   半导体装备与材料产业链图谱 - 本地预览
echo ============================================
echo.
echo 正在启动本地预览服务...
echo 请在浏览器访问: http://localhost:8000
echo 关闭本窗口即停止服务。
echo.
python -m http.server 8000 2>nul || py -m http.server 8000 2>nul || echo [错误] 未检测到 Python，请安装 Python 或使用任意静态 HTTP 服务器。
pause
