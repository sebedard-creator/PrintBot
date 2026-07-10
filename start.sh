#!/bin/bash
cd "$(dirname "$0")/server" || exit

echo "Lancement du serveur PrintBot..."
source .venv/bin/activate
python3 app.py
