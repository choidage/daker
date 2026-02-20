@echo off
chcp 65001 >nul
title VIBE-X Docker Compose

cd /d "%~dp0vibe-x"
if errorlevel 1 (
    echo [오류] vibe-x 폴더를 찾을 수 없습니다.
    pause
    exit /b 1
)

echo.
echo   ╔══════════════════════════════════════╗
echo   ║    VIBE-X Docker Compose Start       ║
echo   ╚══════════════════════════════════════╝
echo.

REM Docker 실행 확인
docker info >nul 2>&1
if errorlevel 1 (
    echo [오류] Docker가 실행되고 있지 않습니다.
    echo        Docker Desktop을 먼저 시작해 주세요.
    echo.
    pause
    exit /b 1
)

echo   Docker 확인 완료. 컨테이너를 시작합니다...
echo.

docker compose up -d --build
if errorlevel 1 (
    echo.
    echo [오류] Docker Compose 실행 실패.
    pause
    exit /b 1
)

echo.
echo   ╔══════════════════════════════════════╗
echo   ║          시작 완료!                   ║
echo   ╠══════════════════════════════════════╣
echo   ║  대시보드: http://localhost:3000      ║
echo   ║  API:     http://localhost:8000      ║
echo   ║  계정:    admin / admin1234          ║
echo   ╚══════════════════════════════════════╝
echo.
echo   종료: docker compose down
echo.

REM 브라우저 열기
powershell -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://localhost:3000'"

echo   아무 키나 누르면 컨테이너를 중지합니다...
pause >nul

echo.
echo   컨테이너 중지 중...
docker compose down
echo   완료.
pause
