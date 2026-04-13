@echo off
echo ================================================
echo    Calas de Almeria - Compilar a .EXE
echo ================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado.
    pause
    exit /b 1
)

echo [1/3] Instalando PyInstaller...
python -m pip install pyinstaller --quiet

echo [2/3] Compilando... (puede tardar 3-5 minutos)
echo.
python -m PyInstaller calasdealmeria.spec --clean

if %errorlevel% neq 0 (
    echo.
    echo ERROR durante la compilacion.
    pause
    exit /b 1
)

echo.
echo ================================================
echo  COMPILACION COMPLETADA
echo.
echo  El ejecutable esta en:
echo  dist\calasdealmeria.exe
echo.
echo  Copia ese archivo al PC de tu padre.
echo ================================================
echo.
pause
