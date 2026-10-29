@echo off
chcp 65001 >nul
title Dual MiMo Research Engine — Autônomo 24/7
cd /d "%~dp0"

echo ========================================================
echo   DUAL MIMO RESEARCH ENGINE — PESQUISA AUTÔNOMA 24/7
echo ========================================================
echo   Pesquisador A: mimo-v2.6-pro-ultraspeed
echo   Pesquisador B: mimo-v2.6-pro
echo   Proxy Local  : http://127.0.0.1:8088/v1
echo   Hardware     : NVIDIA RTX 3060 12GB (CUDA)
echo   Telemetria   : Discord Ativo (Rich Embeds)
echo ========================================================
echo.

rem Remove sinais residuais
if exist STOP.signal del STOP.signal
if exist PAUSE.signal del PAUSE.signal

python orchestrator.py loop 500

pause
