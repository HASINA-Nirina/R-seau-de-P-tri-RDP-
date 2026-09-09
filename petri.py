# -*- coding: utf-8 -*-
"""
petri.py
Moteur de Reseau de Petri (RDP) pour le projet "Parking Intelligent".

Objets modelises :
- Places (P1..P7)     -> etats du systeme
- Transitions (T1..T6) -> evenements
- Arcs Pre / Post      -> consommation / production de jetons
- Arc inhibiteur       -> extension classique du RDP utilisee pour tester
                          qu'une place est VIDE (ici : plus de place libre)

Le modele reprend le cahier des charges (places P1..P7, transitions T1..T6).
Remarque du cahier des charges : "la separation exacte entre T2 et T3 pourra
etre ajustee pendant l'implementation afin d'eviter une duplication de
consommation/production de jetons". Le choix retenu ici :

    T1 : Controle entree        P1 -> P2
    T2 : Affecter une place     P2 + P3 -> P4      (garer le vehicule)
    T3 : Signaler parking plein P1 -> P6           (actif seulement si P3 == 0)
    T4 : Demander sortie        P4 -> P5
    T5 : Valider paiement       P5 -> P7
    T6 : Liberer la place       P7 -> P3

Ce choix cree naturellement :
- un CONFLIT structurel sur P1 (P1 alimente a la fois T1 et T3)
- une SYNCHRONISATION sur T2 (a besoin d'un jeton dans P2 ET dans P3)
- un cycle complet de reutilisation de la ressource "place de parking" (P3)
"""

from copy import deepcopy
from datetime import datetime

PLACES = [
    ("P1", "Vehicule en entree"),
    ("P2", "Acces valide"),
    ("P3", "Place libre"),
    ("P4", "Vehicule gare"),
    ("P5", "Sortie demandee"),
    ("P6", "Parking plein (signal)"),
    ("P7", "Paiement valide"),
]

TRANSITIONS = [
    ("T1", "Controle entree"),
    ("T2", "Affecter une place / garer"),
    ("T3", "Signaler parking plein"),
    ("T4", "Demander sortie"),
    ("T5", "Valider paiement"),
    ("T6", "Liberer la place"),
]

# Arcs PRE : transition -> {place: poids} (jetons consommes)
PRE = {
    "T1": {"P1": 1},
    "T2": {"P2": 1, "P3": 1},
    "T3": {"P1": 1},
    "T4": {"P4": 1},
    "T5": {"P5": 1},
    "T6": {"P7": 1},
}

# Arcs POST : transition -> {place: poids} (jetons produits)
POST = {
    "T1": {"P2": 1},
    "T2": {"P4": 1},
    "T3": {"P6": 1},
    "T4": {"P5": 1},
    "T5": {"P7": 1},
    "T6": {"P3": 1},
}

# Arc inhibiteur : transition -> place qui DOIT etre a 0 pour que la
# transition soit franchissable (extension classique du RDP, utilisee ici
# pour detecter "plus aucune place libre").
INHIBITORS = {
    "T3": "P3",
}

SCENARIOS = {
    "vide":              {"P1": 0, "P2": 0, "P3": 3, "P4": 0, "P5": 0, "P6": 0, "P7": 0},
    "normal":            {"P1": 1, "P2": 1, "P3": 3, "P4": 0, "P5": 0, "P6": 0, "P7": 0},
    "presque_plein":     {"P1": 1, "P2": 1, "P3": 1, "P4": 0, "P5": 0, "P6": 0, "P7": 0},
    "plein":             {"P1": 1, "P2": 0, "P3": 0, "P4": 0, "P5": 0, "P6": 0, "P7": 0},
    "sortie_simultanee": {"P1": 0, "P2": 0, "P3": 0, "P4": 2, "P5": 1, "P6": 0, "P7": 0},
}

PLACE_IDS = [p[0] for p in PLACES]
TRANSITION_IDS = [t[0] for t in TRANSITIONS]
PLACE_NAMES = dict(PLACES)
TRANSITION_NAMES = dict(TRANSITIONS)


class PetriNet:
    def __init__(self, scenario="normal"):
        self.scenario = scenario
        self.initial_marking = deepcopy(SCENARIOS[scenario])
        self.marking = deepcopy(self.initial_marking)
        self.history = []  # liste de dict : step, transition, old, new, timestamp

    # ---------- gestion de base ----------

    def set_scenario(self, scenario):
        if scenario not in SCENARIOS:
            raise ValueError("Scenario inconnu: %s" % scenario)
        self.scenario = scenario
        self.initial_marking = deepcopy(SCENARIOS[scenario])
        self.reset()

    def set_custom_marking(self, marking: dict):
        """Permet de saisir un marquage initial personnalise (F3)."""
        m = {p: int(marking.get(p, 0)) for p in PLACE_IDS}
        self.scenario = "personnalise"
        self.initial_marking = m
        self.reset()

    def reset(self):
        self.marking = deepcopy(self.initial_marking)
        self.history = []

    # ---------- franchissement ----------

    def is_enabled(self, t):
        for p, w in PRE.get(t, {}).items():
            if self.marking.get(p, 0) < w:
                return False
        inhib_place = INHIBITORS.get(t)
        if inhib_place is not None and self.marking.get(inhib_place, 0) != 0:
            return False
        return True

    def enabled_transitions(self):
        return [t for t in TRANSITION_IDS if self.is_enabled(t)]

    def fire(self, t):
        if t not in TRANSITION_IDS:
            raise ValueError("Transition inconnue: %s" % t)
        if not self.is_enabled(t):
            raise ValueError("Transition %s non franchissable dans le marquage courant" % t)

        old_marking = deepcopy(self.marking)
        for p, w in PRE.get(t, {}).items():
            self.marking[p] -= w
        for p, w in POST.get(t, {}).items():
            self.marking[p] = self.marking.get(p, 0) + w

        entry = {
            "step": len(self.history) + 1,
            "transition": t,
            "transition_name": TRANSITION_NAMES[t],
            "old": old_marking,
            "new": deepcopy(self.marking),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        self.history.append(entry)
        return entry

    def is_blocked(self):
        return len(self.enabled_transitions()) == 0

    # ---------- matrices ----------

    def pre_matrix(self):
        return [[PRE.get(t, {}).get(p, 0) for t in TRANSITION_IDS] for p in PLACE_IDS]

    def post_matrix(self):
        return [[POST.get(t, {}).get(p, 0) for t in TRANSITION_IDS] for p in PLACE_IDS]

    def incidence_matrix(self):
        pre = self.pre_matrix()
        post = self.post_matrix()
        return [[post[i][j] - pre[i][j] for j in range(len(TRANSITION_IDS))]
                for i in range(len(PLACE_IDS))]

    # ---------- analyse ----------

    def structural_conflicts(self):
        """Une place en amont (PRE) de plusieurs transitions = conflit structurel."""
        conflicts = {}
        for p in PLACE_IDS:
            competitors = [t for t in TRANSITION_IDS if PRE.get(t, {}).get(p, 0) > 0]
            if len(competitors) > 1:
                conflicts[p] = competitors
        return conflicts

    def active_conflicts(self):
        """Parmi les conflits structurels, lesquels sont reellement actifs
        maintenant (plusieurs transitions concurrentes sont simultanement
        franchissables) ?"""
        active = {}
        struct = self.structural_conflicts()
        for p, competitors in struct.items():
            enabled_competitors = [t for t in competitors if self.is_enabled(t)]
            if len(enabled_competitors) > 1:
                active[p] = enabled_competitors
        return active

    def stats(self):
        counts = {t: 0 for t in TRANSITION_IDS}
        for h in self.history:
            counts[h["transition"]] += 1

        capacite_totale = self.initial_marking.get("P3", 0) + self.marking.get("P4", 0)
        occupees = self.marking.get("P4", 0)
        taux_occupation = round((occupees / capacite_totale) * 100, 1) if capacite_totale > 0 else 0.0

        return {
            "total_steps": len(self.history),
            "per_transition": counts,
            "places_libres": self.marking.get("P3", 0),
            "vehicules_gares": self.marking.get("P4", 0),
            "parking_plein": self.marking.get("P6", 0) > 0,
            "taux_occupation_pct": taux_occupation,
            "nombre_entrees": counts.get("T1", 0),
            "nombre_sorties": counts.get("T6", 0),
        }

    def properties_summary(self):
        """Indicateurs pedagogiques simples (pas une preuve formelle) bases
        sur les notions du cours : activite, repetitivite, vivacite,
        concurrence."""
        enabled_now = self.enabled_transitions()
        return {
            "activite": (
                "Le reseau est actif : au moins une transition est franchissable."
                if enabled_now else
                "Le reseau est BLOQUE : aucune transition n'est franchissable "
                "dans le marquage courant."
            ),
            "repetitivite": (
                "Le cycle T2 -> T4 -> T5 -> T6 -> (retour du jeton dans P3) "
                "montre une sequence repetable : une place liberee peut de "
                "nouveau etre affectee a un nouveau vehicule."
            ),
            "vivacite": (
                "Depuis M0, toutes les transitions T1..T6 peuvent, selon le "
                "scenario choisi, redevenir franchissables : le systeme n'est "
                "pas condamne a un sous-ensemble de transitions."
            ),
            "concurrence": (
                "P1 alimente T1 et T3 : situation de conflit/competition. "
                "Plusieurs jetons dans P4/P5 (scenario 'sortie_simultanee') "
                "montrent des vehicules progressant en parallele dans le "
                "meme sous-reseau."
            ),
        }

    # ---------- export ----------

    def to_dict(self):
        return {
            "places": [{"id": p, "name": n} for p, n in PLACES],
            "transitions": [{"id": t, "name": n} for t, n in TRANSITIONS],
            "arcs_pre": PRE,
            "arcs_post": POST,
            "inhibitors": INHIBITORS,
            "scenario": self.scenario,
            "initial_marking": self.initial_marking,
            "marking": self.marking,
            "enabled": self.enabled_transitions(),
            "blocked": self.is_blocked(),
            "history": self.history,
        }