import asyncio
from bleak import BleakScanner

async def scan():
    print("Recherche de peripheriques Bluetooth en cours... (Patientez 5 secondes)")
    devices = await BleakScanner.discover(timeout=5.0)
    found_niimbot = False
    
    print("\n--- PERIPHERIQUES TROUVES ---")
    for d in devices:
        name = d.name or "Inconnu"
        print(f"[{d.address}] {name}")
        if "B1" in name.upper() or "NIIMBOT" in name.upper():
            print(f">>> IMPRIMANTE TROUVEE : {name} a l'adresse {d.address} <<<")
            found_niimbot = True
            
    if not found_niimbot:
        print("\n[!] Aucune imprimante Niimbot n'a ete trouvee. Verifie qu'elle est allumee et clignote (mode appairage).")

if __name__ == "__main__":
    asyncio.run(scan())
