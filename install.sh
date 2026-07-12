#!/bin/bash
echo "=========================================="
echo "     INSTALLATION DE PRINTBOT (MAC)"
echo "=========================================="
echo ""

cd "$(dirname "$0")/server" || exit

echo "[1/4] Creation de l'environnement virtuel (.venv)..."
python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo -e "\033[0;31m[ERREUR] Impossible de creer l'environnement virtuel."
    echo -e "Verifiez que Python 3 est bien installe.\033[0m"
    exit 1
fi

echo ""
echo "[2/4] Activation et mise a jour de pip..."
source .venv/bin/activate
pip install --upgrade pip

echo ""
echo "[3/4] Installation de FFmpeg (Requis pour l'audio)..."
if command -v brew &> /dev/null; then
    brew install ffmpeg
else
    echo "Homebrew non trouve. Veuillez installer ffmpeg manuellement."
fi

echo ""
echo "[4/4] Installation des dependances..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "\033[0;31m[ERREUR] Un probleme est survenu lors de l'installation des librairies.\033[0m"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo ""
    echo "[4/4] Creation du fichier .env par defaut..."
    cp .env.example .env
    echo -e "\033[1;33m[ATTENTION] N'oubliez pas d'ouvrir le fichier .env et d'y ajouter vos cles API !\033[0m"
fi

echo ""
echo "=========================================="
echo "  INSTALLATION TERMINEE AVEC SUCCES !     "
echo "=========================================="
echo ""
echo "Vous pouvez maintenant lancer ./start.sh"
