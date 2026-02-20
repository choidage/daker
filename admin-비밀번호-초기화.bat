@echo off
chcp 65001 >nul
title VIBE-X admin 비밀번호 초기화

cd /d "%~dp0vibe-x"
if errorlevel 1 (
    echo [오류] vibe-x 폴더를 찾을 수 없습니다.
    pause
    exit /b 1
)

echo.
echo   VIBE-X admin 비밀번호 초기화
echo   ─────────────────────────────
echo.

python scripts\reset_admin_password.py
if errorlevel 1 (
    echo.
    echo [오류] 실행 실패. 아래 항목을 확인하세요:
    echo   1. Python이 설치되어 있는지 확인
    echo   2. vibe-x\scripts\reset_admin_password.py 파일 존재 여부 확인
)
echo.
pause
