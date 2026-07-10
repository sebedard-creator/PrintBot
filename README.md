# PrintBot 🤖🖨️

PrintBot est un jouet interactif et magique basé sur le concept du "Bouton Unique", conçu spécialement pour les enfants. En maintenant enfoncé le gros bouton d'un petit module Wi-Fi, l'enfant peut demander n'importe quel dessin farfelu (ex: "Dessine-moi un chat à 5 pattes qui vole dans l'espace"). Le robot lui répond alors avec une voix générée par l'IA (avec un accent local personnalisé) et imprime instantanément son dessin sous forme d'autocollant grâce à une imprimante thermique portable !

## 🌟 Fonctionnalités

- **Magie du Bouton Unique** : Construit autour du M5Stack ATOM Echo. Maintenez pour parler, relâchez pour imprimer.
- **Transcription Locale Ultra-Rapide** : Utilise `faster-whisper` en local pour une reconnaissance vocale (STT) instantanée et respectueuse de la vie privée.
- **Prompt Engineering Intelligent** : S'appuie sur Claude 3 Haiku d'Anthropic pour réécrire les requêtes des enfants en prompts vectoriels minimalistes de haute qualité, parfaits pour l'impression thermique.
- **Génération d'Images Superbes** : Utilise l'API Replicate (Flux-dev) pour générer des dessins aux contours nets et épurés.
- **Clonage Vocal et Personnages** : Utilise Qwen3-TTS via Replicate pour cloner des voix. Vous pouvez téléverser des échantillons de 5 secondes ("Papa", "Maman", "Monstre") via l'interface Web et basculer entre eux instantanément.
- **Changement de Voix Vocal** : L'enfant peut dire "Change de voix" à tout moment, et le robot listera les voix disponibles pour le laisser choisir oralement !
- **Interface Web de Configuration** : Une belle interface Web Flask locale pour gérer les clés API, téléverser des échantillons vocaux et tester la connexion à l'imprimante (Sans toucher au code !).
- **Impression Thermique Bluetooth** : Se connecte de façon transparente à une imprimante thermique Niimbot B1 via un Port Série Virtuel (COM) sous Windows grâce à la librairie `niimprint`.

## 🏗️ Architecture

1. **Matériel (Hardware)** : 
   - **M5Stack ATOM Echo** : Agit comme le microphone et le haut-parleur (streame l'audio I2S via UDP en Wi-Fi).
   - **Serveur PC (Windows)** : Fait tourner le backend Flask, le modèle local Whisper STT, et s'occupe du routage API.
   - **Niimbot B1** : Imprimante thermique Bluetooth portable.
2. **Pipeline Logiciel** :
   - `Flux UDP` -> `Pydub` (Nettoyage audio) -> `Faster-Whisper` (STT) -> `Claude 3` (Réécriture du prompt) -> `Flux-dev` (Génération d'image) -> `Qwen3-TTS` (Clonage vocal TTS) -> `Niimbot B1` (Impression).

## 🚀 Guide d'Installation

### Prérequis
- Python 3.11+
- Windows ou macOS (Le port série virtuel Bluetooth est supporté sur les deux plateformes)
- Un ATOM Echo flashé avec le firmware C++ de streaming UDP adéquat
- Une imprimante thermique Niimbot B1
- Des clés API pour **Replicate** et **Anthropic**

### Installation

1. **Cloner le projet** :
   ```bash
   git clone https://github.com/votre_nom/PrintBot.git
   cd PrintBot/server
   ```

   *Sous Windows :* Lancez `install.bat`
   *Sous Mac/Linux :* Lancez `bash install.sh`
   *(Ces scripts s'occuperont de créer l'environnement virtuel et d'installer les dépendances)*

3. **Configurer l'environnement** :
   Copiez le fichier d'exemple et ajoutez vos clés API :
   ```bash
   copy .env.example .env
   ```
   *(Alternativement, vous pouvez ignorer cette étape et configurer vos clés directement via l'interface Web au premier lancement).*

### Démarrer le Serveur

Double-cliquez sur `start.bat` (Windows) ou lancez `bash start.sh` (Mac) à la racine du projet.
Le serveur démarrera localement sur le port `5666`.

### Configuration de l'Imprimante
1. Allumez votre imprimante Niimbot B1.
2. Allez dans les paramètres Bluetooth de Windows et **Jumelez** l'imprimante (`B1-...`).
3. Ouvrez l'interface Web PrintBot (`http://localhost:5666`).
4. Dans la section **Configuration Imprimante Niimbot**, cliquez sur **Actualiser** pour lister les ports COM disponibles.
5. Sélectionnez un port et cliquez sur **Tester et Sauvegarder**. Si la connexion réussit, le système affichera le niveau de batterie de l'imprimante et sauvegardera la configuration pour l'avenir.

## 🔒 Vie Privée & Sécurité

Ce projet a été pensé pour le respect de la vie privée :
- Les enregistrements audio de l'enfant sont transcrits localement puis supprimés de la mémoire.
- Seul le texte de la requête est envoyé aux APIs externes (Claude).
- Le fichier `.gitignore` est pré-configuré pour s'assurer qu'aucun fichier `.env`, modèle d'IA local ou clone vocal privé ne soit accidentellement poussé sur un dépôt public.

## 🙏 Remerciements

- [niimprint](https://github.com/kurbatov/niimprint) pour le fantastique reverse-engineering du protocole Niimbot.
- Anthropic & Replicate pour leurs APIs ultra-rapides.
- M5Stack pour le superbe matériel ATOM Echo.

---
*Conçu par Sébastien Bédard - 2026*
