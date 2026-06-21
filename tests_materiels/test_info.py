import os
from dotenv import load_dotenv
from niimprint import PrinterClient, SerialTransport, InfoEnum

load_dotenv('Y:/PrintBot/server/.env')
port = os.getenv('NIIMBOT_COM_PORT')
transport = SerialTransport(port)
client = PrinterClient(transport)

print("--- NIIMBOT INFO ---")
for info in InfoEnum:
    try:
        val = client.get_info(info)
        print(f"{info.name}: {val}")
    except Exception as e:
        print(f"{info.name}: ERROR")
