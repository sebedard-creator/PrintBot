# Changelog

Toutes les modifications importantes de ce projet (Vibe-Print Bot) seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/), et ce projet adhère au [Versionnement Sémantique](https://semver.org/).

## [0.7.0] - 2026-06-18
### Ajouté
- **Intégration Niimbot B1 (Port Série Virtuel) :** Le script interagit désormais avec l'imprimante thermique Niimbot B1 via une connexion Série (COM Port virtuel Windows) plutôt que des sockets RFCOMM bruts, améliorant drastiquement la stabilité.
- **Scanner de Ports UI :** L'interface web intègre un panneau dynamique pour scanner les ports COM locaux, tester la communication avec l'imprimante (demande de batterie), et sauvegarder le port fonctionnel directement dans `.env`.
- **Statut de Batterie Logique :** Le niveau de batterie de l'imprimante est converti de son format natif "barres (1-4)" en pourcentage "25-100%" pour plus de clarté dans l'UI.
- **Sécurisation GitHub :** Création d'un fichier `.gitignore` exhaustif et d'un `.env.example` pour permettre la mise en open source du projet sans fuite de clés API ou de gros modèles/clones locaux.
- **Script de Test d'Impression :** Ajout de `test_impression.py` qui génère un dessin bitmap local (carré avec un X) et l'envoie à l'imprimante pour valider le pipeline matériel même sans papier (erreur 219 interceptée).

## [0.6.3] - 2026-06-13
### Ajouté
- **Changement de voix vocal par numéro :** L'utilisateur peut dire "Change de voix" ou "Changer de voix" à tout moment à l'ATOM Echo. Le robot listera les voix disponibles en banque avec des numéros (ex: "1... Sébastien", "2... Mylène").
- **Tolérance aux erreurs de transcription (Homophones) :** Ajout d'un dictionnaire phonétique qui convertit les mots erronés générés par Whisper (comme "Dirt", "The", "Sank") en chiffres pour assurer une sélection fiable de la voix, même avec un modèle anglais transcrivant du français.
- **Confirmation de changement vocal :** Une fois la voix modifiée par commande vocale, le robot joue automatiquement le message de *Greeting* pré-caché de cette nouvelle voix pour confirmer le changement, sans générer d'attente TTS supplémentaire.

## [0.6.2] - 2026-06-12
### Ajouté
- **Réponses Ludiques Aléatoires :** Le robot ne dit plus toujours la même phrase ("C'est parti...") lors de l'impression. Il pioche maintenant aléatoirement parmi 50 réponses beaucoup plus amusantes et thématiques ("Je sors mes crayons magiques...", "Garde l'œil sur l'imprimante...", etc.) pour rendre l'expérience plus vivante.
- **Optimisation du Prompt Engineering (Claude) :** Le prompt système pour la génération d'images a été restructuré pour obliger Claude à préserver *tous* les détails de la demande de l'utilisateur (aussi complexe soit-elle) et à les placer au tout début du prompt final, évitant ainsi que les instructions de "style" ne prennent le dessus sur le sujet principal.
- **Pré-génération globale des Greetings :** Au démarrage du serveur (ou lors de l'ajout/modification d'une voix), la fonction `precache_all_greetings()` génère en arrière-plan les messages d'accueil pour *toutes* les voix de la bibliothèque. Les fichiers sont nommés explicitement (`greeting_Sebastien.wav`, etc.) dans `_tts_cache`. L'ESP32 reçoit le fichier instantanément au boot sans aucune attente IA.
- **Champ Style Vocal (UI + API) :** Chaque voix dans la Banque de Voix possède désormais un champ `style` (ex: `"Voix d'un homme adulte, ton enjoué"`) modifiable directement depuis l'interface Web. Ce style est passé à Qwen3-TTS comme `Direction de jeu` combinée avec l'instruction de base québécoise.
- **`normalize_tts_text()` :** Normalisation des espaces dans le texte de référence avant envoi à Replicate (copie exacte de `quebec-audio-gen`).
- **Paramètre `cache_filename` dans `clone_voice` :** Permet de forcer un nom de fichier précis pour le cache (utilisé par les greetings nommés).

### Corrigé
- **`fix_mojibake` corrigée :** La condition de garde était incorrecte (cherchait des chaînes qui ne pouvaient jamais matcher). Corrigée pour être identique à `quebec-audio-gen` : détection via les marqueurs `('Ã', 'Â', 'Å')`.
- **`style_instruction` Qwen3-TTS :** Le prompt envoyé à Replicate aligne désormais exactement `quebec-audio-gen` : base québécoise fixe + `Direction de jeu: [style]`, empêchant Qwen de tomber sur une voix française par défaut.
- **Pré-cache individuel retiré :** La génération d'un greeting unique au changement de voix active a été remplacée par `precache_all_greetings()` (couverture universelle).

## [0.6.1] - 2026-06-12
### Ajouté
- **Filtre Anti-Mojibake (UTF-8) :** Intégration initiale de `fix_mojibake` dans `printbot_engine.py` (version corrigée en 0.6.2).

### Corrigé
- **Hallucinations de Genre Qwen3-TTS :** Premier alignement du prompt avec `quebec-audio-gen` (complété et stabilisé en 0.6.2).

## [0.6.0] - 2026-06-12
### Modifié
- **Refonte Web UI :** Suppression des composants de virtualisation (Simulateur Web et Machine à États jouet). La page web (port 5666) devient exclusivement un gestionnaire de configuration : insertion des clés API et de la Banque de Voix. L'utilisateur peut y télécharger ses fichiers vocaux et sélectionner d'un simple clic la "Voix Active" qui sera envoyée instantanément au robot physique, remplaçant la gestion obsolète via l'ESP32.
- **Purge TTS :** Le cache audio a été entièrement purgé pour forcer la regénération des phrases clés ("Bonjour", "As-tu bien dit...") avec le nouveau moteur de Normalisation Maximale.
- **Sauvegarde de la Voix Active :** Le serveur persiste désormais la voix sélectionnée dans le fichier `.env` pour la conserver même après un redémarrage de l'ordinateur.
- **Logique de Confirmation :** La phrase "D'accord. Que veux-tu imprimer alors ?" a été remplacée par "Pas de problème. Dis-moi ce que tu veux imprimer." pour aider l'IA de clonage à mieux garder l'accent québécois. Le bot considère désormais automatiquement que TOUT ce qui n'est pas un "Oui" clair (silence, bruit, "Mouh", "Non") est un refus.
- **Optimisation du Prompt d'Image (V3) :** Le style "Minimalist Vector Logo" générait de trop gros aplats noirs et abstraisait trop l'anatomie (transformant le capybara en rongeur à queue). Remplacement par le style "Clean contour line drawing, unshaded, pure outlines only". L'IA dessine désormais uniquement des contours uniformes sur fond blanc, parfait pour économiser le papier thermique Niimbot et garantir un rendu clair. (La contrainte stricte d'anatomie a été relâchée pour plus de créativité).
- **Message d'Introduction :** Restauration du message d'introduction ludique ("Salut Octave ! Dis-moi, qu'est-ce que tu aimerais qu'on crée ensemble aujourd'hui ?") avec prise en charge complète des accents UTF-8 et liaison dynamique pour qu'il soit toujours lu avec la Voix Active sélectionnée.
- **Console Serveur en Temps Réel :** Ajout d'une console (Live Logs) directement dans l'interface Web affichant les 500 dernières lignes d'activité du serveur. Idéal pour monitorer le programme lorsqu'il tourne en arrière-plan via un script VBS.
- **Refonte UI Mineure :** Simplification du nom de l'application en "PrintBot" et suppression des emojis superflus dans l'en-tête de l'interface d'administration.

### Corrigé
- **Bug Majeur de Pitch-Down (Voix au ralenti) :** L'ESP32 envoyait le flux I2S du microphone PDM en stéréo entrelacé (32 bits par cycle). Python le lisait comme du mono, divisant ainsi la vitesse de lecture par deux et rendant la voix grave et méconnaissable. Le serveur télécharge désormais le buffer à la bonne vitesse, et effectue un downmix en Mono pour restaurer la voix à la perfection !
- **Rognage de l'Image (Correction de Cadrage) :** Le script de traitement d'image `image_formatter.py` utilisait une logique de "Cover" (remplissage) au lieu de "Contain" (ajustement), ce qui coupait le haut et le bas des images générées. Le ratio est désormais calculé correctement pour que le dessin entier tienne dans la zone imprimable avec des marges blanches.
- **Auto-Trim des Images (Maximisation de l'Espace) :** L'IA a tendance à générer un dessin minuscule au milieu d'un énorme canevas blanc (1024x1024). Un algorithme de détection de pixels (`getbbox()`) a été ajouté dans le script de formatage pour découper chirurgicalement tout le vide blanc atour du dessin *avant* de le redimensionner. L'image finale prend désormais 100% de la largeur ou de la hauteur de l'étiquette disponible !
- **Correction du Timeout ESP32 (Pre-caching) :** Au premier démarrage, l'ESP32 demandait le message vocal d'introduction au serveur et attendait la réponse. La génération IA prenant environ 10 secondes, l'ESP32 faisait un "Timeout" (connexion coupée) et plantait. Le serveur Python lance désormais une pré-génération en arrière-plan (Background Thread) du message d'accueil dès son démarrage ou dès qu'on change la voix active. L'ESP32 reçoit donc le fichier instantanément sans jamais crasher !

## [0.5.1] - 2026-06-12
### Ajouté
- **Nettoyage Studio de l'Audio PDM :** La normalisation de l'entrée a été remise en place, MAIS cette fois elle est précédée d'un nettoyage d'égalisation algorithmique. L'audio brut passe par un filtre passe-haut (300Hz) pour retirer le bourdonnement électrique, et un filtre passe-bas (3000Hz) pour écraser le souffle statique insupportable du microphone. La normalisation s'applique ensuite uniquement sur la voix propre !
- **Amorce Anti-Phonétique :** Ajout d'une amorce forcée pour Whisper listant les mots exacts des animaux (crocodile, alligator, etc.) afin d'empêcher l'IA de faire de l'écriture phonétique québécoise ("krakradil").

## [0.5.0] - 2026-06-12
### Modifié
- **Mise à niveau du Modèle d'IA :** Le moteur de transcription Whisper passe de `base` (74 Mo) à `small` (244 Mo). Le microphone du robot (PDM) capture énormément d'électricité statique (souffle), et lorsqu'il est amplifié (Normalisation Input), le petit modèle `base` hallucine et invente des mots. Le modèle `small` est beaucoup plus intelligent, résistant au bruit, et est capable de déchiffrer la voix humaine même dans une tempête de souffle statique ! Le "prompt contextuel" (qui causait aussi des hallucinations) a été retiré.

## [0.4.2] - 2026-06-12
### Corrigé
- **Transcription Whisper Erronée :** La normalisation audio du microphone (Input) amplifiait massivement le bruit de fond matériel de l'ESP32, ce qui détruisait la compréhension de l'IA. La normalisation Input a été retirée.
- **Filtre VAD & Amorce Contextuelle :** L'activation du filtre de détection de voix (`vad_filter=True`) et l'ajout d'une phrase d'amorce contextuelle ("Dessine un chat...") forcent Whisper à ignorer le bruit ambiant et à privilégier le vocabulaire lié au dessin pour ses prédictions.

## [0.4.1] - 2026-06-12
### Ajouté
- **Normalisation Audio Intégrale :** Le volume de la voix capturée par le robot est désormais boosté automatiquement au niveau maximum avant d'être analysé par Whisper (Input). De même, toutes les voix synthétisées (TTS Replicate/Kokoro) sont traitées via `pydub` pour exploiter 100% de la puissance du haut-parleur sans saturation (Output).

## [0.4.0] - 2026-06-12
### Corrigé
- **Perte totale du premier enregistrement (Silence/Micro) :** Le module WiFi de l'ESP32 passait secrètement en mode "sommeil profond" (Modem Sleep) entre le démarrage et le premier clic. De plus, la fonction `udp.beginPacket()` effectuait une requête DNS silencieuse à chaque fois pour résoudre la chaîne de caractères "10.0.0.30". Ces deux phénomènes engorgeaient le réseau pendant la première seconde, ce qui faisait "sauter" tous les premiers paquets UDP contenant la voix. La mise en veille a été désactivée (`WiFi.setSleep(false)`), la résolution DNS est mise en cache au démarrage (`IPAddress`), et les délais de matériel I2S ont été doublés. Le son est maintenant capturé instantanément.

## [0.3.3] - 2026-06-12
### Corrigé
- **Enregistrement Muet au premier clic (MaxAmp 900) :** Ajout de délais de stabilisation matériels (50ms). Lors du premier clic, le haut-parleur était désactivé asynchronement par l'ESP32. Si le microphone démarrait instantanément, il ne parvenait pas à capturer la matrice GPIO (toujours bloquée par l'extinction du haut-parleur). Les délais garantissent que le micro a l'exclusivité des broches avant de démarrer son horloge.

## [0.3.2] - 2026-06-12
### Corrigé
- **Conflit I2S (Loop "Je me suis perdu" et "register I2S object failed") :** L'approche de la version 0.3.1 (mettre tout le monde sur le port 0) posait problème car la librairie `ESP8266Audio` s'attendait à retrouver son état de manière persistante, ou laissait une trace interne même après destruction. L'architecture a été réécrite pour une approche *Double Port & Destruction Mutuelle* : le Haut-Parleur vit **strictement** sur `I2S_NUM_1` et le Micro sur `I2S_NUM_0`. Pour éviter le conflit GPIO matériel, chaque contrôleur "détruit" et désinstalle complètement l'autre port matériel avant de s'activer. L'horloge I2S n'est donc plus jamais bloquée !

## [0.3.1] - 2026-06-12
### Corrigé
- **Multiplexage I2S (Loop Silence et Crash de Lecture) :** Le "détachement" de pins (0.3.0) s'est avéré insuffisant car la librairie `ESP8266Audio` conservait un état de configuration interne fantôme. Le code a été entièrement réécrit pour forcer le Haut-Parleur et le Microphone à s'initialiser et se détruire proprement, à tour de rôle, sur le *même* port matériel de la puce (`I2S_NUM_0`), ce qui élimine définitivement les conflits de GPIO et d'horloge.

## [0.3.0] - 2026-06-12
### Corrigé
- **Conflit Matériel (Silence Audio) :** Résolution d'un conflit fatal au niveau de l'*ESP32 GPIO Matrix*. Sur le M5Stack ATOM Echo, le haut-parleur et le microphone partagent physiquement la pin `33` (LRCK / PDM_CLK). Lorsque l'un était actif, il bloquait l'accès à l'autre, privant le microphone de son signal d'horloge (ce qui causait l'enregistrement du silence pur). Le code "détache" (libère) désormais explicitement les pins I2S avant de basculer du mode haut-parleur au mode microphone.

## [0.2.9] - 2026-06-12
### Corrigé
- **Enregistrement Audio (Silence / Fallback "Perdu") :** Correction matérielle des pins du microphone PDM (SPM1423) pour le M5Stack ATOM Echo. Le code assignait par erreur les GPIO 32 et 34 (port Grove), ce qui causait l'enregistrement d'un silence pur. Le modèle de transcription traduisait ce silence par une chaîne de caractères vide, déclenchant le message d'erreur de l'IA ("Je me suis perdu"). Les pins officielles correctes (`33` pour l'horloge et `23` pour les données) sont désormais utilisées.

## [0.2.8] - 2026-06-12
### Corrigé
- **Streaming Audio UDP (Timeout 408) :** L'ouverture (`beginPacket`) et la fermeture (`endPacket`) du flux réseau ont été déplacés à l'intérieur de la boucle de capture audio. Précédemment, l'audio s'accumulait dans un seul "paquet fantôme" infini, ce qui provoquait un dépassement de tampon et la perte systématique du message "END". Le serveur Python ne détectait donc jamais la fin de l'enregistrement. Le message "END" est maintenant envoyé 3 fois pour garantir sa réception via UDP.

## [0.2.7] - 2026-06-12
### Corrigé
- **Crash Audio ATOM Echo (Kernel Panic) :** Remplacement du mode `INTERNAL_DAC` (qui forçait matériellement l'usage du port 0) par `EXTERNAL_I2S` (0) pour l'initialisation du haut-parleur. Cela corrige le crash fatal `I2S built-in ADC/DAC only support on I2S0` qui survenait au moment de lire l'audio.

## [0.2.6] - 2026-06-12
### Modifié
- **Décodeur Audio ATOM Echo :** Remplacement du décodeur `AudioGeneratorMP3` par `AudioGeneratorWAV` sur l'ESP32. Qwen3-TTS génère nativement des fichiers WAV (non compressés) et le décodeur MP3 plantait silencieusement en essayant de les lire.

## [0.2.5] - 2026-06-12
### Corrigé
- **Crash Enregistrement Micro (MCLK) :** L'assignation de la pin `mck_io_num` a été explicitement réglée à `I2S_PIN_NO_CHANGE` pour corriger une erreur d'initialisation aléatoire (`error GPIO number: 1061164136`) lors de la création de la structure I2S en C++.
### Ajouté
- **Message d'accueil automatique :** L'ATOM Echo joue désormais automatiquement le message vocal d'accueil (`/api/greeting`) au démarrage, juste après sa connexion au Wi-Fi.

## [0.2.4] - 2026-06-12
### Corrigé
- **Crash de l'ATOM Echo (Bootloop) :** Correction d'un conflit fatal ("CONFLICT! legacy i2s driver") entre le microphone (PDM) et le haut-parleur. L'ESP32 requiert l'usage exclusif du port `I2S_NUM_0` pour le PDM. Le port du haut-parleur a été déplacé sur `I2S_NUM_1`.

## [0.2.3] - 2026-06-12
### Corrigé
- **Formatage d'Image pour Impression (Pointillés) :** Remplacement de l'algorithme de tramage (Dithering Floyd-Steinberg) par un binarisation stricte (Threshold 200). Cela corrige l'effet de "points dispersés" sur les tracés fins et garantit des lignes noires épaisses et continues pour le style "Line Art".

## [0.2.2] - 2026-06-12
### Corrigé
- **Crash Serveur UDP (WinError 10048) :** Empêchement du double démarrage du thread UDP lié au reloader natif de Flask en environnement de développement (`WERKZEUG_RUN_MAIN`).
- **Anomalie de Clonage Vocal (TTS) :** Retrait de la ponctuation agressive (`!` et `?`) dans les phrases pré-générées pour éviter la déformation de l'intonation par le modèle Qwen3. Purge complète de l'ancien dossier `_tts_cache`.
- **Modèle Anthropic 404 :** Mise à jour du nom de code du modèle Claude vers la version économique la plus récente et disponible (`claude-3-5-haiku-20241022`).
- **Dépendances Manquantes :** Ajout d'`anthropic`, `faster-whisper`, et `deep-translator` dans le fichier `requirements.txt`.

## [0.2.1] - 2026-06-12
### Ajouté
- **Interface Configuration API :** Ajout d'un champ dédié dans l'interface Web (front-end) pour saisir et sauvegarder la clé `ANTHROPIC_API_KEY` séparément de la clé Replicate.
- Lien direct vers la console de facturation Anthropic ajouté dans le pied de page du portail Web.

## [0.2.0] - 2026-06-12
### Ajouté
- **Architecture Hybride (PC + ATOM Echo) :** Remplacement total de l'idée de l'application Android par le firmware C++ pour microcontrôleur M5Stack ATOM Echo.
- **Firmware ATOM Echo :** Création du code C++ complet gérant le WiFiManager (avec champ IP serveur custom), l'enregistrement I2S (SPM1423), le streaming UDP en temps réel, l'attente HTTP (polling) et la lecture audio I2S (NS4168) de la réponse.
- **Serveur UDP en arrière-plan :** Intégration du serveur de réception UDP (port 5005) directement dans un thread au sein de `app.py` pour assembler les paquets audio streamés par l'ATOM.
- **Endpoint de Synchronisation :** Création de la route `/api/device/sync` permettant à l'ESP32 de déclencher le traitement asynchrone de la conversation via `ConversationManager` et de récupérer la réponse TTS.

## [0.1.8] - 2026-06-11
### Modifié
- **Prompt Engineering avancé (Image) :** Remplacement de la simple traduction (GoogleTranslator) par une reformulation intelligente via Anthropic (Claude 3 Haiku). Claude a pour instruction stricte d'exagérer les demandes anatomiques farfelues (ex: "un chien avec EXACTEMENT CINQ (5) pattes, c'est une créature magique...") afin de contourner l'auto-correction anatomique très tenace de Flux-dev. Le style graphique enfantin est également ajouté dynamiquement par Claude à la fin de chaque requête.

## [0.1.7] - 2026-06-11
### Modifié
- **Prompt Engineering (Image) :** Modification du prompt système caché envoyé à Flux. L'esthétique a été changée pour un style "livre de coloriage pour enfants, mignon, amusant, dessin animé" avec des contours plus épais.
- **Interprétation Littérale (Image) :** Renforcement de la consigne interdisant à l'IA de corriger l'anatomie ("You MUST NOT correct anatomical 'mistakes'") pour permettre la génération de concepts absurdes demandés par les enfants (ex: chien à 5 pattes).

## [0.1.6] - 2026-06-11
### Corrigé
- **Rate Limit Replicate (Voix) :** Ajout de la boucle de réessai automatique (retry) avec pause de 10 secondes pour contourner l'erreur de Throttle (429) lors de la génération audio, fonction qui n'était présente que pour la génération d'image.

## [0.1.5] - 2026-06-11
### Modifié
- **Script d'accueil :** Modification de la phrase de salutation du robot (remplacement de "imagine" par "crée" pour plus de clarté pour l'enfant).

## [0.1.4] - 2026-06-11
### Modifié
- **Retour de l'accent québécois :** Remplacement du modèle de clonage vocal (`lucataco/xtts-v2`) par `qwen/qwen3-tts` pour forcer l'accent et la prosodie québécoise via des instructions de style spécifiques (comme dans l'ancien projet quebec-audio-gen).
### Ajouté
- **Transcription automatique des voix :** L'upload d'un fichier vocal dans l'interface déclenche maintenant automatiquement sa transcription locale (`faster-whisper`), sauvegardée en arrière-plan, car le modèle Qwen3 nécessite impérativement le texte de la référence pour un clonage de qualité.

## [0.1.3] - 2026-06-11
### Corrigé
- **Crash Silencieux du Simulateur :** Ajout de blocs `try/except` dans les routes de l'API Flask pour renvoyer des erreurs JSON propres au lieu d'une page d'erreur HTML 500, ce qui empêche le JavaScript de planter et le bouton de rester bloqué indéfiniment.
- **Erreur de Modèle TTS Replicate :** Remplacement du modèle de test invalide (`jichengdu/cosyvoice:1`) par un modèle de clonage vocal valide et fonctionnel (`lucataco/xtts-v2`) nécessitant uniquement l'audio source.

## [0.1.2] - 2026-06-11
### Corrigé
- **Rate Limit Replicate (Erreur 429) :** Ajout d'une boucle de réessai automatique avec une pause de 10 secondes pour gérer les limites de l'API lorsque le solde est faible.
- **Compréhension du Prompt Image :** Ajout de la librairie locale `deep-translator` pour traduire automatiquement la transcription française en anglais avant l'envoi à `flux-schnell`.
- **Prompt Engineering :** Réorganisation de la requête pour placer le sujet au tout début de la phrase avant les instructions de style, réglant ainsi le problème où l'IA ignorait le sujet principal.
- **Autorisation Replicate (Erreur 401) :** Instanciation explicite du `replicate.Client` avec la clé API pour forcer l'utilisation de `REPLICATE_API_KEY` stockée dans `.env`.

## [0.1.1] - 2026-06-11
### Modifié
- **Pivot Architectural :** Abandon de l'idée initiale (Groq/Whisper) pour s'aligner sur le code de `Y:\quebec-audio-gen`. Le STT (Reconnaissance vocale) et le TTS (Clonage vocal) utiliseront l'API Replicate.
### Ajouté
- Planification d'une interface web (Flask) pour gérer la bibliothèque de voix de clonage (upload, sauvegarde, test) copiée sur le modèle de `quebec-audio-gen`.
- Ajout d'un menu dans l'interface web pour configurer directement la clé `REPLICATE_API_KEY` (sauvegardée dans le fichier `.env`).
- Ajout d'un lien vers la facturation Replicate dans le pied de page de l'interface web.
- **Phase 5 :** Ajout de la Machine à États (Logique Conversationnelle). Le robot simule maintenant une vraie interaction : Salutation -> Écoute -> Demande de confirmation -> Impression ou Rejet.
- Mise en place d'un système de **Cache TTS** pour sauvegarder localement les réponses audio pré-générées ("Salut Octave", "Que veux-tu alors") afin d'économiser les requêtes API et d'avoir des réponses instantanées.
- Ajout d'une section "Jouet Interactif" dans l'interface web pour simuler la conversation de bout en bout avec lecture audio.
- Ajout d'un **Simulateur Web** intégré à l'interface permettant d'uploader un fichier audio et d'obtenir la transcription et l'image tramée générée directement à l'écran.
- **Phase 4 :** Migration de la reconnaissance vocale (STT) de l'API cloud Replicate vers un modèle 100% local (`faster-whisper` sur CPU). 
- Retrait des limitations de délai (sleep) liées aux limites de requêtes de l'API pour le traitement de l'audio.
- **Phase 3 :** Implémentation de la génération d'image (API Replicate) et du module de traitement d'image (Pillow) pour générer des fichiers PNG 1-bit (Dithering) adaptés à la Niimbot B1.
- Intégration du pipeline complet dans le serveur de réception UDP (Audio -> Texte -> Image -> Dithering).

## [0.1.0] - 2026-06-11
### Ajouté
- Fichier `print_bot_master_prompt.md` contenant la définition du projet (existant).
- Fichier `changelog.md` pour le suivi des versions et l'historique de développement.
- Mise en place des règles de développement : dépendances strictement locales (autosuffisance).
