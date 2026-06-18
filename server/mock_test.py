import os
from dotenv import load_dotenv
load_dotenv()

import printbot_engine
import replicate

# Mock replicate.Client.run
class MockClient:
    def __init__(self, **kwargs):
        pass
    def run(self, model, input):
        print("====== REPLICATE INPUT MOCK ======")
        print(f"Model: {model}")
        for k, v in input.items():
            if k == 'reference_audio':
                print(f"{k}: <file handle>")
            else:
                print(f"{k}: {repr(v)}")
        print("==================================")
        return "http://fake-url.com/fake.wav"

replicate.Client = MockClient

try:
    text = "Salut Octave. Dis-moi, qu'est-ce que tu aimerais qu'on dessine aujourd'hui ?"
    ref_audio = "Y:/PrintBot/server/voice_library/84c480612f4c4838bc7c962fe5aaa3a0_Sebastien.wav"
    ref_text = "Salut! C'est vraiment super de pouvoir se parler aujourd'hui. Franchement, je me demande bien ce qu'on va pouvoir inventer de beaux ensemble. Quoi qu'il arrive, j'ai super hâte de voir le résultat de notre petite expérience. Alors, tu es prêt à commencer?"
    
    # Bypass cache by changing text
    import uuid
    url = printbot_engine.clone_voice(text + str(uuid.uuid4()), ref_audio, ref_text)
except Exception as e:
    print(f"Error: {e}")
