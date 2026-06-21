from niimprint import PrinterClient, BluetoothTransport, InfoEnum

try:
    print("Tentative de connexion Bluetooth native...")
    transport = BluetoothTransport("03:07:12:69:DB:6E")
    client = PrinterClient(transport)
    batt = client.get_info(InfoEnum.BATTERY)
    print(f"SUCCES! Batterie: {batt}")
except Exception as e:
    print(f"ERREUR: {e}")
