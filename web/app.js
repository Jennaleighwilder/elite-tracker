/* THE HIDDEN NETWORKS - Real Data */
let graphData = { nodes: [], edges: [] };
let filteredData = { nodes: [], edges: [] };
let simulation = null, svg = null, g = null, selectedNode = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeGraph();
    initializeParticles();
    initializeEventListeners();
    loadData();
});

async function loadData() {
    try {
        const res = await fetch('data/network.json');
        const data = await res.json();
        graphData.nodes = data.nodes.map(n => ({
            ...n,
            id: n.id || n.name,
            societies: n.type === 'policy' ? ['Skull & Bones', 'Bilderberg'] : ['Skull & Bones']
        }));
        graphData.edges = data.edges.map(e => ({
            source: e.source,
            target: e.target,
            type: e.type || 'society-connection',
            weight: e.weight || 2
        }));
        filteredData = { nodes: [...graphData.nodes], edges: [...graphData.edges] };
        updateGraph();
        updateStatistics();
        document.getElementById('search-input').addEventListener('input', handleSearch);
    } catch (err) {
        console.error('Failed to load data:', err);
        document.body.innerHTML += '<div style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);color:#8B0000;font-size:1.2rem;">Failed to load data. Run: python3 web/build_data.py</div>';
    }
}

function handleSearch(e) {
    const q = e.target.value.toLowerCase().trim();
    if (!q) { filteredData = { nodes: [...graphData.nodes], edges: [...graphData.edges] }; updateGraph(); return; }
    const matches = graphData.nodes.filter(n => n.name.toLowerCase().includes(q));
    const ids = new Set(matches.map(m => m.id));
    filteredData.nodes = matches;
    filteredData.edges = graphData.edges.filter(ed => {
        const s = typeof ed.source === 'object' ? ed.source.id : ed.source;
        const t = typeof ed.target === 'object' ? ed.target.id : ed.target;
        return ids.has(s) && ids.has(t);
    });
    updateGraph();
}

function initializeGraph() {
    const container = document.getElementById('network-graph');
    const width = container.clientWidth, height = container.clientHeight;
    svg = d3.select('#network-graph').attr('width', width).attr('height', height);
    const zoom = d3.zoom().scaleExtent([0.1, 4]).on('zoom', e => g.attr('transform', e.transform));
    svg.call(zoom);
    g = svg.append('g');
    simulation = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id).distance(80))
        .force('charge', d3.forceManyBody().strength(-400))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(25));
}

function updateGraph() {
    g.selectAll('*').remove();
    if (filteredData.nodes.length === 0) return;

    const link = g.append('g').attr('class', 'links')
        .selectAll('line').data(filteredData.edges).enter().append('line')
        .attr('class', 'edge')
        .style('stroke', d => getEdgeColor(d.type))
        .style('stroke-width', d => (d.weight || 1) * 1.5)
        .style('stroke-opacity', 0.5);

    const node = g.append('g').attr('class', 'nodes')
        .selectAll('circle').data(filteredData.nodes).enter().append('circle')
        .attr('class', 'node').attr('r', d => getNodeSize(d))
        .style('fill', d => getNodeColor(d.type))
        .style('stroke', '#C5A572').style('stroke-width', 2)
        .style('filter', d => `drop-shadow(0 0 6px ${getNodeColor(d.type)})`)
        .call(drag(simulation))
        .on('click', (e, d) => { selectedNode = d; showNodeDetails(d); highlightNode(d); })
        .on('mouseenter', (e, d) => showTooltip(e, d))
        .on('mouseleave', () => hideTooltip());

    const label = g.append('g').attr('class', 'labels')
        .selectAll('text').data(filteredData.nodes).enter().append('text')
        .text(d => d.name).attr('font-size', 9).attr('font-family', "'EB Garamond', serif")
        .attr('fill', '#E8DCC4').attr('text-anchor', 'middle').attr('dy', -18)
        .style('pointer-events', 'none');

    simulation.nodes(filteredData.nodes);
    simulation.force('link').links(filteredData.edges);
    simulation.on('tick', () => {
        link.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        node.attr('cx', d => d.x).attr('cy', d => d.y);
        label.attr('x', d => d.x).attr('y', d => d.y);
    });
    simulation.alpha(1).restart();
}

function getNodeColor(type) {
    return { 'secret-society': '#660000', 'policy': '#8B7355' }[type] || '#C5A572';
}
function getEdgeColor(type) {
    return { 'society-connection': '#8B0000', 'policy-connection': '#8B7355' }[type] || '#8B7355';
}
function getNodeSize(node) {
    return Math.min(12 + (node.connections || 0) * 0.3, 28);
}

function drag(sim) {
    function dragstarted(e) { if (!e.active) sim.alphaTarget(0.3).restart(); e.subject.fx = e.subject.x; e.subject.fy = e.subject.y; }
    function dragged(e) { e.subject.fx = e.x; e.subject.fy = e.y; }
    function dragended(e) { if (!e.active) sim.alphaTarget(0); e.subject.fx = null; e.subject.fy = null; }
    return d3.drag().on('start', dragstarted).on('drag', dragged).on('end', dragended);
}

function showTooltip(e, node) {
    const t = document.getElementById('node-tooltip');
    let c = `<strong>${node.type}</strong><br>`;
    if (node.cohort_year) c += `Cohort: ${node.cohort_year}<br>`;
    if (node.position) c += node.position.substring(0, 80) + (node.position.length > 80 ? '…' : '') + '<br>';
    c += `Connections: ${node.connections || 0}`;
    t.querySelector('.tooltip-name').textContent = node.name;
    t.querySelector('.tooltip-type').textContent = node.type === 'policy' ? 'Skull & Bones + Bilderberg' : 'Skull & Bones';
    t.querySelector('.tooltip-content').innerHTML = c;
    t.style.left = (e.pageX + 15) + 'px'; t.style.top = (e.pageY + 15) + 'px';
    t.classList.remove('hidden');
}
function hideTooltip() { document.getElementById('node-tooltip').classList.add('hidden'); }

function showNodeDetails(node) {
    const panel = document.getElementById('details-panel');
    const content = document.getElementById('details-content');
    let html = `<h3 style="font-family:var(--font-header);color:var(--gold-leaf);margin-bottom:1rem">${node.name}</h3>`;
    html += `<div><strong>Type:</strong> ${node.type}<br>`;
    if (node.cohort_year) html += `<strong>Cohort:</strong> ${node.cohort_year}<br>`;
    if (node.position) html += `<strong>Position:</strong> ${node.position}<br>`;
    html += `<strong>Connections:</strong> ${node.connections || 0}</div>`;
    const conns = filteredData.edges.filter(e => e.source.id === node.id || e.target.id === node.id);
    html += `<div style="margin-top:1rem"><strong>Direct links:</strong> ${conns.slice(0, 8).map(c => {
        const o = c.source.id === node.id ? c.target : c.source;
        return o.name;
    }).join(', ')}${conns.length > 8 ? '…' : ''}</div>`;
    content.innerHTML = html;
    panel.classList.remove('hidden');
}

function highlightNode(node) {
    d3.selectAll('.node').style('opacity', 0.2).style('stroke-width', 2);
    d3.selectAll('.node').filter(d => d.id === node.id).style('opacity', 1).style('stroke', '#8B0000').style('stroke-width', 4).style('filter', 'drop-shadow(0 0 15px #8B0000)');
    const ids = new Set(filteredData.edges.filter(e => e.source.id === node.id || e.target.id === node.id).flatMap(e => [e.source.id, e.target.id]));
    d3.selectAll('.node').filter(d => ids.has(d.id)).style('opacity', 0.8).style('stroke', '#C5A572');
    d3.selectAll('.edge').style('opacity', 0.05);
    d3.selectAll('.edge').filter(e => e.source.id === node.id || e.target.id === node.id).style('opacity', 0.9).style('stroke-width', 3);
}

function initializeParticles() {
    const canvas = document.getElementById('particle-canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth; canvas.height = window.innerHeight;
    const symbols = ['☠', '👁', '🗝', '⚰', '🕯', '✦', '☥', '⛤', '⛧'];
    const particles = Array.from({ length: 25 }, () => ({
        x: Math.random() * canvas.width, y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.2, vy: (Math.random() - 0.5) * 0.2,
        symbol: symbols[Math.floor(Math.random() * symbols.length)],
        opacity: Math.random() * 0.15 + 0.03, size: Math.random() * 20 + 12
    }));
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            p.x += p.vx; p.y += p.vy;
            if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
            ctx.font = `${p.size}px serif`;
            ctx.fillStyle = `rgba(197, 165, 114, ${p.opacity})`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(p.symbol, p.x, p.y);
        });
        requestAnimationFrame(animate);
    }
    animate();
    window.addEventListener('resize', () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; });
}

function initializeEventListeners() {
    document.getElementById('close-details').onclick = () => { document.getElementById('details-panel').classList.add('hidden'); resetHighlight(); };
    document.getElementById('stats-toggle').onclick = () => { document.getElementById('stats-modal').classList.remove('hidden'); updateStatistics(); };
    document.getElementById('close-stats').onclick = () => document.getElementById('stats-modal').classList.add('hidden');
    document.getElementById('export-toggle').onclick = () => document.getElementById('export-modal').classList.remove('hidden');
    document.getElementById('close-export').onclick = () => document.getElementById('export-modal').classList.add('hidden');
    document.getElementById('help-toggle').onclick = () => document.getElementById('help-modal').classList.remove('hidden');
    document.getElementById('close-help').onclick = () => document.getElementById('help-modal').classList.add('hidden');
    document.getElementById('zoom-in').onclick = () => svg.transition().call(d3.zoom().scaleBy, 1.3);
    document.getElementById('zoom-out').onclick = () => svg.transition().call(d3.zoom().scaleBy, 0.7);
    document.getElementById('zoom-reset').onclick = () => svg.transition().call(d3.zoom().transform, d3.zoomIdentity);
    document.getElementById('apply-filters').onclick = applyFilters;
    document.getElementById('reset-filters').onclick = resetFilters;
    const start = document.getElementById('timeline-slider-start'), end = document.getElementById('timeline-slider-end');
    start.oninput = e => { document.getElementById('timeline-start').textContent = e.target.value; applyTimelineFilter(); };
    end.oninput = e => { document.getElementById('timeline-end').textContent = e.target.value; applyTimelineFilter(); };
    document.getElementById('export-json').onclick = () => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([JSON.stringify(filteredData, null, 2)], { type: 'application/json' }));
        a.download = 'hidden-networks.json';
        a.click();
    };
    document.querySelectorAll('.modal').forEach(m => m.onclick = e => { if (e.target === m) m.classList.add('hidden'); });
}

function applyFilters() {
    const types = Array.from(document.querySelectorAll('.filter-checkbox input:checked')).map(c => c.value);
    filteredData.nodes = graphData.nodes.filter(n => types.includes(n.type));
    const ids = new Set(filteredData.nodes.map(n => n.id));
    filteredData.edges = graphData.edges.filter(e => {
        const s = typeof e.source === 'object' ? e.source.id : e.source;
        const t = typeof e.target === 'object' ? e.target.id : e.target;
        return ids.has(s) && ids.has(t);
    });
    updateGraph();
    updateStatistics();
}
function resetFilters() {
    document.querySelectorAll('.filter-checkbox input').forEach(c => c.checked = true);
    filteredData = { nodes: [...graphData.nodes], edges: [...graphData.edges] };
    updateGraph();
    updateStatistics();
}
function applyTimelineFilter() {
    const start = +document.getElementById('timeline-slider-start').value;
    const end = +document.getElementById('timeline-slider-end').value;
    filteredData.nodes = graphData.nodes.filter(n => {
        const y = +(n.cohort_year || 1900);
        return y >= start && y <= end;
    });
    const ids = new Set(filteredData.nodes.map(n => n.id));
    filteredData.edges = graphData.edges.filter(e => {
        const s = typeof e.source === 'object' ? e.source.id : e.source;
        const t = typeof e.target === 'object' ? e.target.id : e.target;
        return ids.has(s) && ids.has(t);
    });
    updateGraph();
}

function resetHighlight() {
    d3.selectAll('.node').style('opacity', 1).style('stroke', '#C5A572').style('stroke-width', 2).style('filter', d => `drop-shadow(0 0 6px ${getNodeColor(d.type)})`);
    d3.selectAll('.edge').style('opacity', 0.5).style('stroke-width', d => (d.weight || 1) * 1.5).interrupt();
}

function updateStatistics() {
    document.getElementById('stat-nodes').textContent = filteredData.nodes.length;
    document.getElementById('stat-edges').textContent = filteredData.edges.length;
    const max = (filteredData.nodes.length * (filteredData.nodes.length - 1)) / 2;
    document.getElementById('stat-density').textContent = max ? ((filteredData.edges.length / max) * 100).toFixed(1) + '%' : '0%';
    const counts = {};
    filteredData.edges.forEach(e => { counts[e.source] = (counts[e.source] || 0) + 1; counts[e.target] = (counts[e.target] || 0) + 1; });
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 5);
    document.getElementById('top-nodes').innerHTML = top.map(([id, c]) => {
        const n = filteredData.nodes.find(x => x.id === id);
        return `<div style="padding:0.5rem;border-bottom:1px solid rgba(139,0,0,0.3)">${n?.name || id}: <strong>${c}</strong></div>`;
    }).join('') || '<div>No data</div>';
}
