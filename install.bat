@echo off
color 0A
echo ==========================================
echo      INSTALLATION DE PRINTBOT
echo ==========================================
echo.

cd /d "%~dp0server"

echo [1/3] Creation de l'environnement virtuel (.venv)...
python -m venv .venv
if %errorlevel% neq 0 (
    echo.
    color 0C
    echo [ERREUR] Impossible de creer l'environnement virtuel. 
    echo Verifiez que Python est bien installe et ajoute au PATH.
    pause
    exit /b
)

echo.
echo [2/3] Activation et mise a jour de pip...
call .venv\Scripts\activate.bat
python.exe -m pip install --upgrade pip

echo.
echo [3/3] Installation des dependances...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    color 0C
    echo [ERREUR] Un probleme est survenu lors de l'installation des librairies.
    pause
    exit /b
)

echo.
echo ==========================================
echo   INSTALLATION TERMINEE AVEC SUCCES !
echo ==========================================
echo.
echo Vous pouvez maintenant lancer start.bat
pause
