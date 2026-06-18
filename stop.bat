@echo off
echo Arret du serveur PrintBot...
taskkill /FI "WINDOWTITLE eq PrintBot_Server*" /T /F
echo Serveur arrete.
pause
