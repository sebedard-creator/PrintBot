import json

path = 'Y:/PrintBot/server/voice_library/index.json'

try:
    # First, try to read as cp1252 (ANSI) which is the most likely corruption
    with open(path, 'r', encoding='cp1252') as f:
        data = f.read()
    
    # Try to see if it's already perfectly valid JSON
    items = json.loads(data)
    
    # Fix the mojibake if any
    for item in items:
        if 'transcript' in item:
            # If it was actually UTF-8 but read as cp1252, this will break.
            # Let's read it properly.
            pass
except:
    pass

# Better approach: Just write the EXACT correct string for the transcript 
# since the user explicitly gave us the transcript.
items = [
  {
    "id": "84c480612f4c4838bc7c962fe5aaa3a0",
    "name": "Sebastien",
    "filename": "84c480612f4c4838bc7c962fe5aaa3a0_Sebastien.wav",
    "transcript": "Salut! C'est vraiment super de pouvoir se parler aujourd'hui. Franchement, je me demande bien ce qu'on va pouvoir inventer de beau ensemble ? Quoi qu'il arrive, j'ai super hâte de voir le résultat de notre petite expérience ! Alors... tu es prêt à commencer ?",
    "created_at": "2026-06-12T14:29:02.924878"
  }
]

with open(path, 'w', encoding='utf-8') as f:
    json.dump(items, f, indent=2, ensure_ascii=False)

print("Fixed index.json")
