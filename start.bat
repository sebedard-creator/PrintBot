@echo off
cd /d "%~dp0server"

echo Demarrage du serveur PrintBot...
start "PrintBot_Server" cmd /c "title PrintBot_Server & .\.venv\Scripts\python.exe app.py & pause"
echo Serveur lance dans une nouvelle fenetre.
