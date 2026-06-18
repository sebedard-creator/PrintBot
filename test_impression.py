import os
from dotenv import load_dotenv
from niimprint import PrinterClient, SerialTransport
from PIL import Image, ImageDraw

# Charger le port COM depuis le .env
load_dotenv(os.path.join(os.path.dirname(__file__), 'server', '.env'))
port = os.getenv('NIIMBOT_COM_PORT')

if not port:
    print("Aucun port COM n'est configure. Va d'abord tester et sauvegarder le port dans l'interface web.")
    exit(1)

print(f"Creation d'une petite image de test...")
# Creer une image blanche toute simple (ex: 200x200 pixels)
img = Image.new('1', (200, 200), 1)
draw = ImageDraw.Draw(img)
# Dessiner un gros X noir
draw.line((0, 0, 200, 200), fill=0, width=5)
draw.line((0, 200, 200, 0), fill=0, width=5)

print(f"Tentative d'envoi de l'image a la Niimbot sur le port {port}...")
try:
    transport = SerialTransport(port)
    client = PrinterClient(transport)
    
    # Envoi de l'ordre d'impression !
    client.print_image(img, density=3)
    print("\n>>> SUCCES ! L'image a ete envoyee a l'imprimante. <<<")
    print("L'imprimante devrait faire du bruit, puis probablement clignoter en rouge car elle n'a pas de papier.")
    
except Exception as e:
    print(f"\n[!] Erreur lors de l'envoi : {e}")
