# Parking Intelligent — Réseau de Petri (Projet complet)

Application web (Python + Flask) qui modélise, simule et analyse un
**Réseau de Petri** représentant un parking intelligent, conformément au
cahier des charges `Projet_RDP_Parking_Intelligent_Complet.docx`.

Elle est **déjà fonctionnelle**. Ce README explique, dans l'ordre, tout ce
qu'il vous reste à faire jusqu'à la soutenance.

---

## 0. Comprendre où vous en êtes (pip vs "interface web")

Petite clarification importante, parce que la confusion est normale :

- **"pip"** est simplement l'outil qui installe des bibliothèques Python
  (ici, seulement `Flask`). Ce n'est pas un choix concurrent à autre chose :
  vous en avez **besoin dans tous les cas** pour installer Flask avant de
  lancer le projet.
- **"L'interface web"** dont vous parlez est probablement Claude.ai (là où
  vous me parlez). Elle n'est **pas nécessaire** pour faire tourner le
  projet : le projet est une vraie application web Flask qui tourne **sur
  votre ordinateur**, dans votre propre navigateur (Chrome/Edge), à
  l'adresse `http://127.0.0.1:5000`.

Donc concrètement : vous installez Python + pip sur votre PC (ou vous les
avez déjà), vous installez Flask avec pip, vous lancez `python app.py`,
et vous ouvrez votre navigateur. Rien d'autre.

---

## 1. Structure du projet

```
parking_rdp/
├── app.py                 # Serveur Flask : toutes les routes web + API
├── petri.py                # Moteur du Réseau de Petri (le cœur mathématique)
├── requirements.txt         # Dépendances (Flask)
├── .gitignore
├── instance/                # Base SQLite (historique) créée automatiquement
├── templates/
│   ├── base.html
│   ├── index.html            # Accueil
│   ├── model.html             # Places / Transitions / Arcs / Scénarios
│   ├── simulation.html         # Diagramme RDP + tir des transitions
│   └── analysis.html           # Matrices Pre/Post/W, conflits, propriétés
└── static/
    ├── css/style.css
    └── js/
        ├── diagram.js         # Dessin SVG du réseau
        ├── simulation.js       # Logique de la page simulation
        └── analysis.js          # Logique de la page analyse
```

Le modèle implémenté (voir `petri.py` pour tous les détails et
commentaires) :

- **Places** : P1 Véhicule en entrée, P2 Accès validé, P3 Place libre,
  P4 Véhicule garé, P5 Sortie demandée, P6 Parking plein (signal),
  P7 Paiement validé.
- **Transitions** : T1 Contrôle entrée, T2 Affecter une place / garer,
  T3 Signaler parking plein, T4 Demander sortie, T5 Valider paiement,
  T6 Libérer la place.
- **Point important à dire à l'oral** : le cahier des charges signalait
  lui-même que la séparation entre T2 et T3 devait être ajustée pendant
  l'implémentation pour éviter une double consommation de jetons. La
  solution retenue ici : T2 fusionne "affecter" et "garer" (elle a besoin
  d'un jeton dans P2 **et** dans P3 — c'est une **synchronisation**), et T3
  devient la transition qui signale "parking plein" via un **arc
  inhibiteur** (elle n'est active que si P3 = 0). Cela crée aussi un
  **conflit structurel** naturel sur P1 (P1 alimente T1 et T3), qui sert
  très bien à démontrer la notion de conflit/concurrence du cours.

---

## 2. Installation et lancement en local

Ouvrez un terminal (PowerShell sur Windows, ou Terminal sur Mac/Linux)
dans le dossier `parking_rdp`.

### Étape 1 — Vérifier Python
```bash
python --version
```
Si la commande n'existe pas, essayez `python3 --version`. Il faut Python
3.9 ou plus récent.

### Étape 2 — Créer un environnement virtuel (recommandé, pas obligatoire)
```bash
python -m venv venv
```
Puis activez-le :
- Windows : `venv\Scripts\activate`
- Mac/Linux : `source venv/bin/activate`

### Étape 3 — Installer les dépendances avec pip
```bash
pip install -r requirements.txt
```

### Étape 4 — Lancer l'application
```bash
python app.py
```
Vous devez voir dans le terminal :
```
Running on http://127.0.0.1:5000
```

### Étape 5 — Ouvrir le navigateur
Allez sur **http://127.0.0.1:5000**. Naviguez entre les pages
**Accueil / Modèle / Simulation / Analyse** avec le menu en haut.

Pour arrêter le serveur : `CTRL + C` dans le terminal.

---

## 3. Comment utiliser l'application pendant la démo

1. Page **Modèle** : montrez les places/transitions/arcs, puis choisissez
   un scénario (bouton) : `vide`, `normal`, `presque_plein`, `plein`,
   `sortie_simultanee`.
2. Page **Simulation** :
   - Le diagramme SVG affiche les jetons en direct.
   - Seules les transitions **franchissables** (en vert) sont cliquables.
   - Cliquez sur une transition pour la tirer : le marquage et
     l'historique se mettent à jour automatiquement.
   - Testez le scénario `plein` : seules T1 et T3 sont actives
     (conflit) ; si vous tirez T3, le système se bloque (bannière rouge).
   - Bouton **Réinitialiser** = retour à M0. Bouton **Exporter JSON** =
     télécharge le modèle + historique.
3. Page **Analyse** : matrices Pré, Post, W = Post − Pré, conflits
   détectés automatiquement, propriétés (activité, répétitivité,
   vivacité, concurrence), statistiques des tirs.

---

## 4. Git et GitHub — pas à pas

Si vous n'avez encore rien initialisé, suivez ces commandes **dans
l'ordre**, dans le dossier `parking_rdp` :

### 4.1 Initialiser le dépôt local
```bash
git init
git add .
git commit -m "Version initiale : moteur RDP, simulation, analyse, interface web"
```

### 4.2 Créer le dépôt sur GitHub
1. Allez sur https://github.com et connectez-vous.
2. Cliquez sur **New repository**.
3. Donnez un nom, par exemple `parking-intelligent-rdp`.
4. **Ne cochez pas** "Add a README" (vous en avez déjà un) pour éviter un
   conflit inutile.
5. Cliquez sur **Create repository**. GitHub vous donne une URL du type :
   `https://github.com/VOTRE_NOM/parking-intelligent-rdp.git`

### 4.3 Relier votre projet local à GitHub et envoyer le code
```bash
git remote add origin https://github.com/VOTRE_NOM/parking-intelligent-rdp.git
git branch -M main
git push -u origin main
```
(Si Git vous demande de vous connecter, utilisez votre compte GitHub ou un
token d'accès personnel si le mot de passe est refusé — GitHub l'explique
directement dans le message d'erreur.)

### 4.4 Pour vos prochaines modifications
Chaque fois que vous modifiez du code après aujourd'hui :
```bash
git add .
git commit -m "Description de ce que vous avez changé"
git push
```

### 4.5 Commandes utiles si besoin
```bash
git status          # voir ce qui a changé
git log --oneline   # voir l'historique des commits
git diff             # voir le détail des changements non commités
```

---

## 5. Scénario de démonstration vidéo (aligné sur le cahier des charges)

Le document prévoyait un script de 10 minutes. Voici comment le réaliser
avec cette application, étape par étape :

| Temps | Contenu | Ce que vous montrez concrètement |
|---|---|---|
| 0:00–1:00 | Introduction | Page Accueil, expliquez le problème du parking |
| 1:00–2:00 | Notions RDP | Page Modèle : places, transitions, arcs |
| 2:00–3:30 | Modèle | Toujours page Modèle : M0, tableaux P1..P7, T1..T6 |
| 3:30–5:30 | Simulation | Page Simulation, scénario "normal" : tirez T1 puis T2, montrez le jeton se déplacer |
| 5:30–6:30 | Sortie | Continuez : tirez T4, T5, T6, montrez la place libérée dans P3 |
| 6:30–7:30 | Matrices | Page Analyse : montrez Pré, Post, W |
| 7:30–9:00 | Analyse | Chargez le scénario "plein" en page Modèle, revenez à Simulation, montrez le conflit T1/T3, tirez T3, montrez le blocage en page Analyse |
| 9:00–10:00 | Conclusion | Résumez ce qui a été fait et les améliorations futures (capteurs, barrière, tarifs...) |

Pour l'enregistrement, utilisez l'enregistreur d'écran natif de votre
système (Windows : `Win + G` ; Mac : `Cmd + Shift + 5`), ou OBS Studio si
vous l'avez déjà. Enregistrez votre voix en même temps pour expliquer
chaque étape.

---

## 6. Ce qui est déjà fait vs les extensions possibles

**Déjà fait et fonctionnel** : modèle complet (7 places, 6 transitions),
franchissement, marquage, historique, matrices Pré/Post/W, détection de
conflits, détection de blocage, 5 scénarios prêts à l'emploi, export JSON,
persistance SQLite de l'historique, interface web complète en français.

**Non nécessaire pour la version 1** (mentionné dans le cahier des
charges comme amélioration future, à ne pas faire avant la soutenance) :
capteurs réels, barrière physique, reconnaissance de plaque, plusieurs
zones de parking, tarification, notifications.

---

## 7. En cas de problème

- **`ModuleNotFoundError: No module named 'flask'`** → vous n'avez pas
  fait `pip install -r requirements.txt`, ou vous n'êtes pas dans le bon
  environnement virtuel.
- **`Address already in use`** → un ancien serveur tourne encore ; fermez
  le terminal précédent ou changez de port avec `app.run(port=5050)`
  dans `app.py`.
- **La page est blanche / erreur 500** → regardez le message d'erreur
  affiché dans le terminal où tourne `python app.py`, il indique
  exactement la ligne du problème.
