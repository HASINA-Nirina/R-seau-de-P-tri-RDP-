# -*- coding: utf-8 -*-
"""
app.py - Application Flask "Parking Intelligent - Reseau de Petri"

Lancement local :
    pip install -r requirements.txt
    python app.py
puis ouvrir http://127.0.0.1:5000 dans le navigateur.
"""

import json
import os
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file, g
from flask_wtf import CSRFProtect

from petri import (
    PetriNet, PLACES, TRANSITIONS, PRE, POST, INHIBITORS,
    SCENARIOS, PLACE_IDS, TRANSITION_IDS, PLACE_NAMES, TRANSITION_NAMES,
)

app = Flask(__name__)

# Cle secrete necessaire a Flask-WTF pour generer/verifier le jeton CSRF.
# En local/demo on utilise une valeur par defaut ; en production on la
# fournirait via une variable d'environnement (jamais en dur dans le code).
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-projet-rdp-parking")

# Protection CSRF activee globalement (repond a l'alerte "disabling CSRF
# protection"). Les routes /api/* sont exemptees juste en dessous : ce sont
# des endpoints JSON appeles en AJAX (fetch) par notre propre JavaScript,
# pas des formulaires HTML classiques soumis avec des cookies de session.
csrf = CSRFProtect(app)

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "parking_rdp.db")

# Etat de simulation en memoire (un seul reseau actif : suffisant pour une
# demonstration / soutenance individuelle). L'historique est en plus
# persiste dans SQLite pour repondre a l'exigence de persistance du cahier
# des charges.
net = PetriNet(scenario="normal")


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        db = g._database = sqlite3.connect(DB_PATH)
        db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario TEXT,
                step INTEGER,
                transition TEXT,
                old_marking TEXT,
                new_marking TEXT,
                ts TEXT
            )
        """)
        db.commit()
    return db


@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def log_to_db(entry):
    db = get_db()
    db.execute(
        "INSERT INTO history (scenario, step, transition, old_marking, new_marking, ts) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            net.scenario,
            entry["step"],
            entry["transition"],
            json.dumps(entry["old"]),
            json.dumps(entry["new"]),
            entry["timestamp"],
        ),
    )
    db.commit()


# ---------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/model", methods=["GET"])
def model_page():
    return render_template(
        "model.html",
        places=PLACES,
        transitions=TRANSITIONS,
        pre=PRE,
        post=POST,
        inhibitors=INHIBITORS,
        scenarios=list(SCENARIOS.keys()),
        current_scenario=net.scenario,
    )


@app.route("/simulation", methods=["GET"])
def simulation_page():
    return render_template(
        "simulation.html",
        places=PLACES,
        transitions=TRANSITIONS,
    )


@app.route("/analysis", methods=["GET"])
def analysis_page():
    return render_template(
        "analysis.html",
        places=PLACES,
        transitions=TRANSITIONS,
    )


# ---------------------------------------------------------------------
# API JSON
# ---------------------------------------------------------------------

@app.route("/api/state", methods=["GET"])
def api_state():
    return jsonify(net.to_dict())


@app.route("/api/scenario", methods=["POST"])
@csrf.exempt
def api_scenario():
    data = request.get_json(force=True)
    scenario = data.get("scenario")
    try:
        net.set_scenario(scenario)
        return jsonify({"ok": True, **net.to_dict()})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/custom_marking", methods=["POST"])
@csrf.exempt
def api_custom_marking():
    data = request.get_json(force=True)
    marking = data.get("marking", {})
    net.set_custom_marking(marking)
    return jsonify({"ok": True, **net.to_dict()})


@app.route("/api/fire", methods=["POST"])
@csrf.exempt
def api_fire():
    data = request.get_json(force=True)
    t = data.get("transition")
    try:
        entry = net.fire(t)
        log_to_db(entry)
        return jsonify({"ok": True, "fired": entry, **net.to_dict()})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e), **net.to_dict()}), 400


@app.route("/api/reset", methods=["POST"])
@csrf.exempt
def api_reset():
    net.reset()
    return jsonify({"ok": True, **net.to_dict()})


@app.route("/api/matrices", methods=["GET"])
def api_matrices():
    return jsonify({
        "places": PLACE_IDS,
        "transitions": TRANSITION_IDS,
        "pre": net.pre_matrix(),
        "post": net.post_matrix(),
        "w": net.incidence_matrix(),
    })


@app.route("/api/analysis", methods=["GET"])
def api_analysis():
    return jsonify({
        "conflicts_structural": net.structural_conflicts(),
        "conflicts_active": net.active_conflicts(),
        "stats": net.stats(),
        "properties": net.properties_summary(),
        "blocked": net.is_blocked(),
        "enabled": net.enabled_transitions(),
    })


@app.route("/api/export", methods=["GET"])
def api_export():
    data = net.to_dict()
    data["place_names"] = PLACE_NAMES
    data["transition_names"] = TRANSITION_NAMES
    data["exported_at"] = datetime.now().isoformat()
    path = os.path.join(os.path.dirname(__file__), "instance", "export_rdp_parking.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return send_file(path, as_attachment=True, download_name="export_rdp_parking.json")


if __name__ == "__main__":
    # Le mode debug n'est plus force en dur : il est desactive par defaut
    # et ne s'active que si vous lancez explicitement :
    #   FLASK_DEBUG=1 python app.py        (Mac/Linux)
    #   set FLASK_DEBUG=1 && python app.py  (Windows cmd)
    # Pour la demo/soutenance, laissez la valeur par defaut (debug off) :
    # l'application fonctionne exactement pareil, seul l'auto-reload et le
    # debogueur interactif de Flask sont desactives.
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode)
