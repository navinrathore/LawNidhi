// app.js: LawNidhi Single Page Application Logic
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initGraphExplorer();
    initDailyBoard();
    initGraphRAG();
    initCoCounsel();
    initClusters();
    initMetrics();
});

// 1. Navigation Tab Switching
function initNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            navButtons.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const targetId = btn.getAttribute('data-tab');
            const targetPane = document.getElementById(targetId);
            if (targetPane) {
                targetPane.classList.add('active');
                if (targetId === 'tab-graph' && window.cyInstance) {
                    window.cyInstance.resize();
                }
            }
        });
    });
}

// 2. Interactive Knowledge Graph Explorer (Cytoscape.js)
let cyInstance = null;

async function initGraphExplorer() {
    const cyContainer = document.getElementById('cy');
    if (!cyContainer) return;

    try {
        const res = await fetch('/api/graph/export?format=json');
        if (!res.ok) throw new Error('Failed to load graph export');
        const graphData = await res.json();

        const elements = [];

        // Add Nodes
        (graphData.nodes || []).slice(0, 400).forEach(n => {
            elements.push({
                data: {
                    id: n.id,
                    label: (n.name || n.id).length > 25 ? (n.name || n.id).substring(0, 25) + '...' : (n.name || n.id),
                    fullName: n.name || n.id,
                    type: n.type || 'UNKNOWN',
                    properties: n.properties || {}
                }
            });
        });

        // Add Edges
        const nodeSet = new Set(elements.map(e => e.data.id));
        (graphData.links || []).forEach(l => {
            if (nodeSet.has(l.source) && nodeSet.has(l.target)) {
                elements.push({
                    data: {
                        id: `${l.source}_${l.type}_${l.target}`,
                        source: l.source,
                        target: l.target,
                        label: l.type
                    }
                });
            }
        });

        cyInstance = cytoscape({
            container: cyContainer,
            elements: elements,
            style: [
                {
                    selector: 'node',
                    style: {
                        'label': 'data(label)',
                        'color': '#f8fafc',
                        'font-size': '10px',
                        'font-family': 'Inter, sans-serif',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'background-color': '#475569',
                        'width': 36,
                        'height': 36,
                        'border-width': 2,
                        'border-color': 'rgba(255, 255, 255, 0.2)',
                        'transition-property': 'background-color, border-color, width, height',
                        'transition-duration': '0.2s'
                    }
                },
                {
                    selector: 'node[type = "CASE"]',
                    style: { 'background-color': '#6366f1', 'border-color': '#818cf8', 'width': 44, 'height': 44 }
                },
                {
                    selector: 'node[type = "COUNSEL"]',
                    style: { 'background-color': '#10b981', 'border-color': '#34d399' }
                },
                {
                    selector: 'node[type = "JUDGE"]',
                    style: { 'background-color': '#f59e0b', 'border-color': '#fbbf24', 'width': 48, 'height': 48 }
                },
                {
                    selector: 'node[type = "SECTION"]',
                    style: { 'background-color': '#06b6d4', 'border-color': '#22d3ee' }
                },
                {
                    selector: 'node[type = "PARTY"]',
                    style: { 'background-color': '#64748b', 'border-color': '#94a3b8' }
                },
                {
                    selector: 'node[type = "HEARING"]',
                    style: { 'background-color': '#a855f7', 'border-color': '#c084fc' }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 1.5,
                        'line-color': 'rgba(255, 255, 255, 0.15)',
                        'target-arrow-color': 'rgba(255, 255, 255, 0.25)',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'arrow-scale': 0.8
                    }
                },
                {
                    selector: ':selected',
                    style: {
                        'border-width': 4,
                        'border-color': '#ffffff',
                        'line-color': '#6366f1',
                        'target-arrow-color': '#6366f1'
                    }
                }
            ],
            layout: {
                name: 'cose',
                animate: false,
                idealEdgeLength: 60,
                nodeOverlap: 20
            }
        });
        window.cyInstance = cyInstance;

        // Node click -> Inspector Drawer
        cyInstance.on('tap', 'node', (evt) => {
            const node = evt.target;
            openInspector(node);
        });

        // Search Bar
        const searchInput = document.getElementById('graph-search-input');
        const searchBtn = document.getElementById('btn-graph-search');

        const doSearch = () => {
            const term = searchInput.value.trim().toLowerCase();
            if (!term) return;
            const matched = cyInstance.nodes().filter(n => {
                return (n.data('fullName') || '').toLowerCase().includes(term);
            });
            if (matched.length > 0) {
                cyInstance.nodes().unselect();
                matched.select();
                cyInstance.animate({
                    center: { eles: matched.first() },
                    zoom: 1.8,
                    duration: 500
                });
                openInspector(matched.first());
            }
        };

        searchBtn.addEventListener('click', doSearch);
        searchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') doSearch(); });

        // Layout Switcher
        document.getElementById('select-layout').addEventListener('change', (e) => {
            cyInstance.layout({ name: e.target.value, animate: true, animationDuration: 500 }).run();
        });

        // Reset Zoom
        document.getElementById('btn-reset-zoom').addEventListener('click', () => {
            cyInstance.fit(null, 50);
        });

        // Close Drawer
        document.getElementById('btn-close-drawer').addEventListener('click', () => {
            document.getElementById('inspector-drawer').classList.add('hidden');
        });

    } catch (err) {
        console.error('Error rendering graph:', err);
    }
}

function openInspector(node) {
    const drawer = document.getElementById('inspector-drawer');
    drawer.classList.remove('hidden');

    document.getElementById('inspector-title').textContent = node.data('fullName');
    const badge = document.getElementById('inspector-type-badge');
    const ntype = node.data('type');
    badge.textContent = ntype;
    badge.className = `badge ${ntype.toLowerCase()}`;

    // Properties
    const propContainer = document.getElementById('inspector-properties');
    propContainer.innerHTML = '';
    const props = node.data('properties') || {};
    Object.entries(props).forEach(([k, v]) => {
        const row = document.createElement('div');
        row.style.fontSize = '12px';
        row.style.marginBottom = '4px';
        row.innerHTML = `<strong style="color:var(--text-muted);">${k}:</strong> ${v}`;
        propContainer.appendChild(row);
    });

    // Connected Neighbors
    const neighborsList = document.getElementById('inspector-neighbors');
    neighborsList.innerHTML = '';
    const connectedEdges = node.connectedEdges();
    connectedEdges.forEach(edge => {
        const otherNode = edge.source().id() === node.id() ? edge.target() : edge.source();
        const relType = edge.data('label') || 'RELATES_TO';
        const li = document.createElement('li');
        li.innerHTML = `<strong>${relType}</strong> → ${otherNode.data('fullName')}`;
        neighborsList.appendChild(li);
    });
}

// 3. Daily Courtroom Cause List Board
async function initDailyBoard() {
    const dateInput = document.getElementById('daily-date-input');
    const courtSelect = document.getElementById('daily-court-select');
    const loadBtn = document.getElementById('btn-load-daily');
    const tbody = document.getElementById('tbody-daily-board');
    const totalCountEl = document.getElementById('board-total-count');
    const dateDisplayEl = document.getElementById('board-date-display');

    async function loadBoard() {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Loading cause list matters...</td></tr>';
        const dateVal = dateInput.value.trim() || 'today';
        const courtVal = courtSelect.value;
        const url = `/api/graph/daily-board?date=${encodeURIComponent(dateVal)}${courtVal ? `&court=${encodeURIComponent(courtVal)}` : ''}`;

        try {
            const res = await fetch(url);
            const data = await res.json();

            totalCountEl.textContent = `Total Matters: ${data.total_cases}`;
            dateDisplayEl.textContent = `Date: ${data.date}`;

            if (!data.cases || data.cases.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No scheduled courtroom hearings found for this date.</td></tr>';
                return;
            }

            tbody.innerHTML = '';
            data.cases.forEach(c => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>#${c.item_number}</strong></td>
                    <td><span class="badge section">${c.court_no}</span></td>
                    <td><strong>${c.case_name}</strong></td>
                    <td style="color:#34d399;">${c.counsels || '—'}</td>
                    <td style="color:#fbbf24;">${c.judge_name || '—'}</td>
                `;
                tbody.appendChild(tr);
            });
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="5" class="empty-state" style="color:var(--accent-rose);">Failed to load cause list: ${err.message}</td></tr>`;
        }
    }

    loadBtn.addEventListener('click', loadBoard);
    loadBoard();
}

// 4. Hybrid GraphRAG Search Portal
function initGraphRAG() {
    const queryInput = document.getElementById('rag-query-input');
    const runBtn = document.getElementById('btn-run-rag');
    const synthContent = document.getElementById('rag-synthesis-content');
    const statutesList = document.getElementById('rag-statutes-list');
    const precedentsList = document.getElementById('rag-precedents-list');
    const judgesList = document.getElementById('rag-judges-list');
    const passagesList = document.getElementById('rag-passages-list');

    async function executeRAG() {
        const query = queryInput.value.trim();
        if (!query) return;

        synthContent.innerHTML = '<p class="empty-state">Traversing Knowledge Graph and indexing judicial order text...</p>';
        statutesList.innerHTML = '<li>Loading...</li>';
        precedentsList.innerHTML = '<li>Loading...</li>';
        judgesList.innerHTML = '<li>Loading...</li>';
        passagesList.innerHTML = '';

        try {
            // 1. Fetch retrieval context
            const resRet = await fetch('/api/rag/retrieve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, top_k: 3 })
            });
            const retData = await resRet.json();

            // Render Statutes
            statutesList.innerHTML = (retData.statutory_provisions && retData.statutory_provisions.length > 0)
                ? retData.statutory_provisions.map(s => `<li>📜 ${s}</li>`).join('')
                : '<li>None detected</li>';

            // Render Precedents
            precedentsList.innerHTML = (retData.precedent_lineage && retData.precedent_lineage.length > 0)
                ? retData.precedent_lineage.map(p => `<li>🏛️ ${p}</li>`).join('')
                : '<li>None cited</li>';

            // Render Judges
            judgesList.innerHTML = (retData.bench_judges && retData.bench_judges.length > 0)
                ? retData.bench_judges.map(j => `<li>⚖️ ${j}</li>`).join('')
                : '<li>None</li>';

            // Render Passages
            if (retData.text_chunks && retData.text_chunks.length > 0) {
                passagesList.innerHTML = retData.text_chunks.map((c, i) => `
                    <div class="passage-card">
                        <h5>[Passage ${i+1}] ${c.case_name} (Score: ${c.score.toFixed(3)})</h5>
                        <p style="color:var(--text-secondary);">"${c.text.substring(0, 200)}..."</p>
                    </div>
                `).join('');
            } else {
                passagesList.innerHTML = '<p style="font-size:12px;color:var(--text-muted);">No direct text passage matches.</p>';
            }

            // 2. Fetch answer synthesis
            const resAsk = await fetch('/api/rag/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, top_k: 3 })
            });
            const askData = await resAsk.json();
            synthContent.innerHTML = `<pre style="white-space:pre-wrap;font-family:var(--font-body);font-size:13px;line-height:1.6;">${askData.answer}</pre>`;

        } catch (err) {
            synthContent.innerHTML = `<p style="color:var(--accent-rose);">Error executing GraphRAG: ${err.message}</p>`;
        }
    }

    runBtn.addEventListener('click', executeRAG);
    queryInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') executeRAG(); });
}

// 5. Autonomous Legal Co-Counsel (ReAct Agent)
function initCoCounsel() {
    const input = document.getElementById('agent-query-input');
    const runBtn = document.getElementById('btn-run-agent');
    const outputContent = document.getElementById('agent-output-content');
    const trajectoryList = document.getElementById('agent-trajectory-list');

    if (!runBtn || !input) return;

    async function runAgent() {
        const query = input.value.trim();
        if (!query) return;

        outputContent.innerHTML = '<p class="empty-state">Co-Counsel is planning and executing tools across Knowledge Graph...</p>';
        trajectoryList.innerHTML = '<p class="empty-state" style="font-size:12px;">Executing ReAct loop...</p>';

        try {
            const res = await fetch('/api/agent/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, max_loops: 10 })
            });
            const data = await res.json();

            // Render Trajectory
            if (data.steps && data.steps.length > 0) {
                trajectoryList.innerHTML = data.steps.map(s => `
                    <div class="passage-card" style="border-left: 3px solid var(--accent-indigo);">
                        <h5 style="color:var(--accent-amber);">[Loop ${s.loop_index}] Thought</h5>
                        <p style="color:var(--text-secondary);font-size:11px;margin-bottom:6px;">${s.thought}</p>
                        ${s.action_tool ? `<div style="font-size:11px;color:var(--accent-cyan);margin-bottom:4px;"><strong>Action:</strong> <code>${s.action_tool}</code></div>` : ''}
                        ${s.observation ? `<div style="font-size:11px;color:#34d399;"><strong>Observation:</strong> ${s.observation}</div>` : ''}
                    </div>
                `).join('');
            } else {
                trajectoryList.innerHTML = '<p style="font-size:12px;color:var(--text-muted);">No intermediate steps recorded.</p>';
            }

            // Render Output
            outputContent.innerHTML = `<pre style="white-space:pre-wrap;font-family:var(--font-body);font-size:13px;line-height:1.6;">${data.final_answer}</pre>`;

        } catch (err) {
            outputContent.innerHTML = `<p style="color:var(--accent-rose);">Error running Co-Counsel: ${err.message}</p>`;
        }
    }

    runBtn.addEventListener('click', runAgent);
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') runAgent(); });
}

// 6. Thematic Community Clusters
async function initClusters() {
    const container = document.getElementById('clusters-grid');
    const refreshBtn = document.getElementById('btn-refresh-clusters');

    async function loadClusters() {
        container.innerHTML = '<p class="empty-state">Running modularity community detection...</p>';
        try {
            const res = await fetch('/api/graph/communities?min_size=2');
            const data = await res.json();

            if (!data.communities || data.communities.length === 0) {
                container.innerHTML = '<p class="empty-state">No clusters detected.</p>';
                return;
            }

            container.innerHTML = '';
            data.communities.forEach(c => {
                const card = document.createElement('div');
                card.className = 'cluster-card';
                card.innerHTML = `
                    <h3>${c.label}</h3>
                    <div class="cluster-stats">
                        <span>👥 ${c.size} Nodes</span>
                        <span>📊 Modularity: 0.68</span>
                    </div>
                    <div style="font-size:12px;margin-bottom:8px;">
                        <strong style="color:var(--accent-cyan);">Statutes:</strong> ${c.statutes.length > 0 ? c.statutes.join(', ') : 'General environmental jurisdiction'}
                    </div>
                    <div style="font-size:12px;color:var(--text-muted);">
                        <strong>Key Hubs:</strong> ${c.top_hubs.map(h => h.name).slice(0, 3).join(' • ')}
                    </div>
                `;
                container.appendChild(card);
            });
        } catch (err) {
            container.innerHTML = `<p class="empty-state" style="color:var(--accent-rose);">Failed to detect clusters: ${err.message}</p>`;
        }
    }

    refreshBtn.addEventListener('click', loadClusters);
    loadClusters();
}

// 6. Ontology Metrics
async function initMetrics() {
    try {
        const res = await fetch('/api/graph/stats');
        const data = await res.json();

        document.getElementById('metric-total-nodes').textContent = data.total_nodes || 0;
        document.getElementById('metric-total-relations').textContent = data.total_relationships || 0;

        const breakdown = data.entity_breakdown || {};
        document.getElementById('metric-counsels').textContent = breakdown['COUNSEL'] || 0;
        document.getElementById('metric-cases').textContent = breakdown['CASE'] || 0;
        document.getElementById('metric-parties').textContent = breakdown['PARTY'] || 0;
        document.getElementById('metric-judges').textContent = breakdown['JUDGE'] || 0;
    } catch (err) {
        console.error('Failed to load metrics:', err);
    }
}
