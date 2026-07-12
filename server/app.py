import os
import json
import uuid
import time
import socket
import threading
import wave
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect
from werkzeug.utils import secure_filename
from dotenv import load_dotenv, set_key
from collections import deque
import sys
from serial.tools.list_ports import comports as list_comports
try:
    from niimprint import PrinterClient, SerialTransport, InfoEnum
except ImportError:
    pass

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

class LogCatcher:
    def __init__(self, max_lines=500):
        self.logs = deque(maxlen=max_lines)
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.lock = threading.Lock()
        
    def write(self, message):
        self.original_stdout.write(message)
        if message:
            with self.lock:
                for line in message.splitlines():
                    if line.strip():
                        self.logs.append(line.strip())
                
    def flush(self):
        self.original_stdout.flush()

log_catcher = LogCatcher()
sys.stdout = log_catcher
sys.stderr = log_catcher

import printbot_engine
import image_formatter
import conversation_manager

manager = conversation_manager.ConversationManager()

# Desactiver les logs d'acces HTTP de Flask (Werkzeug) pour eviter le spam de /api/logs
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

@app.route('/api/logs')
def get_logs():
    with log_catcher.lock:
        return jsonify({'logs': list(log_catcher.logs)})

VOICE_LIBRARY_DIR = os.path.join(app.root_path, 'voice_library')
VOICE_LIBRARY_INDEX = os.path.join(VOICE_LIBRARY_DIR, 'index.json')
ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.m4a'}

def ensure_voice_library():
    os.makedirs(VOICE_LIBRARY_DIR, exist_ok=True)
    if not os.path.exists(VOICE_LIBRARY_INDEX):
        with open(VOICE_LIBRARY_INDEX, 'w', encoding='utf-8') as f:
            json.dump([], f)

def load_voice_library():
    ensure_voice_library()
    with open(VOICE_LIBRARY_INDEX, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_voice_library(items):
    ensure_voice_library()
    with open(VOICE_LIBRARY_INDEX, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def precache_all_greetings():
    items = load_voice_library()
    if not items: return
    text = "Salut Octave. Dis-moi, qu'est-ce que tu aimerais qu'on crée ensemble aujourd'hui ?"
    for item in items:
        try:
            ref_audio = os.path.join(VOICE_LIBRARY_DIR, item['filename'])
            custom_style = item.get('style', "Voix d'un homme adulte, ton naturel.")
            safe_name = secure_filename(item['name']) or 'voice'
            cache_filename = f"greeting_{safe_name}.wav"
            print(f"[Cache] Verification/Generation pour: {item['name']}")
            printbot_engine.clone_voice(text, ref_audio, item.get('transcript', ''), custom_style, cache_filename=cache_filename)
        except Exception as e:
            print(f"[Cache] Erreur pour {item['name']} : {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/voice-library', methods=['GET'])
def list_voices():
    voices = load_voice_library()
    return jsonify({'voices': voices})

@app.route('/voice-library', methods=['POST'])
def save_voice():
    name = (request.form.get('name') or '').strip()
    style = (request.form.get('style') or '').strip()
    audio_file = request.files.get('audio_reference')

    if not name:
        return jsonify({'error': 'Le nom de la voix est requis.'}), 400
    if not audio_file:
        return jsonify({'error': 'Un fichier audio est requis.'}), 400

    ext = os.path.splitext(audio_file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Format non supporté. Autorisés : {ALLOWED_EXTENSIONS}'}), 400

    voice_id = uuid.uuid4().hex
    safe_name = secure_filename(name) or 'voice'
    filename = f"{voice_id}_{safe_name}{ext}"
    
    ensure_voice_library()
    filepath = os.path.join(VOICE_LIBRARY_DIR, filename)
    audio_file.save(filepath)
    
    # Transcription automatique pour Qwen3-TTS
    try:
        transcript = printbot_engine.transcribe_audio(filepath)
    except Exception as e:
        print(f"Erreur de transcription pour la voix : {e}")
        transcript = ""

    item = {
        'id': voice_id,
        'name': name,
        'style': style if style else "Voix d'un homme adulte, ton naturel.",
        'filename': filename,
        'transcript': transcript,
        'created_at': datetime.now().isoformat()
    }

    items = load_voice_library()
    items.append(item)
    save_voice_library(items)
    
    # Pre-generer le greeting pour cette nouvelle voix (en arriere-plan)
    threading.Thread(target=precache_all_greetings, daemon=True).start()

    return jsonify({'success': True, 'voice_id': voice_id}), 201

@app.route('/voice-library/<voice_id>/audio', methods=['GET'])
def get_voice_audio(voice_id):
    items = load_voice_library()
    item = next((i for i in items if i['id'] == voice_id), None)
    
    if not item:
        return jsonify({'error': 'Voix introuvable.'}), 404

    filepath = os.path.join(VOICE_LIBRARY_DIR, item['filename'])
    if not os.path.exists(filepath):
        return jsonify({'error': 'Fichier audio introuvable.'}), 404

    return send_file(filepath)

@app.route('/voice-library/<voice_id>/style', methods=['POST'])
def update_voice_style(voice_id):
    data = request.get_json()
    new_style = data.get('style', '').strip()
    if not new_style:
        return jsonify({'error': 'Le style ne peut pas etre vide.'}), 400
        
    items = load_voice_library()
    item = next((i for i in items if i['id'] == voice_id), None)
    if not item:
        return jsonify({'error': 'Voix introuvable.'}), 404
        
    item['style'] = new_style
    save_voice_library(items)
    
    # Re-générer le cache pour cette voix avec le nouveau style
    threading.Thread(target=precache_all_greetings, daemon=True).start()
    
    return jsonify({'success': True, 'style': new_style})

@app.route('/api-key', methods=['GET'])
def get_api_key():
    rep_key = os.getenv('REPLICATE_API_KEY', '')
    ant_key = os.getenv('ANTHROPIC_API_KEY', '')
    
    rep_masked = rep_key[:8] + '...' + rep_key[-4:] if len(rep_key) > 12 and not rep_key.startswith('votre_') else ''
    ant_masked = ant_key[:8] + '...' + ant_key[-4:] if len(ant_key) > 12 and not ant_key.startswith('votre_') else ''
    
    return jsonify({
        'replicate': {'has_key': bool(rep_masked), 'masked': rep_masked},
        'anthropic': {'has_key': bool(ant_masked), 'masked': ant_masked}
    })

@app.route('/api-key', methods=['POST'])
def set_api_key():
    rep_key = (request.form.get('replicate_key') or '').strip()
    ant_key = (request.form.get('anthropic_key') or '').strip()
    
    env_path = os.path.join(app.root_path, '.env')
    
    if rep_key:
        set_key(env_path, 'REPLICATE_API_KEY', rep_key)
        os.environ['REPLICATE_API_KEY'] = rep_key
        
    if ant_key:
        set_key(env_path, 'ANTHROPIC_API_KEY', ant_key)
        os.environ['ANTHROPIC_API_KEY'] = ant_key
    
    return jsonify({'success': True}), 200

@app.route('/api/printer/ports', methods=['GET'])
def get_printer_ports():
    ports = [port.device for port in list_comports()]
    current_port = os.getenv('NIIMBOT_COM_PORT', '')
    return jsonify({'ports': ports, 'current_port': current_port})

@app.route('/api/printer/test', methods=['POST'])
def test_printer_port():
    data = request.json
    port = data.get('port')
    if not port:
        return jsonify({'error': 'Aucun port specifie'}), 400
        
    try:
        transport = SerialTransport(port)
        client = PrinterClient(transport)
        battery_bars = client.get_info(InfoEnum.BATTERY)
        battery_percentage = int(battery_bars) * 25 if battery_bars else "Inconnu"
        
        # TOUJOURS FERMER LE PORT APRES UTILISATION
        if hasattr(transport, '_serial'):
            transport._serial.close()
        
        env_path = os.path.join(app.root_path, '.env')
        set_key(env_path, 'NIIMBOT_COM_PORT', port)
        os.environ['NIIMBOT_COM_PORT'] = port
        
        return jsonify({'success': True, 'battery': battery_percentage})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/active_voice', methods=['GET', 'POST'])
def active_voice():
    global atom_voice_id
    if request.method == 'POST':
        data = request.json
        if data and 'voice_id' in data:
            atom_voice_id = data['voice_id']
            env_path = os.path.join(app.root_path, '.env')
            set_key(env_path, 'ACTIVE_VOICE_ID', atom_voice_id)
            os.environ['ACTIVE_VOICE_ID'] = atom_voice_id
            # On ne fait plus de pre-generation individuelle ici car precache_all_greetings a deja ete appele au boot ou a la creation.
            return jsonify({'success': True, 'voice_id': atom_voice_id})
        return jsonify({'error': 'voice_id manquant'}), 400
    return jsonify({'active_voice': atom_voice_id})

@app.route('/print-ready')
def get_print_ready():
    filepath = os.path.join(app.root_path, "print_ready.png")
    if os.path.exists(filepath):
        return send_file(filepath)
    return jsonify({'error': 'Image non trouvee.'}), 404

@app.route('/api/greeting', methods=['GET'])
def greeting():
    # Appele par l'ATOM Echo au boot
    text = manager.power_up()
    # On renvoie le message "Bonjour. Je suis connecté..." mais on garde le message initial de l'état
    try:
        items = load_voice_library()
        global atom_voice_id
        item = next((i for i in items if i['id'] == atom_voice_id), items[0] if items else None)
        
        if not item:
            return jsonify({'error': 'Voix introuvable.'}), 404
            
        ref_audio_path = os.path.join(VOICE_LIBRARY_DIR, item['filename'])
        ref_text = item.get('transcript', '')
        custom_style = item.get('style', "Voix d'un homme adulte, ton naturel.")
        safe_name = secure_filename(item['name']) or 'voice'
        cache_filename = f"greeting_{safe_name}.wav"
        
        # Generer l'audio
        tts_filepath = printbot_engine.clone_voice(text, ref_audio_path, ref_text, custom_style, cache_filename=cache_filename)
        
        if isinstance(tts_filepath, str) and tts_filepath.startswith("http"):
            return redirect(tts_filepath)
            
        return send_file(tts_filepath, mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tts-cache/<filename>')
def serve_tts(filename):
    cache_dir = os.path.join(app.root_path, "_tts_cache")
    return send_file(os.path.join(cache_dir, filename))

# --- Integration ATOM Echo (UDP / HTTP Hybride) ---
ATOM_UDP_PORT = 5005
ATOM_SAMPLE_RATE = 16000
# L'ESP32 envoie toujours l'I2S PDM en stereo (32 bits par sample).
# Si on lit en mono (1), le son est 2x plus lent et grave (pitch-down).
ATOM_CHANNELS = 2 
ATOM_SAMPWIDTH = 2
atom_audio_buffer = bytearray()
atom_sync_event = threading.Event()
atom_sync_result = {}
atom_voice_id = os.getenv('ACTIVE_VOICE_ID')

def udp_server_thread():
    global atom_audio_buffer, atom_sync_result
    
    # CRITIQUE : L'échauffement du modèle IA doit obligatoirement se faire DANS le thread 
    # qui va exécuter les transcriptions (CTranslate2 Thread-Local Storage bug).
    printbot_engine.warmup_engine()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', ATOM_UDP_PORT))
    sock.settimeout(1.0)
    print(f"[UDP] Serveur ATOM Echo en ecoute sur le port {ATOM_UDP_PORT}...")
    
    receiving = False
    
    while True:
        try:
            data, addr = sock.recvfrom(2048)
            if data == b"END":
                print("[UDP] Fin de transmission recue de l'ATOM Echo.")
                receiving = False
                
                if len(atom_audio_buffer) > 0:
                    wav_path = os.path.join(app.root_path, "atom_capture.wav")
                    
                    try:
                        from pydub import AudioSegment
                        from pydub.effects import normalize as pydub_normalize
                        
                        print("[UDP] Nettoyage et normalisation du volume de la capture vocale...")
                        # Charger les donnees PCM brutes (stereo hardware)
                        audio_seg = AudioSegment(
                            data=bytes(atom_audio_buffer),
                            sample_width=ATOM_SAMPWIDTH,
                            frame_rate=ATOM_SAMPLE_RATE,
                            channels=ATOM_CHANNELS
                        )
                        # Downmix immediat en Mono pour retablir la vitesse et la hauteur exactes !
                        audio_seg = audio_seg.set_channels(1)
                        # Le micro PDM génère un énorme souffle (hautes fréquences) et un bourdonnement (basses fréquences).
                        # On isole la fréquence de la voix humaine (300Hz - 3000Hz)
                        audio_seg = audio_seg.high_pass_filter(300)
                        audio_seg = audio_seg.low_pass_filter(3000)
                        
                        # Normaliser le volume au max (maintenant que le bruit est supprimé, seule la voix sera boostée !)
                        audio_seg = pydub_normalize(audio_seg)
                        
                        # Sauvegarder en WAV
                        audio_seg.export(wav_path, format="wav")
                    except Exception as e:
                        print(f"[UDP] Erreur de normalisation ({e}), sauvegarde classique...")
                        with wave.open(wav_path, 'wb') as wf:
                            wf.setnchannels(ATOM_CHANNELS)
                            wf.setsampwidth(ATOM_SAMPWIDTH)
                            wf.setframerate(ATOM_SAMPLE_RATE)
                            wf.writeframes(atom_audio_buffer)
                            
                    print("[UDP] Fichier WAV sauvegarde, traitement en cours...")
                    
                    try:
                        transcript = printbot_engine.transcribe_audio(wav_path)
                        items = load_voice_library()
                        response_text, action = manager.process_text(transcript, available_voices=items)
                        
                        image_url = None
                        if action == "CHANGE_VOICE":
                            global atom_voice_id
                            atom_voice_id = response_text
                            env_path = os.path.join(app.root_path, '.env')
                            set_key(env_path, 'ACTIVE_VOICE_ID', atom_voice_id)
                            os.environ['ACTIVE_VOICE_ID'] = atom_voice_id
                            response_text = "Changement de voix confirme."
                            
                        elif action == "PRINT":
                             prompt_text = response_text
                             img_url_or_path = printbot_engine.generate_image(prompt_text)
                             final_image = os.path.join(app.root_path, "print_ready.png")
                             image_formatter.format_for_thermal_printer(img_url_or_path, final_image)
                             
                             # --- Impression physique Niimbot (en arriere-plan) ---
                             port = os.getenv('NIIMBOT_COM_PORT')
                             if port:
                                 def print_task():
                                     try:
                                         from niimprint import PrinterClient, SerialTransport
                                         from PIL import Image
                                         print(f"[{datetime.now().strftime('%H:%M:%S')}] Envoi de l'image a la Niimbot sur {port}...")
                                         transport = SerialTransport(port)
                                         client = PrinterClient(transport)
                                         client.print_image(Image.open(final_image), density=3)
                                         if hasattr(transport, '_serial'):
                                             transport._serial.close()  # TOUJOURS FERMER LE PORT !
                                         print(f"[{datetime.now().strftime('%H:%M:%S')}] Impression Niimbot terminee.")
                                     except Exception as e:
                                         print(f"[{datetime.now().strftime('%H:%M:%S')}] Erreur d'impression Niimbot : {e}")
                                 threading.Thread(target=print_task).start()
                             else:
                                 print(f"[{datetime.now().strftime('%H:%M:%S')}] AVERTISSEMENT : Aucun port COM Niimbot configure dans .env.")
                             
                             image_url = f'/print-ready?t={os.path.getmtime(final_image)}'
                             
                             ludique_responses = [
                                 "C'est un super choix ! Je sors mes crayons magiques et je te l'imprime tout de suite.",
                                 "Oh wow, j'adore l'idée ! La machine est en marche, ton dessin sort dans un instant.",
                                 "Excellente idée ! Laisse-moi deux petites secondes, je te dessine ça et ça s'en vient.",
                                 "Génial ! Garde l'œil sur l'imprimante, ton chef-d'œuvre arrive d'une seconde à l'autre.",
                                 "Parfait ! La magie opère... ton dessin s'en vient !",
                                 "C'est brillant ! Je mets mes circuits en marche et je dessine ça.",
                                 "Ouh, j'aime ça ! Regarde bien l'imprimante, ça va apparaître.",
                                 "Très cool comme idée. Laisse-moi une seconde pour te préparer ça.",
                                 "Parfait, chef ! J'allume mon imagination et l'impression commence.",
                                 "Ça, c'est une idée de génie. L'imprimante se met au travail.",
                                 "Fantastique ! Je sors ma feuille de papier et je te l'envoie.",
                                 "Wow, quelle belle suggestion ! Ton dessin est presque prêt.",
                                 "C'est noté ! Reste là, la machine va faire sortir ton image.",
                                 "Super idée ! Je m'en occupe tout de suite, compte sur moi.",
                                 "Excellent ! J'envoie ça directement à mon imprimante magique.",
                                 "Oh, ça va être beau ! L'impression démarre dans un instant.",
                                 "D'accord, c'est parti mon kiki ! Ton image s'en vient.",
                                 "Très bon choix. J'imprime ça plus vite que l'éclair.",
                                 "Formidable ! Attends un peu, l'imprimante va te sortir un beau dessin.",
                                 "Quelle imagination ! Je te trace ça sur-le-champ.",
                                 "J'adore ton idée. Je fais chauffer l'imprimante pour toi.",
                                 "Super chouette ! Garde les yeux sur la petite imprimante.",
                                 "C'est parti ! Mes petits robots intérieurs dessinent ça à toute vitesse.",
                                 "C'est entendu ! Je te sors un dessin qui va te faire sourire.",
                                 "Wow, je n'y aurais jamais pensé. L'impression commence maintenant.",
                                 "Merveilleux ! Mon moteur créatif est lancé, regarde bien.",
                                 "Ça marche ! Je prépare le papier magique pour toi.",
                                 "Très original ! Je suis sûr que tu vas adorer le résultat.",
                                 "C'est un grand oui ! Ton idée s'en vient sur papier.",
                                 "Absolument ! Mon cerveau électronique travaille fort pour te l'imprimer.",
                                 "Super ! Laisse-moi juste le temps de dessiner, et hop, ça sort.",
                                 "Magnifique idée. Je t'imprime ça en un clin d'œil.",
                                 "C'est dans la poche ! Regarde l'imprimante s'activer.",
                                 "Je suis prêt ! Ton chef-d'œuvre arrive dans quelques secondes.",
                                 "Très inspirant ! Je lance l'impression, tu vas voir.",
                                 "Oh, j'ai hâte de voir ça sur papier. C'est parti !",
                                 "Belle trouvaille ! Je mets la machine en branle tout de suite.",
                                 "C'est compris ! Je t'envoie ton dessin magique.",
                                 "Quel talent ! Je vais essayer de dessiner ça du mieux que je peux.",
                                 "Formidable idée, Octave approuve ! L'imprimante est en route.",
                                 "Génialissime ! L'encre chauffe et ton dessin s'en vient.",
                                 "Parfaitement parfait ! Attends-toi à une belle surprise sur le papier.",
                                 "C'est un plan ! Je m'applique et je te l'imprime.",
                                 "Super suggestion ! La magie de l'impression commence.",
                                 "Oh la la, ça va être amusant. Ton dessin sort bientôt.",
                                 "C'est d'accord ! Mes pinceaux virtuels sont à l'œuvre.",
                                 "J'aime beaucoup ton idée. Regarde la petite machine imprimer ça.",
                                 "Wow, tu débordes d'imagination ! Je lance l'impression.",
                                 "Excellent choix mon ami. La feuille magique arrive.",
                                 "C'est tout bon ! Mon imprimante s'occupe du reste."
                             ]
                             response_text = random.choice(ludique_responses)
                        
                        items = load_voice_library()
                        # Par defaut la premiere voix si voice_id n'est pas passe ou invalide
                        item = next((i for i in items if i['id'] == atom_voice_id), items[0] if items else None)
                        if item:
                            if action == "CHANGE_VOICE":
                                safe_name = secure_filename(item['name']) or 'voice'
                                cache_filename = f"greeting_{safe_name}.wav"
                                tts_filepath = os.path.join(app.root_path, "_tts_cache", cache_filename)
                                audio_url = f"/tts-cache/{os.path.basename(tts_filepath)}"
                            elif action == "PLAY_SONG":
                                audio_url = random.choice(["/tts-cache/chanson.wav", "/tts-cache/chanson2.wav", "/tts-cache/chanson3.wav", "/tts-cache/chanson4.wav", "/tts-cache/chanson5.wav"])
                            else:
                                ref_audio_path = os.path.join(VOICE_LIBRARY_DIR, item['filename'])
                                ref_text = item.get('transcript', '')
                                custom_style = item.get('style', "Voix d'un homme adulte, ton naturel.")
                                tts_filepath = printbot_engine.clone_voice(response_text, ref_audio_path, ref_text, custom_style)
                                
                                audio_url = tts_filepath if (isinstance(tts_filepath, str) and tts_filepath.startswith("http")) else f"/tts-cache/{os.path.basename(tts_filepath)}"
                        else:
                            audio_url = ""
                            
                        atom_sync_result = {
                            'transcript': transcript,
                            'response_text': response_text,
                            'audio_url': audio_url,
                            'action': action,
                            'image_url': image_url,
                            'state': manager.state
                        }
                        print(f"[UDP] Traitement termine avec succes. Reponse prete pour l'ATOM.")
                    except Exception as e:
                        print(f"[UDP] Erreur de traitement: {e}")
                        atom_sync_result = {'error': str(e)}
                        
                    atom_sync_event.set() # Revoquer le bloquage HTTP
                atom_audio_buffer = bytearray()
                
            else:
                if not receiving:
                    print(f"[UDP] Debut de reception de {addr}...")
                    receiving = True
                    atom_sync_event.clear()
                    atom_sync_result = {}
                atom_audio_buffer.extend(data)
                
        except socket.timeout:
            pass

@app.route('/api/device/sync', methods=['GET'])
def device_sync():
    # La voix est desormais geree globalement par la Web UI via /api/active_voice
    print("[HTTP] L'ATOM Echo attend sa reponse...")
    
    # On attend maximum 60 secondes que le thread UDP finisse son travail (IA + generation)
    if atom_sync_event.wait(timeout=60.0):
        atom_sync_event.clear()
        print("[HTTP] Reponse envoyee a l'ATOM Echo !")
        return jsonify(atom_sync_result)
    
    print("[HTTP] Timeout, l'ATOM n'a pas recu de reponse a temps.")
    return jsonify({'error': 'Timeout attente audio UDP'}), 408

if __name__ == '__main__':
    ensure_voice_library()
    # Lancement du serveur UDP (protege contre le double-lancement du reloader Flask)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or os.getenv('FLASK_DEBUG', '1') != '1':
        threading.Thread(target=udp_server_thread, daemon=True).start()
        
        # Lancer le pre-cache au demarrage pour toutes les voix
        threading.Thread(target=precache_all_greetings, daemon=True).start()
        
    app.run(host=os.getenv('SERVER_HOST', '0.0.0.0'), port=5666, debug=(os.getenv('FLASK_DEBUG', '1') == '1'))
