// analysis.js

function renderMatrix(container, places, transitions, matrix) {
    let html = '<table class="tbl"><tr><th>Place \\ Transition</th>';
    transitions.forEach(t => html += `<th>${t}</th>`);
    html += '</tr>';
    matrix.forEach((row, i) => {
        html += `<tr><th>${places[i]}</th>`;
        row.forEach(v => {
            const cls = v > 0 ? 'style="color:#16a34a;font-weight:700"' : (v < 0 ? 'style="color:#dc2626;font-weight:700"' : '');
            html += `<td ${cls}>${v}</td>`;
        });
        html += '</tr>';
    });
    html += '</table>';
    document.getElementById(container).innerHTML = html;
}

function renderConflicts(structural, active) {
    let html = '';
    const keys = Object.keys(structural);
    if (keys.length === 0) {
        html = '<p class="note">Aucun conflit structurel détecté.</p>';
    } else {
        html += '<ul>';
        keys.forEach(p => {
            const isActive = active[p] !== undefined;
            html += `<li><b>${p}</b> alimente plusieurs transitions : ${structural[p].join(', ')}`;
            html += isActive
                ? ` — <span style="color:#dc2626;font-weight:700">CONFLIT ACTIF maintenant (${active[p].join(', ')} sont toutes deux franchissables)</span>`
                : ' — conflit structurel (pas actif dans le marquage courant)';
            html += '</li>';
        });
        html += '</ul>';
    }
    document.getElementById('conflicts').innerHTML = html;
}

function renderProperties(props) {
    let html = '<ul>';
    Object.keys(props).forEach(k => {
        html += `<li><b>${k}</b> : ${props[k]}</li>`;
    });
    html += '</ul>';
    document.getElementById('properties').innerHTML = html;
}

function renderStats(stats) {
    let html = `<table class="tbl">
        <tr><td>Nombre total de tirs (transitions exécutées)</td><td><b>${stats.total_steps}</b></td></tr>
        <tr><td>Taux d'occupation du parking</td><td><b>${stats.taux_occupation_pct}%</b></td></tr>
        <tr><td>Nombre d'entrées (T1 franchie)</td><td><b>${stats.nombre_entrees}</b></td></tr>
        <tr><td>Nombre de sorties (T6 franchie)</td><td><b>${stats.nombre_sorties}</b></td></tr>
        <tr><td>Places libres actuellement</td><td><b>${stats.places_libres}</b></td></tr>
        <tr><td>Véhicules garés</td><td><b>${stats.vehicules_gares}</b></td></tr>
        <tr><td>Parking plein signalé</td><td><b>${stats.parking_plein ? 'Oui' : 'Non'}</b></td></tr>
    </table>
    <h4>Tirs par transition</h4>
    <table class="tbl"><tr>`;
    Object.keys(stats.per_transition).forEach(t => html += `<th>${t}</th>`);
    html += '</tr><tr>';
    Object.values(stats.per_transition).forEach(v => html += `<td>${v}</td>`);
    html += '</tr></table>';
    document.getElementById('stats').innerHTML = html;
}

function renderStatus(blocked, enabled) {
    let html = '';
    if (blocked) {
        html = '<p class="banner">⚠️ Le réseau est BLOQUÉ : aucune transition franchissable.</p>';
    } else {
        html = `<p class="note">Transitions actuellement franchissables : <b>${enabled.join(', ') || 'aucune'}</b></p>`;
    }
    document.getElementById('net-status').innerHTML = html;
}

(async function init() {
    const matRes = await fetch('/api/matrices');
    const mat = await matRes.json();
    renderMatrix('mat-pre', mat.places, mat.transitions, mat.pre);
    renderMatrix('mat-post', mat.places, mat.transitions, mat.post);
    renderMatrix('mat-w', mat.places, mat.transitions, mat.w);

    const anRes = await fetch('/api/analysis');
    const an = await anRes.json();
    renderConflicts(an.conflicts_structural, an.conflicts_active);
    renderProperties(an.properties);
    renderStats(an.stats);
    renderStatus(an.blocked, an.enabled);
})();
