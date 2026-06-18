# -*- coding: utf-8 -*-
import printbot_engine

res = printbot_engine.clone_voice(
    text="C'est parti, je l'imprime tout de suite.",
    reference_audio_path="Y:/PrintBot/server/voice_library/84c480612f4c4838bc7c962fe5aaa3a0_Sebastien.wav",
    reference_text="Salut! C'est vraiment super de pouvoir se parler aujourd'hui. Franchement, je me demande bien ce qu'on va pouvoir inventer de beaux ensemble. Quoi qu'il arrive, j'ai super hâte de voir le résultat de notre petite expérience. Alors, tu es prêt à commencer?",
    custom_style="Voix d'un homme adulte, ton naturel."
)
print("Result: " + res)
