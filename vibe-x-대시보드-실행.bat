@echo off
chcp 65001 >nul
title VIBE-X Dashboard

cd /d "%~dp0vibe-x"
if errorlevel 1 (
    echo [오류] vibe-x 폴더를 찾을 수 없습니다: %~dp0vibe-x
    pause
    exit /b 1
)

echo.
echo   ╔══════════════════════════════════════╗
echo   ║      VIBE-X Dashboard Start          ║
echo   ╚══════════════════════════════════════╝
echo.
echo   [1] Backend  : http://localhost:8000  (FastAPI)
echo   [2] Frontend : http://localhost:3000  (Next.js)
echo.
echo   브라우저에서 http://localhost:3000 으로 접속하세요.
echo   기본 계정: admin / admin1234
echo   종료하려면 이 창에서 Ctrl+C 를 누르세요.
echo.

REM 프론트엔드 서버를 별도 창으로 실행
start "VIBE-X Frontend" cmd /k "cd /d "%~dp0vibe-x\dashboard" && npm run dev"

REM 백엔드 서버 실행 (현재 창)
python server.py
if errorlevel 1 (
    echo.
    echo [오류] 서버 실행 실패. 아래 항목을 확인하세요:
    echo   1. pip install -r requirements.txt  (vibe-x 폴더에서)
    echo   2. cd dashboard ^&^& npm install     (프론트엔드 의존성)
    echo.
    pause
)
