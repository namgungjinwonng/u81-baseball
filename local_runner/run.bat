@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo U-18 로컬 자동 일정 수집기를 시작합니다...
python u18_auto.py
echo.
echo (종료되었습니다. 창을 닫으셔도 됩니다.)
pause
