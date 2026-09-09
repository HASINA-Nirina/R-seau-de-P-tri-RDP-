// simulation.js
let PLACE_NAMES = {};
let TRANSITION_NAMES = {};

async function loadState() {
    const res = await fetch('/api/state');
    return res.json();
}

function renderMarkingTable(marking) {
    const tbl = document.getElementById('marking-table');
    let html = '<tr><th>Place</th><th>Nom</th><th>Jetons</th></tr>';
    Object.keys(marking).forEach(p => {
        html += `<tr><td>${p}</td><td>${PLACE_NAMES[p] || ''}</td><td><b>${marking[p]}</b></td></tr>`;
    });
    tbl.innerHTML = html;
}

function renderTransitionsList(enabled, allTransitions) {
    const holder = document.getElementById('transitions-list');
    holder.innerHTML = '';
    allTransitions.forEach(t => {
        const isEnabled = enabled.includes(t.id);
        const btn = document.createElement('button');
        btn.className = 'transition-btn' + (isEnabled ? ' enabled' : '');
        btn.disabled = !isEnabled;
        btn.textContent = `${t.id} — ${t.name}${isEnabled ? ' ✅ franchissable' : ''}`;
        btn.addEventListener('click', () => fireTransition(t.id));
        holder.appendChild(btn);
    });
}

function renderTransitionSelect(enabled, allTransitions) {
    const select = document.getElementById('transition-select');
    const names = {};
    allTransitions.forEach(t => names[t.id] = t.name);
    if (enabled.length === 0) {
        select.innerHTML = '<option value="">Aucune transition franchissable</option>';
        select.disabled = true;
    } else {
        select.disabled = false;
        select.innerHTML = enabled.map(t => `<option value="${t}">${t} — ${names[t]}</option>`).join('');
    }
}

function renderHistory(history) {
    const holder = document.getElementById('history-list');
    if (history.length === 0) {
        holder.innerHTML = '<p class="note">Aucun tir pour le moment.</p>';
        return;
    }
    holder.innerHTML = history.slice().reverse().map(h => `
        <div class="history-item">
            <b>Étape ${h.step}</b> — ${h.transition} (${h.transition_name}) à ${h.timestamp}<br>
            Marquage : ${JSON.stringify(h.old)} → ${JSON.stringify(h.new)}
        </div>
    `).join('');
}

let LAST_ENABLED = [];

function applyState(data) {
    renderMarkingTable(data.marking);
    renderTransitionsList(data.enabled, data.transitions);
    renderTransitionSelect(data.enabled, data.transitions);
    renderHistory(data.history);
    updateDiagram(data.marking, data.enabled);
    LAST_ENABLED = data.enabled;
    const banner = document.getElementById('blocked-banner');
    banner.classList.toggle('hidden', !data.blocked);
}

async function fireTransition(t) {
    const res = await fetch('/api/fire', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({transition: t})
    });
    const data = await res.json();
    applyState(data);
}

document.getElementById('btn-tirer').addEventListener('click', () => {
    const select = document.getElementById('transition-select');
    if (select.value) fireTransition(select.value);
});

document.getElementById('btn-suivant').addEventListener('click', () => {
    // Mode "etape par etape" (F7) : tire automatiquement la premiere
    // transition franchissable, pour derouler une demonstration rapide.
    if (LAST_ENABLED.length > 0) fireTransition(LAST_ENABLED[0]);
});

document.getElementById('btn-reset').addEventListener('click', async () => {
    const res = await fetch('/api/reset', {method: 'POST'});
    const data = await res.json();
    applyState(data);
});

document.getElementById('btn-export').addEventListener('click', () => {
    window.location.href = '/api/export';
});

(async function init() {
    const data = await loadState();
    data.places.forEach(p => PLACE_NAMES[p.id] = p.name);
    data.transitions.forEach(t => TRANSITION_NAMES[t.id] = t.name);
    renderDiagram(data.places.map(p => [p.id, p.name]), data.transitions.map(t => [t.id, t.name]));
    applyState(data);
})();