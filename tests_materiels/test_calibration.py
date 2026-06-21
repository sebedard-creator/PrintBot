import sys
from PIL import Image, ImageDraw
import niimprint

print("Creation de l'image de calibration 384x320...")
width = 384  # Printhead width for B1 (48mm)
height = 240 # True physical size for 30mm label

# 1 is white background (blank)
img = Image.new('1', (width, height), 1)
draw = ImageDraw.Draw(img)

# Outline box (black ink = 0)
draw.rectangle([2, 2, width-3, height-3], outline=0, width=4)

# X corner to corner
draw.line([2, 2, width-3, height-3], fill=0, width=4)
draw.line([2, height-3, width-3, 2], fill=0, width=4)

# Center circle
center_x, center_y = width // 2, height // 2
radius = 50
draw.ellipse([center_x - radius, center_y - radius, center_x + radius, center_y + radius], outline=0, width=4)

img.save("test_generated.png")

print("Tentative d'envoi a l'imprimante...")
printer = niimprint.PrinterClient(niimprint.SerialTransport("COM8"))
printer.print_image(img, density=3)
print("\n>>> SUCCES ! L'image de calibration a ete envoyee <<<")
