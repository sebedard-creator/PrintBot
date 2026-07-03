# PrintBot - Architecture et Stack Technique

## 1. Vue d'ensemble (Stack)
- **Matériel IoT** : M5Stack ATOM Echo (ESP32 avec microphone, haut-parleur I2S, LED, Wi-Fi).
- **Imprimante** : Niimbot B1 (Thermique, 203 DPI, Bluetooth SPP virtuel sous Windows).
- **Serveur Backend** : Python (Flask, asyncio) tournant localement sur Windows.
- **Interfaces Web** : Vanilla HTML/CSS/JS (mode sombre) avec requêtes asynchrones.
- **Modèles IA** :
  - Whisper (`faster-whisper` local via CTranslate2) pour la transcription STT.
  - Anthropic Claude 3.5 Sonnet pour la compréhension des requêtes et la génération de prompts d'images riches et nuancés (Dithering optimisé).
  - Replicate (Qwen3-TTS / quebec-audio-gen) pour le clonage vocal TTS avec accent québécois et styles directionnels.
  - Replicate (Flux) pour la génération d'images N&B (contours nets ou dégradés selon prompt).

## 2. Structure et Conventions
- Les communications entre l'ESP32 et le serveur se font en UDP (streaming audio brut) et HTTP (API REST pour le statut et la récupération TTS).
- Le backend `app.py` sert l'UI et orchestre les communications.
- `printbot_engine.py` encapsule la logique d'appel aux modèles d'intelligence artificielle (STT, LLM, TTS, Image Gen).
- `conversation_manager.py` gère l'état de la machine (IDLE, CONFIRMING, etc.) et le dictionnaire phonétique (tolérance aux homophones).
- La bibliothèque `niimprint` (patchée) gère le flux binaire d'impression Bluetooth (contrôle de flux et temporisation matérielle).
- **Sécurité** : Les clés API et les ports sont stockés dans `.env`. Aucun secret en dur.
