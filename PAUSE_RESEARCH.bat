@echo off
cd /d "%~dp0"
echo Gravando sinal de PAUSA...
type nul > PAUSE.signal
echo Pesquisa pausada. Para retomar, execute RESUME_RESEARCH.bat
