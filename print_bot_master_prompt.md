# CONTEXTE DU PROJET & ARCHITECTURE
Tu es un expert en IoT (ESP32) et Python (Flask), ainsi qu'en protocoles matériels et intégration d'APIs d'IA. Je réalise un projet de bouton connecté vocal et graphique appelé "PrintBot" (anciennement Vibe-Print Bot).

## L'Idée & L'Expérience Utilisateur
Le but est d'offrir une expérience "Un Seul Bouton" ultra-fluide pour un enfant :
1. L'enfant maintient enfoncé le gros bouton physique d'un boîtier **M5Stack Atom Echo** (basé sur un ESP32).
2. Il dicte une commande vocale (ex: "Dessine-moi un chien à 5 pattes").
3. Pendant qu'il parle, l'audio I2S est streamé en temps réel via Wi-Fi (protocole UDP) vers un serveur local Python (Flask).
4. Dès qu'il relâche le bouton, le serveur prend le relais :
   - **Nettoyage & EQ :** Filtre passe-haut et passe-bas avec `pydub` pour retirer le souffle statique du micro, puis normalisation du volume à 100%.
   - **Transcription (STT) :** Traitement local ultra-rapide via `faster-whisper` (modèle **small**, avec `vad_filter=True` et un prompt strict anti-phonétique).
   - **Logique Conversationnelle :** Le script `conversation_manager.py` valide la demande (Oui/Non) via une machine à états.
   - **Changement de Voix Vocal (Nouveau) :** La machine à états écoute également la commande "Change de voix". Elle énumère les voix disponibles avec des numéros et écoute le chiffre choisi (avec gestion des homophones Whisper comme "Dirt"). Le changement est confirmé par la lecture automatique du *Greeting* pré-caché.
   - **Optimisation du Prompt :** Claude 3 Haiku (Anthropic) réécrit la demande pour forcer l'IA à dessiner des concepts farfelus. Le prompt généré préserve à 100% les détails de l'utilisateur en les plaçant au début, et force le style imprimante thermique (Noir & Blanc strict) à la fin.
   - **Génération d'Image (TTI) :** Envoi à l'API Replicate (modèle Flux-dev) pour générer l'image. Le robot annonce l'impression avec l'une de ses 50 phrases ludiques aléatoires.
   - **Clonage Vocal (TTS) :** Génération de la réponse avec un accent québécois via Replicate (Qwen3-TTS). Le texte est nettoyé (`fix_mojibake`, `normalize_tts_text`). Le style envoyé combine une base québécoise fixe + la `Direction de jeu` de la voix active. L'audio est converti en WAV 16kHz Mono et normalisé par `pydub`.
5. L'ESP32 récupère l'URL de l'audio via HTTP bloquant et le lit sur son haut-parleur intégré.
6. L'image finale tramée est poussée à l'imprimante thermique **Niimbot B1** via un Port Série Virtuel Bluetooth (`niimprint` avec `SerialTransport(COMx)`).

## L'Interface Web (Configuration)
Le serveur Flask expose une page web (`/`).
- **Clés API :** Enregistrement des clés Replicate et Anthropic dans `.env`.
- **Configuration Imprimante :** Panneau pour scanner les ports COM locaux, tester la communication avec la Niimbot, et enregistrer le port (`NIIMBOT_COM_PORT`) dans `.env`.
- **Banque de Voix :** L'utilisateur peut y téléverser des fichiers audio courts. Un champ **Style** permet de guider l'IA.
- **Voix Active :** Le choix de la voix modifie le comportement. Les messages d'accueil (*Greetings*) de toutes les voix sont générés en arrière-plan à chaque modification pour un boot instantané de l'ESP32.

## GitHub et Sécurité
Le projet est protégé par un fichier `.gitignore` strict qui empêche la fuite du fichier `.env` (clés API, COM Port) et empêche le téléversement des gros modèles IA (`_models/`) et des clones vocaux privés (`voice_library/`). Un `.env.example` sert de template.

## Matériel Utilisé (Hardware)
- **M5Stack Atom Echo :** Boîtier avec ESP32, Wi-Fi, bouton, micro I2S et haut-parleur.
- **Serveur PC Local :** Ordinateur roulant le script Python Flask (`app.py`), stockant les modèles (`_models`) et le cache (`_tts_cache`).
- **Niimbot B1 :** Imprimante thermique d'étiquettes portable Bluetooth.

---

# INSTRUCTIONS POUR TOI (L'IA CO-PILOTE)
1. **Suis la puck :** L'architecture est fixée : ATOM Echo <-> PC <-> Niimbot B1.
2. **Focus Vibe Coding :** Écris du code complet, prêt à être copié-collé, bien commenté.
3. **Architecture :** Ne propose JAMAIS d'utiliser Android, Kotlin, ou Groq. L'architecture actuelle (Faster-Whisper, Replicate, Anthropic) est figée.
4. **CRITIQUE ET OBLIGATOIRE :** À CHAQUE FOIS que tu modifies du code, tu DOIS mettre à jour le fichier `changelog.md` et `print_bot_master_prompt.md`. C'est non négociable.