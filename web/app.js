/* The Hidden Networks - All elite networks */
let allData = { nodes: [], edges: [] };
let filtered = { nodes: [], edges: [] };
let sim = null, svg = null, g = null;

document.addEventListener('DOMContentLoaded', () => {
    initGraph();
    loadData();
    initEvents();
});

async function loadData() {
    try {
        const r = await fetch('data/network.json');
        const d = await r.json();
        allData.nodes = (d.nodes || []).map(n => ({
            ...n,
            id: n.id || n.name,
            orgs: n.orgs || [],
            type: n.type || 'unknown',
        }));
        allData.edges = (d.edges || []).map(e => ({
            source: e.source,
            target: e.target,
            type: e.type || 'connection',
            weight: e.weight || 1,
        }));
        applyFilters();
        document.getElementById('search').addEventListener('input', onSearch);
    } catch (err) {
        console.error(err);
        document.getElementById('detail').innerHTML = '<p style="color:#8B0000">Failed to load. Run: python3 web/build_data.py</p>';
    }
}

function nodeMatchesOrg(node, org) {
    const o = (node.orgs || []).map(x => String(x).toLowerCase());
    if (org === 'skull') return o.some(x => x.includes('skull') || x.includes('bones'));
    if (org === 'bilderberg') return o.some(x => x.includes('bilderberg'));
    if (org === 'trilateral') return o.some(x => x.includes('trilateral'));
    if (org === 'cross-ref') return node.type === 'cross-ref' || o.some(x => x.includes('cross'));
    return false;
}

function applyFilters() {
    const orgs = Array.from(document.querySelectorAll('input[name="org"]:checked')).map(c => c.value);
    const start = +document.querySelector('.era-btn.active')?.dataset.start || 1833;
    const end = +document.querySelector('.era-btn.active')?.dataset.end || 1982;
    const q = document.getElementById('search').value.toLowerCase().trim();

    let nodes = allData.nodes.filter(n => {
        if (!orgs.some(org => nodeMatchesOrg(n, org))) return false;
        const y = +(n.cohort_year || n.year || 1900);
        if (y && (y < start || y > end)) return false;
        if (q && !String(n.name || '').toLowerCase().includes(q)) return false;
        return true;
    });

    const ids = new Set(nodes.map(n => n.id));
    let edges = allData.edges.filter(e => {
        const s = typeof e.source === 'object' ? e.source.id : e.source;
        const t = typeof e.target === 'object' ? e.target.id : e.target;
        return ids.has(s) && ids.has(t);
    });

    filtered = { nodes, edges };
    updateGraph();
}

function onSearch() {
    applyFilters();
    const q = document.getElementById('search').value.toLowerCase().trim();
    if (q && filtered.nodes.length === 1) {
        showDetail(filtered.nodes[0]);
        highlight(filtered.nodes[0]);
    } else if (filtered.nodes.length === 0 && q) {
        document.getElementById('detail').innerHTML = '<p>No matches.</p>';
    } else {
        document.getElementById('detail').innerHTML = '<p class="detail-placeholder">Click a node or search to view details</p>';
    }
}

function initGraph() {
    const wrap = document.querySelector('.graph-wrapper');
    const w = wrap.clientWidth, h = wrap.clientHeight;
    svg = d3.select('#graph').attr('width', w).attr('height', h);
    svg.call(d3.zoom().scaleExtent([0.15, 4]).on('zoom', e => g.attr('transform', e.transform)));
    g = svg.append('g');
    sim = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id).distance(60))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(w / 2, h / 2))
        .force('collision', d3.forceCollide().radius(18));
    window.addEventListener('resize', () => {
        const W = wrap.clientWidth, H = wrap.clientHeight;
        svg.attr('width', W).attr('height', H);
        sim.force('center', d3.forceCenter(W / 2, H / 2));
        sim.alpha(0.2).restart();
    });
}

function nodeColor(n) {
    if (n.type === 'cross-ref') return '#E63946';
    if ((n.orgs || []).some(x => String(x).includes('Bilderberg')) && (n.orgs || []).some(x => String(x).includes('Skull'))) return '#FFD60A';
    if ((n.orgs || []).some(x => String(x).includes('Skull') || String(x).includes('Bones'))) return '#FFFFFF';
    if ((n.orgs || []).some(x => String(x).includes('Trilateral'))) return '#FF6B35';
    return '#888888';
}

function edgeColor(e) {
    const t = e.type || '';
    if (t.includes('skull') || t.includes('cohort')) return '#FFFFFF';
    if (t.includes('bilderberg')) return '#FFD60A';
    if (t.includes('trilateral')) return '#FF6B35';
    return '#666666';
}

function updateGraph() {
    g.selectAll('*').remove();
    if (filtered.nodes.length === 0) return;

    const link = g.append('g').selectAll('line').data(filtered.edges).enter().append('line')
        .attr('class', 'edge')
        .style('stroke', edgeColor)
        .style('stroke-width', d => (d.weight || 1))
        .style('stroke-opacity', 0.4);

    const node = g.append('g').selectAll('circle').data(filtered.nodes).enter().append('circle')
        .attr('class', 'node')
        .attr('r', d => Math.min(6 + (d.connections || 0) * 0.15, 20))
        .style('fill', nodeColor)
        .style('stroke', 'rgba(255,255,255,0.3)')
        .style('stroke-width', 1)
        .call(d3.drag()
            .on('start', e => { if (!e.active) sim.alphaTarget(0.3).restart(); e.subject.fx = e.subject.x; e.subject.fy = e.subject.y; })
            .on('drag', e => { e.subject.fx = e.x; e.subject.fy = e.y; })
            .on('end', e => { if (!e.active) sim.alphaTarget(0); e.subject.fx = null; e.subject.fy = null; }))
        .on('click', (e, d) => { showDetail(d); highlight(d); })
        .on('mouseenter', showTooltip)
        .on('mouseleave', hideTooltip);

    sim.nodes(filtered.nodes);
    sim.force('link').links(filtered.edges);
    sim.on('tick', () => {
        link.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        node.attr('cx', d => d.x).attr('cy', d => d.y);
    });
    sim.alpha(1).restart();
}

function showTooltip(e, d) {
    const t = document.getElementById('tooltip');
    const wrap = document.querySelector('.graph-wrapper');
    const r = wrap.getBoundingClientRect();
    t.innerHTML = `<strong>${d.name}</strong><br>${(d.orgs || []).join(', ')}${d.cohort_year ? ' · ' + d.cohort_year : ''}`;
    t.style.left = (e.clientX - r.left + 12) + 'px';
    t.style.top = (e.clientY - r.top + 12) + 'px';
    t.classList.remove('hidden');
}
function hideTooltip() {
    document.getElementById('tooltip').classList.add('hidden');
}

function showDetail(d) {
    const el = document.getElementById('detail');
    let html = `<h3>${d.name}</h3>`;
    html += `<p><strong>Organizations:</strong> ${(d.orgs || []).join(', ') || '—'}</p>`;
    if (d.cohort_year) html += `<p><strong>Cohort:</strong> ${d.cohort_year}</p>`;
    if (d.position) html += `<p><strong>Notable:</strong> ${d.position}</p>`;
    html += `<p><strong>Connections:</strong> ${d.connections || 0}</p>`;
    const conns = filtered.edges.filter(e => (e.source?.id || e.source) === d.id || (e.target?.id || e.target) === d.id);
    const others = conns.slice(0, 8).map(c => {
        const o = (c.source?.id || c.source) === d.id ? (c.target?.name || c.target) : (c.source?.name || c.source);
        return o;
    });
    if (others.length) html += `<p><strong>Linked:</strong> ${others.join(', ')}${conns.length > 8 ? '…' : ''}</p>`;
    el.innerHTML = html;
}

function highlight(d) {
    d3.selectAll('.node').style('opacity', 0.2).style('stroke-width', 1);
    d3.selectAll('.node').filter(n => n.id === d.id).style('opacity', 1).style('stroke-width', 3);
    const ids = new Set(filtered.edges.filter(e => (e.source?.id || e.source) === d.id || (e.target?.id || e.target) === d.id).flatMap(e => [e.source?.id || e.source, e.target?.id || e.target]));
    d3.selectAll('.node').filter(n => ids.has(n.id)).style('opacity', 0.9).style('stroke-width', 2);
    d3.selectAll('.edge').style('opacity', 0.05);
    d3.selectAll('.edge').filter(e => (e.source?.id || e.source) === d.id || (e.target?.id || e.target) === d.id).style('opacity', 0.8);
}

function initEvents() {
    document.querySelectorAll('input[name="org"]').forEach(cb => {
        cb.onchange = () => applyFilters();
    });
    document.querySelectorAll('.era-btn').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('.era-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('search').value = '';
            applyFilters();
            document.getElementById('detail').innerHTML = '<p class="detail-placeholder">Click a node or search to view details</p>';
        };
    });
}
