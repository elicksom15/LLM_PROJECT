@echo off
cd /d "%~dp0"
echo Removendo sinal de PAUSA...
if exist PAUSE.signal del PAUSE.signal
echo Pesquisa retomada!
