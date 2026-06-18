from niimprint import PrinterClient, SerialTransport, InfoEnum

ports = ["COM7", "COM8", "COM9"]

for port in ports:
    print(f"\nTentative de connexion serie sur {port}...")
    try:
        transport = SerialTransport(port)
        client = PrinterClient(transport)
        
        print(f">>> Connexion reussie sur {port} ! <<<")
        
        # Demander quelques infos pour verifier la communication
        battery = client.get_info(InfoEnum.BATTERY)
        print(f"Niveau de batterie : {battery}%")
        
        device_type = client.get_info(InfoEnum.DEVICETYPE)
        print(f"Modele de l'imprimante (ID) : {device_type}")
        
        print("\nC'est gagne, la communication est fonctionnelle via Port Serie !")
        break
        
    except Exception as e:
        print(f"[!] Echec sur {port} : {e}")
