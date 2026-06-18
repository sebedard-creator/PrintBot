# -*- coding: utf-8 -*-
import json

p = "Y:/PrintBot/server/voice_library/index.json"
d = json.load(open(p, encoding="utf-8"))
d[0]["transcript"] = "Salut! C'est vraiment super de pouvoir se parler aujourd'hui. Franchement, je me demande bien ce qu'on va pouvoir inventer de beau ensemble ? Quoi qu'il arrive, j'ai super hâte de voir le résultat de notre petite expérience ! Alors... tu es prêt à commencer ?"
d[0]["style"] = "Voix d'un homme adulte, ton enjoué."
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
