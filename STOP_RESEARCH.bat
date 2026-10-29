@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Gravando sinal de parada para a Dual MiMo Research Engine...
type nul > STOP.signal
echo Parada solicitada. O orquestrador finalizara apos o ciclo atual.
pause
