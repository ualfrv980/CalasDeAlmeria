@echo off
echo ================================================
echo    Calas de Almeria - Ejecutar
echo ================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado.
    echo Descarga Python desde https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Instalando dependencias...
python -m pip install PySide6 --quiet

echo Iniciando Calas de Almeria...
echo.
python main.py

pause
