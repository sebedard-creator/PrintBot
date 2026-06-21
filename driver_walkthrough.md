# Guide de Connexion Windows : Niimbot B1 via Port Série Virtuel (SPP)

Ce guide explique comment connecter de manière stable une imprimante thermique Niimbot B1 à Windows sans avoir besoin de librairies Bluetooth complexes ou instables en Python (comme `bleak` ou les sockets Windows bruts). 

L'astuce consiste à forcer Windows à créer un **Port Série Virtuel (COM Port)** basé sur le profil Bluetooth SPP (Serial Port Profile). De cette façon, Python peut communiquer avec l'imprimante comme s'il s'agissait d'un simple câble USB.

---

## Étape 1 : Jumelage Bluetooth standard
1. Allumez votre imprimante Niimbot B1.
2. Ouvrez les **Paramètres Windows** > **Bluetooth et appareils**.
3. Assurez-vous que le Bluetooth est activé, puis cliquez sur **Ajouter un appareil**.
4. Sélectionnez **Bluetooth**.
5. Cliquez sur votre imprimante (généralement nommée `B1-XXXX` ou similaire).
6. Si un code PIN est demandé, essayez `0000` ou `1234`. (Habituellement, aucun code n'est requis).
7. L'appareil apparaîtra comme "Connecté", mais à ce stade, il n'est pas encore utilisable par notre script Python.

---

## Étape 2 : Création du Port COM Virtuel (L'astuce magique)
Pour que Python puisse parler à l'imprimante via `pyserial`, nous devons router le signal Bluetooth vers un port COM.

1. Allez au bas de la page des paramètres **Bluetooth et appareils** et cliquez sur **Paramètres des appareils supplémentaires** (ou "Afficher plus d'appareils" -> **Plus de paramètres Bluetooth** selon la version de Windows 11/10).
2. Une ancienne fenêtre Windows intitulée "Paramètres Bluetooth" va s'ouvrir.
3. Allez dans l'onglet **Ports COM**.
4. Cliquez sur le bouton **Ajouter...**.
5. Dans la fenêtre qui s'ouvre, cochez la case **Sortant (l'ordinateur lance la connexion)**.
6. Cliquez sur la liste déroulante *Périphérique :* et sélectionnez votre imprimante `B1-XXXX`.
7. Cliquez sur **OK**.
8. Windows va réfléchir quelques secondes et vous ramener à l'onglet "Ports COM". Vous devriez maintenant voir une nouvelle ligne, par exemple :
   > **Port : COM8 | Direction : Sortant | Nom : B1-XXXX 'Port série'**
9. **Notez précieusement ce numéro de port (ex: `COM8`)**, c'est celui que vous devrez entrer dans l'interface Web de PrintBot !

---

## Étape 3 : Vérification dans le Gestionnaire de Périphériques
Pour s'assurer que le driver s'est bien installé :
1. Faites un clic droit sur le bouton Démarrer de Windows et choisissez **Gestionnaire de périphériques**.
2. Déroulez la section **Ports (COM et LPT)**.
3. Vous devriez y voir **Lien série sur Bluetooth standard (COM8)** (le numéro correspondra à celui noté à l'étape précédente).
4. S'il n'y a pas de triangle jaune, tout est parfait !

---

## Étape 4 : Configuration dans PrintBot
Maintenant que le port matériel est créé, PrintBot peut s'y connecter instantanément.

1. Ouvrez l'interface Web de PrintBot.
2. Allez dans le panneau de contrôle de l'imprimante.
3. Le port `COM8` (ou votre numéro) devrait apparaître dans la liste déroulante.
4. Sélectionnez-le et cliquez sur "Tester la connexion". Le serveur Python utilisera `pyserial` pour ouvrir le port et demandera le statut de la batterie à l'imprimante.
5. Si tout fonctionne, le port sera sauvegardé automatiquement dans le fichier `.env` (`NIIMBOT_COM_PORT=COM8`).

> **Note de stabilité :** 
> En utilisant cette méthode (SPP via Port COM), la connexion Bluetooth est gérée au niveau matériel par le système d'exploitation Windows. Cela empêche les déconnexions aléatoires de sockets et permet à l'imprimante de traiter le flux binaire de manière beaucoup plus résiliente !
