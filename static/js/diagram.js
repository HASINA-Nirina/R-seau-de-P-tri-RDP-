// diagram.js
// Construit le SVG du Réseau de Petri (positions fixes) et fournit des
// fonctions pour mettre à jour les jetons et l'état "franchissable".

const LAYOUT = {
    places: {
        P1: {x: 60,  y: 150},
        P2: {x: 280, y: 150},
        P4: {x: 520, y: 150},
        P5: {x: 740, y: 150},
        P7: {x: 960, y: 150},
        P3: {x: 400, y: 280},
        P6: {x: 280, y: 330},
    },
    transitions: {
        T1: {x: 170, y: 150},
        T2: {x: 400, y: 150},
        T4: {x: 630, y: 150},
        T5: {x: 850, y: 150},
        T3: {x: 170, y: 330},
        T6: {x: 850, y: 330},
    },
};

const ARCS = [
    // [from, to, type]  type: "normal" | "inhibitor"
    ["P1", "T1", "normal"],
    ["T1", "P2", "normal"],
    ["P2", "T2", "normal"],
    ["P3", "T2", "normal"],
    ["T2", "P4", "normal"],
    ["P4", "T4", "normal"],
    ["T4", "P5", "normal"],
    ["P5", "T5", "normal"],
    ["T5", "P7", "normal"],
    ["P7", "T6", "normal"],
    ["T6", "P3", "normal"],
    ["P1", "T3", "normal"],
    ["T3", "P6", "normal"],
    ["P3", "T3", "inhibitor"],
];

const R = 34; // rayon des places
const TW = 130, TH = 34; // taille des rectangles de transition

function nodeCenter(id) {
    if (LAYOUT.places[id]) return LAYOUT.places[id];
    if (LAYOUT.transitions[id]) return LAYOUT.transitions[id];
    return {x: 0, y: 0};
}

function edgeEndpoint(fromId, toId) {
    // Recale les points de départ/arrivée sur le bord des formes, pas le centre.
    const a = nodeCenter(fromId);
    const b = nodeCenter(toId);
    const dx = b.x - a.x, dy = b.y - a.y;
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    const ux = dx / len, uy = dy / len;

    function radiusFor(id) {
        return LAYOUT.places[id] ? R : Math.max(TW, TH) / 2.2;
    }
    const ra = radiusFor(fromId), rb = radiusFor(toId);
    return {
        x1: a.x + ux * ra, y1: a.y + uy * ra,
        x2: b.x - ux * rb, y2: b.y - uy * rb,
    };
}

function buildSVG(places, transitions) {
    let svg = `<svg viewBox="0 0 1040 400" xmlns="http://www.w3.org/2000/svg">`;
    svg += `<defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L6,3 z" fill="#94a3b8"></path>
        </marker>
    </defs>`;

    // arcs
    ARCS.forEach(([from, to, type]) => {
        const p = edgeEndpoint(from, to);
        if (type === "inhibitor") {
            svg += `<line class="inhib-line" x1="${p.x1}" y1="${p.y1}" x2="${p.x2}" y2="${p.y2}"></line>
                    <circle cx="${p.x2}" cy="${p.y2}" r="4" fill="none" stroke="#dc2626" stroke-width="1.5"></circle>`;
        } else {
            svg += `<line class="arc-line" x1="${p.x1}" y1="${p.y1}" x2="${p.x2}" y2="${p.y2}"></line>`;
        }
    });

    // places
    places.forEach(([id, name]) => {
        const c = LAYOUT.places[id];
        svg += `
        <g id="place-${id}">
            <circle class="place-circle" cx="${c.x}" cy="${c.y}" r="${R}"></circle>
            <text class="token-count" id="tokens-${id}" x="${c.x}" y="${c.y + 5}">0</text>
            <text class="place-label" x="${c.x}" y="${c.y + R + 16}">${id}</text>
            <text class="place-label" x="${c.x}" y="${c.y + R + 30}" font-size="10">${name}</text>
        </g>`;
    });

    // transitions
    transitions.forEach(([id, name]) => {
        const c = LAYOUT.transitions[id];
        svg += `
        <g id="trans-group-${id}">
            <rect class="trans-rect" id="trans-${id}" x="${c.x - TW/2}" y="${c.y - TH/2}" width="${TW}" height="${TH}" rx="6"></rect>
            <text class="trans-label" x="${c.x}" y="${c.y + 4}">${id}</text>
            <text class="place-label" x="${c.x}" y="${c.y + TH/2 + 14}" font-size="9">${name}</text>
        </g>`;
    });

    svg += `</svg>`;
    return svg;
}

function renderDiagram(places, transitions) {
    document.getElementById("diagram-holder").innerHTML = buildSVG(places, transitions);
}

function updateDiagram(marking, enabled) {
    Object.keys(marking).forEach(p => {
        const el = document.getElementById("tokens-" + p);
        if (el) el.textContent = marking[p];
    });
    document.querySelectorAll(".trans-rect").forEach(rect => {
        const id = rect.id.replace("trans-", "");
        if (enabled.includes(id)) rect.classList.add("enabled");
        else rect.classList.remove("enabled");
    });
}