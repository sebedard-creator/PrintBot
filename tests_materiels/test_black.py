import os
from dotenv import load_dotenv
from niimprint import PrinterClient, SerialTransport
from PIL import Image

load_dotenv('Y:/PrintBot/server/.env')
port = os.getenv('NIIMBOT_COM_PORT')
print(f'Tentative sur {port}...')
transport = SerialTransport(port)
client = PrinterClient(transport)

# Create a solid black image 384x240
img = Image.new('1', (384, 240), 0)  # 0 is black in 1-bit

client.print_image(img, density=5)  # Max density
print('Impression image toute noire lancee !')
