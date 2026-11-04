@echo off
title Corretor Automatico de Provas - A3 UNIFACS
echo ===================================================================
echo     CORRETOR AUTOMATICO DE PROVAS OBJETIVAS (PROJETO A3)
echo ===================================================================
echo.
echo [1/2] Verificando dependencias e arquivos...
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=python
) else (
    set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
)

echo [2/2] Iniciando servidor web na porta 5000...
echo.
echo Abra o seu navegador e acesse:
echo     http://localhost:5000
echo.
echo Para encerrar o servidor, pressione Ctrl + C.
echo ===================================================================
%PY_CMD% app.py
pause

