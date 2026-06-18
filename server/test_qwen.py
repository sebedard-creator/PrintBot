# -*- coding: utf-8 -*-
import replicate
import os
from dotenv import load_dotenv

load_dotenv()

client = replicate.Client(api_token=os.getenv("REPLICATE_API_KEY"))
ref_audio_path = "Y:/PrintBot/server/voice_library/84c480612f4c4838bc7c962fe5aaa3a0_Sebastien.wav"

with open(ref_audio_path, "rb") as ref_audio:
    output = client.run(
        "qwen/qwen3-tts:0b366549c7541af95a69454651f4ebf02c699036841cd20b78b9e2a26b4b2750",
        input={
            "text": "C'est parti, je l'imprime tout de suite.",
            "mode": "voice_clone",
            "language": "French",
            "reference_audio": ref_audio,
            "reference_text": "Salut! C'est vraiment super de pouvoir se parler aujourd'hui. Franchement, je me demande bien ce qu'on va pouvoir inventer de beaux ensemble. Quoi qu'il arrive, j'ai super hâte de voir le résultat de notre petite expérience. Alors, tu es prêt à commencer?",
            "style_instruction": "Parle en français québécois naturel, avec une diction claire, un accent québécois crédible et aucune cadence française de France. Direction de jeu: Voix d'un homme adulte, ton naturel."
        }
    )
print("Output URL:", output)
