import re
import unicodedata

STATE_IDLE = "IDLE"
STATE_WAITING_PROMPT = "WAITING_PROMPT"
STATE_CONFIRMING = "CONFIRMING"
STATE_CHANGING_VOICE = "CHANGING_VOICE"

class ConversationManager:
    def __init__(self):
        self.state = STATE_IDLE
        self.current_prompt = ""
        
    def power_up(self):
        self.state = STATE_WAITING_PROMPT
        self.current_prompt = ""
        return "Salut Octave. Dis-moi, qu'est-ce que tu aimerais qu'on crée ensemble aujourd'hui ?"
        
    def process_text(self, text, available_voices=None):
        """
        Gere la machine a etats.
        Retourne un tuple: (message_ou_prompt, action)
        action peut etre: 
        - "SPEAK" (Dire le message)
        - "PRINT" (Imprimer le prompt)
        - "CHANGE_VOICE" (Changer la voix avec l'ID en texte)
        """
        if available_voices is None:
            available_voices = []
            
        text_lower = text.lower()
        text_norm = ''.join(c for c in unicodedata.normalize('NFD', text_lower) if unicodedata.category(c) != 'Mn')
        
        # Easter Egg: Chanson
        if re.search(r'\b(?:chante[- ]?moi une chanson|une chanson|la chanson)\b', text_norm):
            self.state = STATE_WAITING_PROMPT
            return "", "PLAY_SONG"
        
        # Detection de la commande de changement de voix (accessible de n'importe ou sauf pendant le choix lui-meme)
        # On inclut des erreurs fréquentes de Whisper comme "Chanser de voir", "Changer de bois", ou "Changer de foi"
        if self.state != STATE_CHANGING_VOICE and re.search(r'\b(?:change|changer|chanse|chanser|changement) de (?:la )?(?:voix|voie|voir|bois|vwa|foi|fois)\b', text_norm):
            self.state = STATE_CHANGING_VOICE
            if not available_voices:
                return "Je n'ai aucune voix en banque.", "SPEAK"
                
            parts = ["Bien sur, voici les voix que j'ai en banque."]
            for i, v in enumerate(available_voices):
                parts.append(f"{i+1}... {v['name']}. ...")
            
            parts.append("Dis-moi le numero de celle que tu choisis.")
            return " ".join(parts), "SPEAK"
            
        if self.state == STATE_CHANGING_VOICE:
            # Chercher si le texte contient un numero ou une orthographe approximative (homophones Whisper)
            number_map = {
                "un": 1, "une": 1, "1": 1, "in": 1, "hun": 1, "ain": 1, "en": 1, "on": 1, "arrête": 1, "erre": 1, "art": 1, "arr...": 1,
                "deux": 2, "2": 2, "de": 2, "dirt": 2, "do": 2, "the": 2, "dough": 2, "d'eux": 2,
                "trois": 3, "3": 3, "toi": 3, "tree": 3, "twa": 3,
                "quatre": 4, "4": 4, "cat": 4, "cut": 4,
                "cinq": 5, "5": 5, "sank": 5, "sync": 5, "sink": 5, "cent": 5, "thank": 5, "you": 5, "saintes": 5, "saint": 5, "sainte": 5,
                "six": 6, "6": 6, "sis": 6, "sees": 6,
                "sept": 7, "7": 7, "set": 7, "seth": 7, "cest": 7, "sait": 7, "cet": 7, "cette": 7,
                "huit": 8, "8": 8, "wheat": 8, "wait": 8, "oui": 8,
                "neuf": 9, "9": 9, "nerf": 9, "enough": 9,
                "dix": 10, "10": 10, "dis": 10, "this": 10, "dice": 10
            }
            
            chosen_index = None
            # On retire la ponctuation (. ? !) pour eviter que "Dirt." ne matche pas "dirt"
            clean_text = re.sub(r'[^\w\s]', '', text_norm)
            for word in clean_text.split():
                if word in number_map:
                    chosen_index = number_map[word] - 1
                    break
                    
            if chosen_index is not None and 0 <= chosen_index < len(available_voices):
                self.state = STATE_WAITING_PROMPT
                return available_voices[chosen_index]['id'], "CHANGE_VOICE"
            
            # Fallback sur le nom exact au cas ou
            for v in available_voices:
                v_name_norm = ''.join(c for c in unicodedata.normalize('NFD', v['name'].lower()) if unicodedata.category(c) != 'Mn')
                if v_name_norm in text_norm:
                    self.state = STATE_WAITING_PROMPT
                    return v['id'], "CHANGE_VOICE"
            
            # Si pas trouve
            self.state = STATE_WAITING_PROMPT
            return "Je n'ai pas compris ce numero. Annulation.", "SPEAK"
        
        if self.state == STATE_WAITING_PROMPT or self.state == STATE_IDLE:
            self.current_prompt = text
            self.state = STATE_CONFIRMING
            return f"As-tu bien dit {text} ?", "SPEAK"
            
        elif self.state == STATE_CONFIRMING:
            # Heuristique : Si ce n'est pas clairement un "oui", on assume que c'est un "non".
            # Aa Acvite les boucles infinies de "Pardon je n'ai pas compris" si Whisper entend "Mouh" au lieu de "Non".
            if re.search(r'\b(oui|ouais|yes|ouep|yep|ou|ui|si)\b', text_lower):
                self.state = STATE_WAITING_PROMPT
                prompt_to_print = self.current_prompt
                self.current_prompt = ""
                return prompt_to_print, "PRINT"
                
            else:
                # Tout le reste (non, nan, mouh, silence, etc) est considAcrAc comme un refus.
                self.state = STATE_WAITING_PROMPT
                self.current_prompt = ""
                return "Pas de problème. Dis-moi ce que tu veux imprimer.", "SPEAK"
                
        else:
            self.state = STATE_WAITING_PROMPT
            return "Je me suis perdu. Recommence s'il te plait.", "SPEAK"
