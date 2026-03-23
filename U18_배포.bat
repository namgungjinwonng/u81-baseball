@echo off
chcp 65001 >nul
title U-18 GitHub Pages 배포
color 0A

cd /d "%~dp0"

echo ==================================================
echo   U-18 GitHub Pages 배포
echo ==================================================
echo.

echo [1/3] docs 폴더 스테이징...
git add docs/
echo.

echo [2/3] 커밋 중...
for /f "tokens=1-2 delims= " %%a in ('python -c "from datetime import datetime; print(datetime.now().strftime('%%Y-%%m-%%d %%H:%%M'))"') do set DT=%%a %%b
git commit -m "데이터 갱신: %DT%"
if %ERRORLEVEL% neq 0 (
    echo.
    echo   변경사항이 없습니다.
    echo.
    pause
    exit /b 0
)
echo.

echo [3/3] GitHub Push 중...
git push origin main
if %ERRORLEVEL% neq 0 (
    color 0C
    echo.
    echo   Push 실패! 네트워크 연결을 확인하세요.
    echo.
    pause
    exit /b 1
)

echo.
echo ==================================================
echo   배포 완료!
echo   1~2분 후 반영됩니다.
echo   https://namgungjinwonng.github.io/u81-baseball/
echo ==================================================
echo.
pause
