import os
from dotenv import load_dotenv
load_dotenv()
import printbot_engine

try:
    text = "Salut Octave. Dis-moi, qu'est-ce que tu aimerais qu'on dessine aujourd'hui ?"
    ref_audio = "Y:/PrintBot/server/voice_library/84c480612f4c4838bc7c962fe5aaa3a0_Sebastien.wav"
    ref_text = "Salut! C'est vraiment super de pouvoir se parler aujourd'hui. Franchement, je me demande bien ce qu'on va pouvoir inventer de beaux ensemble. Quoi qu'il arrive, j'ai super hâte de voir le résultat de notre petite expérience. Alors, tu es prêt à commencer?"
    
    url = printbot_engine.clone_voice(text, ref_audio, ref_text)
    print(f"Success! URL/Path: {url}")
except Exception as e:
    print(f"Error: {e}")
