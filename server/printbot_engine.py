import os
import json
import time
import hashlib
import requests
import replicate
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

# Load environment variables
load_dotenv()

# --- Variables Globales ---
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        print("[Engine] Chargement du modele faster-whisper en memoire (small, int8)...")
        models_dir = os.path.join(os.path.dirname(__file__), "_models")
        os.makedirs(models_dir, exist_ok=True)
        _whisper_model = WhisperModel(
            "small", 
            device="cpu", 
            compute_type="int8", 
            download_root=models_dir
        )
    return _whisper_model

def warmup_engine():
    try:
        print("[Engine] Echauffement des modeles IA en cours (cela peut prendre quelques secondes)...")
        model = get_whisper_model()
        # Lancer une transcription bidon pour forcer le telechargement du VAD
        import numpy as np
        dummy_audio = np.zeros(16000, dtype=np.float32) # 1 sec silence
        model.transcribe(dummy_audio, language='fr')
        print("[Engine] Echauffement IA termine. Pret !")
    except Exception as e:
        print(f"[Engine] Erreur lors de l'echauffement: {e}")

# --- Speech to Text ---
def transcribe_audio(audio_file_path, language='fr'):
    """
    Transcrit un fichier audio localement avec faster-whisper.
    """
    model = get_whisper_model()
    # Amorce pour forcer le dictionnaire français et éviter l'orthographe phonétique québécoise ("krakradil")
    prompt = "Ceci est une dictée vocale en français avec une orthographe parfaite. Mots courants: crocodile, alligator, cheval, lapin, chat, chien, robot." if language == 'fr' else "Exact transcription."
    
    print(f"[Engine] Transcription locale en cours pour {audio_file_path}...")
    segments, _ = model.transcribe(
        audio_file_path,
        language=language,
        beam_size=5,
        condition_on_previous_text=False,
        initial_prompt=prompt,
        vad_filter=True, # Active Silero VAD pour ignorer le bruit de fond et le souffle !
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    seg_list = list(segments)
    print(f"[Engine] DEBUG SEGMENTS TROUVES: {len(seg_list)}")
    for s in seg_list:
        print(f"[Engine] - '{s.text}' (confiance: {s.no_speech_prob})")
        
    transcript = " ".join(segment.text.strip() for segment in seg_list if segment.text.strip())
    print(f"[Engine] DEBUG TRANSCRIPT FINAL: '{transcript}'")
    return transcript.strip()

def extract_transcript(output):
    """Extrait le texte de la réponse de Replicate."""
    if isinstance(output, str):
        return output.strip()
    if isinstance(output, dict):
        for key in ('transcription', 'text', 'output'):
            value = output.get(key)
            if value:
                return extract_transcript(value)
    if hasattr(output, '__iter__') and not isinstance(output, dict):
        # Pour les flux (streams) ou listes
        text = ''.join(str(item) for item in output if item)
        return text.strip()
def fix_mojibake(text):
    """Copie exacte de quebec-audio-gen : repare les accents corrompus latin1->utf8."""
    if not isinstance(text, str):
        return text
    markers = ('Ã', 'Â', 'Å')  # Les vrais marqueurs mojibake latin1
    if not any(marker in text for marker in markers):
        return text
    try:
        fixed = text.encode('latin1').decode('utf-8')
    except UnicodeError:
        return text

    old_score = sum(text.count(marker) for marker in markers)
    new_score = sum(fixed.count(marker) for marker in markers)
    return fixed if new_score < old_score else text


def normalize_tts_text(text):
    """Copie exacte de quebec-audio-gen : normalise les espaces dans le texte de reference."""
    return ' '.join(text.split())


def clone_voice(text, reference_audio_path, reference_text="", custom_style="", cache_filename=None, language="fr"):
    """
    Clone une voix pour lire un texte donné en utilisant l'API Replicate avec système de cache.
    On utilise qwen3-tts pour forcer l'accent québécois via les instructions de style.
    """
    text = fix_mojibake(text)
    reference_text = fix_mojibake(reference_text)
    reference_text = normalize_tts_text(reference_text)

    cache_dir = os.path.join(os.path.dirname(__file__), "_tts_cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    if cache_filename:
        cache_file = os.path.join(cache_dir, cache_filename)
    else:
        # Utilisation d'un MD5 combine (texte + chemin de la voix) pour que le cache soit unique par voix
        hash_str = f"{text}_{os.path.basename(reference_audio_path)}"
        cache_file = os.path.join(cache_dir, hashlib.md5(hash_str.encode('utf-8')).hexdigest() + ".wav")
    
    if os.path.exists(cache_file):
        print(f"[Engine] TTS charge depuis le cache : {text}")
        return cache_file
        
    print(f"[Engine] TTS generation via Replicate pour : {text}")
    model = os.getenv(
        'REPLICATE_TTS_MODEL',
        'qwen/qwen3-tts:0b366549c7541af95a69454651f4ebf02c699036841cd20b78b9e2a26b4b2750'
    )
    
    # Copie STRICTE de la logique de quebec-audio-gen pour éviter les hallucinations de genre
    base_style = "Parle en français québécois naturel, avec une diction claire, un accent québécois crédible et aucune cadence française de France."
    if custom_style:
        style_instruction = f"{base_style} Direction de jeu: {custom_style}"
    else:
        style_instruction = base_style
        
    client = replicate.Client(api_token=os.getenv('REPLICATE_API_KEY'))
    
    # Boucle de retry pour gerer le Rate Limit (Erreur 429)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with open(reference_audio_path, 'rb') as ref_audio:
                output = client.run(
                    model,
                    input={
                        "text": text,
                        "mode": "voice_clone",
                        "language": "French",
                        "reference_audio": ref_audio,
                        "reference_text": reference_text,
                        "style_instruction": style_instruction
                    }
                )
            break # Succès, on sort de la boucle
        except replicate.exceptions.ReplicateError as e:
            error_str = str(e).lower()
            if "429" in error_str or "throttled" in error_str:
                if attempt < max_retries - 1:
                    print(f"[Engine] Rate limit atteint pour TTS. Pause de 10 secondes avant reessai...")
                    time.sleep(10)
                else:
                    raise Exception("Le quota de requêtes Replicate a été dépassé trop de fois pour l'audio (Rate Limit). Veuillez réessayer plus tard ou augmenter votre solde.")
            else:
                raise e
        
    # Extraction propre de l'URL du fichier audio
    url = ""
    if hasattr(output, 'url'):
        url = output.url
    elif hasattr(output, '__iter__') and not isinstance(output, (dict, str)):
        out_list = list(output)
        if out_list:
            first = out_list[0]
            url = first.url if hasattr(first, 'url') else str(first).strip()
    else:
        url = str(output).strip()
    
    if url.startswith("http"):
        response = requests.get(url)
        with open(cache_file, 'wb') as f:
            f.write(response.content)
            
        # Normalisation de la voix générée (Volume maximum avant distorsion)
        try:
            from pydub import AudioSegment
            from pydub.effects import normalize as pydub_normalize
            
            print("[Engine] Normalisation audio (TTS) en cours...")
            audio_seg = AudioSegment.from_file(cache_file)
            audio_seg = pydub_normalize(audio_seg)
            # L'ESP32 utilise AudioGeneratorWAV, il FAUT un fichier WAV (même si l'extension dit .mp3)
            # On force en mono 16kHz pour être parfaitement compatible et rapide.
            audio_seg = audio_seg.set_channels(1).set_frame_rate(16000)
            audio_seg.export(cache_file, format="wav")
        except Exception as e:
            print(f"[Engine] Avertissement: Normalisation echouee ({e})")
            
        return cache_file
        
    return url

# --- Image Generation ---
def generate_image(prompt_text):
    """
    Genere une image via l'API Replicate (Text-to-Image) adaptee pour une imprimante thermique.
    On utilise Anthropic pour faire du Prompt Engineering avancé et forcer l'anatomie bizarre.
    """
    model = os.getenv(
        'REPLICATE_IMAGE_MODEL',
        'black-forest-labs/flux-dev'
    )
    
    # Utilisation de Claude pour optimiser le prompt et forcer les absurdités
    try:
        import anthropic
        claude = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        system_msg = (
            "You are an expert Prompt Engineer for strict image generation models (like Flux). "
            "CRITICAL RULE 1: You MUST PRESERVE EVERY SINGLE DETAIL from the user's request. Do not drop any elements, characters, or actions, no matter how complex. Put the detailed description of the scene at the VERY BEGINNING of the prompt. "
            "CRITICAL RULE 2: The final image MUST BE PURE BLACK AND WHITE for a thermal printer. You MUST STRIP OUT ANY MENTION OF COLORS from the user's request. "
            "If the user asks for a 'red logo', rewrite it to 'a black and white line art version of the logo'. Do not use color words. "
            "CRITICAL RULE 3: If they ask for weird anomalies (e.g., a 5-legged dog), ENHANCE the prompt to FORCE the model to draw it using heavy emphasis. "
            "FORMAT: Output ONLY the english prompt. Start with the highly detailed subject. Then, ALWAYS append this exact style at the very end: "
            "'Detailed black and white illustration. Rich shading, soft gradients, halftones, or stippling are encouraged to give depth and volume. No pure flat outlines, use beautiful greyscale shading.'"
        )
        # Récupération dynamique des modèles disponibles sur ce compte pour éviter les 404
        try:
            available_models = [m.id for m in claude.models.list().data]
            haiku_models = [m for m in available_models if "haiku" in m]
            sonnet_models = [m for m in available_models if "sonnet" in m]
            models_to_try = haiku_models + sonnet_models
            if not models_to_try:
                models_to_try = available_models
        except Exception as e:
            # Fallback en dur si l'endpoint models.list() échoue
            print(f"[Engine] Impossible de lister les modèles : {e}")
            models_to_try = [
                "claude-haiku-4-5-20251001",
                "claude-3-5-haiku-20241022",
                "claude-3-haiku-20240307"
            ]
        
        response = None
        last_error = None
        for model_name in models_to_try:
            try:
                print(f"[Engine] Tentative avec le modele Anthropic: {model_name}...")
                response = claude.messages.create(
                    model=model_name,
                    max_tokens=200,
                    system=system_msg,
                    messages=[
                        {"role": "user", "content": f"User request: {prompt_text}\n\nReturn ONLY the english prompt, nothing else."}
                    ]
                )
                break # On a trouvé un modèle qui marche
            except anthropic.NotFoundError as e:
                last_error = e
                print(f"[Engine] Modele Anthropic {model_name} non disponible (404), tentative avec le prochain...")
                continue
                
        if not response:
            raise Exception(f"Aucun modele Anthropic disponible n'a fonctionne. Derniere erreur : {last_error}")
            
        full_prompt = response.content[0].text.strip()
        print(f"[Engine] Prompt optimisé par Claude : {full_prompt}")
    except Exception as e:
        print(f"[Engine] Erreur avec Anthropic, fallback sur la traduction basique : {e}")
        english_prompt = GoogleTranslator(source='auto', target='en').translate(prompt_text)
        system_style = "Clean contour line drawing, black ink on pure white paper, uniform line thickness, unshaded. No solid black fills, no crosshatching, no stippling, pure outlines only. EXTREMELY IMPORTANT: exactly follow all weird anatomical details requested (like 5 legs)."
        full_prompt = f"{english_prompt}, {system_style}"
    
    client = replicate.Client(api_token=os.getenv('REPLICATE_API_KEY'))
    
    # Boucle de retry pour gerer le Rate Limit (Erreur 429)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"[Engine] Generation d'image (Tentative {attempt + 1}/{max_retries})...")
            output = client.run(
                model,
                input={
                    "prompt": full_prompt,
                    "output_format": "png",
                    "guidance": 3.5,
                    "num_inference_steps": 28
                }
            )
            
            # L'output est generalement une liste d'URLs pour FLUX/SDXL
            if isinstance(output, list) and len(output) > 0:
                return output[0]
            return output
            
        except replicate.exceptions.ReplicateError as e:
            error_str = str(e).lower()
            if "429" in error_str or "throttled" in error_str:
                if attempt < max_retries - 1:
                    print(f"[Engine] Rate limit atteint. Pause de 10 secondes avant reessai...")
                    time.sleep(10)
                else:
                    raise Exception("Le quota de requêtes Replicate a été dépassé trop de fois (Rate Limit). Veuillez réessayer plus tard ou augmenter votre solde.")
            else:
                raise e


