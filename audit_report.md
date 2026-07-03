# 🔍 Audit Complet — PrintBot Codebase

## 🔴 Bugs & Incohérences Critiques

### 1. Double appel à `power_up()` — [app.py:283-284](file:///Y:/PrintBot/server/app.py#L283-L284)
```python
msg = manager.power_up()   # ← résultat assigné à msg, jamais utilisé
text = manager.power_up()  # ← re-appelé, résultat dans text
```
`power_up()` est appelé **deux fois** à chaque boot. Le premier appel reset l'état de la machine, puis le deuxième refait la même chose. La variable `msg` est morte.

---

### 2. Méthode `start_print()` dupliquée — [printer.py](file:///Y:/PrintBot/server/niimprint/printer.py)
La classe `PrinterClient` définit **deux fois** la méthode `start_print()` :
- **Lignes 120-123** : Version 7 octets (page count + color) — celle qu'on avait rétro-ingéniérée de `niim.blue`
- **Lignes 318-320** : Version simple `b"\x01"`

En Python, la deuxième définition **écrase silencieusement** la première. Donc notre correction de protocole 7 octets n'est probablement **jamais exécutée**. C'est potentiellement la source de bugs d'impression futurs.

> [!CAUTION]
> Si l'imprimante fonctionne actuellement, c'est possible que la version simple suffise pour les impressions d'une seule page. Mais si tu veux un jour imprimer en batch, ce bug va resurgir.

---

### 3. `VOICE_ID` — Code mort des deux côtés
- **Arduino** ([AtomEcho_PrintBot.ino:33](file:///Y:/PrintBot/AtomEcho_PrintBot/AtomEcho_PrintBot.ino#L33)) : `VOICE_ID = ""` — initialisé vide et **jamais modifié**.
- L'Arduino envoie `?voice_id=` au serveur (lignes 245-247), mais le serveur **ne lit jamais** ce paramètre dans `/api/device/sync`.
- C'est du code fantôme des deux côtés.

---

### 4. `extract_transcript()` — Fonction morte dans [printbot_engine.py:72-84](file:///Y:/PrintBot/server/printbot_engine.py#L72-L84)
Définie mais **jamais appelée** nulle part. Probablement un vestige de l'époque où le STT passait par Replicate au lieu de faster-whisper local.

---

## 🟡 Incohérences Moyennes

### 5. IP hardcodée `10.0.0.30`
- [app.py:552](file:///Y:/PrintBot/server/app.py#L552) : `app.run(host='10.0.0.30', ...)`
- Devrait être configuré via `.env` (genre `SERVER_HOST`). Si ton IP locale change, le serveur ne démarre plus.

### 6. `import replicate` inutilisé dans app.py
- [app.py:48](file:///Y:/PrintBot/server/app.py#L48) : `import replicate` est importé mais **jamais utilisé directement** dans ce fichier. Tous les appels Replicate passent par `printbot_engine.py`.

### 7. Risque XSS dans l'interface Web
- [index.html:314](file:///Y:/PrintBot/server/templates/index.html#L314) : Les logs serveur sont injectés via `innerHTML` sans sanitisation. Si un log contient du HTML malicieux, il s'exécute.
- [index.html:249](file:///Y:/PrintBot/server/templates/index.html#L249) : Même risque avec le champ `style` des voix.

### 8. Homophones problématiques dans [conversation_manager.py](file:///Y:/PrintBot/server/conversation_manager.py)
- `"en"` → 1, `"on"` → 1, `"de"` → 2 : Ce sont des mots français ultra-courants. En état `CHANGING_VOICE`, une phrase comme *"on veut un cheval"* déclencherait la voix #1 sur le mot "on".
- `"oui"` → 8 : Si l'utilisateur dit "oui" en mode changement de voix, ça sélectionne la voix 8 au lieu de confirmer.

### 9. `.env.example` incomplet
Variables manquantes dans le template : `ACTIVE_VOICE_ID`, `FLASK_DEBUG`, `LABEL_WIDTH_PX`, `LABEL_HEIGHT_PX`.

### 10. `architecture.md` inexact
- Dit "Whisper via Transformers" → le code utilise en fait `faster-whisper` (CTranslate2).
- Dit "Claude pour le dialogue" → Claude ne sert **qu'à** la génération de prompts d'images. Le dialogue est géré par la machine à états de `conversation_manager.py`.

---

## 🟢 Code Mort à Nettoyer (Non Critique)

| # | Fichier | Description |
|---|---------|-------------|
| 1 | `niimprint/printer.py` | Classes `BluetoothTransport` et `TcpTransport` — jamais utilisées |
| 2 | `niimprint/printer.py` | Blocs `match/case` commentés (lignes ~213-221, 280-299) |
| 3 | `niimprint/printer.py` | `import time` / `import math` re-importés dans les méthodes (déjà au top-level) |
| 4 | `requirements.txt` | `numpy` manquant (installé comme dépendance transitive de faster-whisper, mais devrait être explicite) |
| 5 | `.gitignore` | `*.wav` et `*.png` globaux (lignes 23-24) rendent les règles `server/*.wav` et `server/*.png` (lignes 25-26) redondantes |

---

## ✅ Points Positifs Confirmés

| Aspect | Statut |
|--------|--------|
| Aucune clé API en dur | ✅ Tout passe par `.env` |
| `.env` exclu du git | ✅ |
| Clés masquées dans le frontend | ✅ `app.py` masque avant envoi |
| Routes HTML ↔ Flask cohérentes | ✅ Toutes les routes matchent |
| États Arduino ↔ Python cohérents | ✅ `CONFIRMING`, `WAITING_PROMPT`, `IDLE` identiques |
| `voice_library/` exclu du git | ✅ Vie privée protégée |
