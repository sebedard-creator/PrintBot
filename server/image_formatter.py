import os
from PIL import Image
import requests
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# Dimensions par defaut: 384x240 pixels (correspond approximativement a une etiquette 50x30mm a 203 DPI)
LABEL_WIDTH = int(os.getenv('LABEL_WIDTH_PX', '384'))
LABEL_HEIGHT = int(os.getenv('LABEL_HEIGHT_PX', '240'))

def format_for_thermal_printer(image_url_or_path, output_filename="print_ready.png"):
    """
    Telecharge l'image, la redimensionne aux dimensions de l'etiquette,
    et la convertit en Noir & Blanc pur (1-bit) via Floyd-Steinberg dithering.
    """
    print(f"[ImageFormatter] Traitement de l'image : {image_url_or_path}")
    
    # 1. Charger l'image (depuis une URL si c'est genere par l'API, ou depuis le disque)
    if isinstance(image_url_or_path, str) and image_url_or_path.startswith('http'):
        # Pour les objets FileOutput de Replicate (replicate >= 0.30.0), il faut ouvrir le flux ou utiliser httpx/requests
        # On essaie d'abord via requests s'il s'agit d'une simple URL
        response = requests.get(image_url_or_path)
        img = Image.open(BytesIO(response.content))
    else:
        # Dans le cas d'un objet FileOutput retourné par Replicate dans les versions récentes
        if hasattr(image_url_or_path, 'read'):
            img = Image.open(BytesIO(image_url_or_path.read()))
        else:
            img = Image.open(image_url_or_path)

    # 1.5 Auto-Trim (Recadrage automatique pour enlever les grandes marges blanches)
    import PIL.ImageOps
    bw_mask = img.convert('L').point(lambda p: 255 if p > 240 else 0)
    inverted_mask = PIL.ImageOps.invert(bw_mask)
    bbox = inverted_mask.getbbox()
    if bbox:
        padding = 15
        left = max(0, bbox[0] - padding)
        upper = max(0, bbox[1] - padding)
        right = min(img.width, bbox[2] + padding)
        lower = min(img.height, bbox[3] + padding)
        img = img.crop((left, upper, right, lower))
        print(f"[ImageFormatter] Auto-crop applique : Nouvelle dimension {img.width}x{img.height}")

    # 2. Redimensionnement (Resize et recadrage/Centrage)
    # On garde le ratio d'aspect
    img_ratio = img.width / img.height
    target_ratio = LABEL_WIDTH / LABEL_HEIGHT
    
    if img_ratio > target_ratio:
        # L'image est plus large proportionnellement, on la contraint par la largeur
        new_width = LABEL_WIDTH
        new_height = int(new_width / img_ratio)
    else:
        # L'image est plus haute proportionnellement, on la contraint par la hauteur
        new_height = LABEL_HEIGHT
        new_width = int(new_height * img_ratio)
        
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Centrage sur un canvas blanc aux dimensions exactes
    canvas = Image.new('RGB', (LABEL_WIDTH, LABEL_HEIGHT), (255, 255, 255))
    x_offset = (LABEL_WIDTH - new_width) // 2
    y_offset = (LABEL_HEIGHT - new_height) // 2
    canvas.paste(img, (x_offset, y_offset))
    
    # 3. Binarisation (Noir et Blanc strict sans Dithering)
    # Le Dithering (Floyd-Steinberg) détruit le "line art" en transformant les lignes grises en points.
    # On utilise un seuil (threshold) strict : tout ce qui est plus sombre que 200 devient noir, le reste blanc.
    img_gray = canvas.convert('L')
    img_1bit = img_gray.point(lambda p: 255 if p > 200 else 0).convert('1', dither=Image.Dither.NONE)
    
    # 4. Sauvegarde
    img_1bit.save(output_filename, format="PNG")
    print(f"[ImageFormatter] Image 1-bit prete pour impression sauvegardee sous : {output_filename}")
    return output_filename

