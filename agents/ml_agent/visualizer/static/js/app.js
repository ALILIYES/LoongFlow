const state = {
    runs: [],
    currentRunId: null,
    currentRun: null,
    currentStageId: null,
    currentStage: null,
    currentIteration: null,
    autoRefresh: true,
    refreshTimer: null
};

const ICONS = {
    chart: '\u{1F4CA}',
    download: '\u{2B07}',
    scissors: '\u{2702}',
    filter: '\u{2699}',
    cpu: '\u{1F5A5}',
    layers: '\u{1F3AC}',
    play: '\u{25B6}'
};

// ==================== API ====================
async function fetchJSON(url) {
    const r = await fetch(url);
    return r.json();
}

async function loadRuns() {
    try {
        const data = await fetchJSON('/api/runs');
        if (data.success) {
            state.runs = data.runs;
            renderRunList();
        }
    } catch (e) { console.error(e); }
}

async function loadRun(runId) {
    try {
        const data = await fetchJSON('/api/runs/' + runId);
        if (data.success) {
            state.currentRun = data.run;
            state.currentRunId = runId;
            state.currentStageId = null;
            state.currentStage = null;
            state.currentIteration = null;
            renderRunDetail();
        }
    } catch (e) { console.error(e); }
}

async function loadStage(stageId) {
    if (!state.currentRunId) return;
    try {
        const data = await fetchJSON('/api/runs/' + state.currentRunId + '/stages/' + stageId);
        if (data.success) {
            state.currentStage = data.stage;
            state.currentStageId = stageId;
            renderStageDetail();
        }
    } catch (e) { console.error(e); }
}

async function loadPlan() {
    if (!state.currentRunId) return;
    try {
        const data = await fetchJSON('/api/runs/' + state.currentRunId + '/plan');
        if (data.success) {
            renderPlan(data.plan);
        }
    } catch (e) { console.error(e); }
}

async function loadFile(iterNum, stageId, evalId, filename) {
    if (!state.currentRunId) return;
    try {
        const data = await fetchJSON(
            '/api/runs/' + state.currentRunId + '/iterations/' + iterNum +
            '/stages/' + stageId + '/evals/' + evalId + '/files/' + encodeURIComponent(filename)
        );
        if (data.success) {
            renderFileContent(data.file);
        }
    } catch (e) { console.error(e); }
}

// ==================== Render ====================
function renderRunList() {
    const el = document.getElementById('runList');
    if (!state.runs.length) {
        el.innerHTML = '<div class="empty-state">No ML runs found</div>';
        return;
    }
    el.innerHTML = state.runs.map(r => {
        const active = r.run_id === state.currentRunId ? ' active' : '';
        const shortId = r.run_id.substring(0, 8);
        const progress = r.completed_stages ? r.completed_stages.length + '/7 stages' : '';
        return '<div class="run-item' + active + '" onclick="selectRun(\'' + r.run_id + '\')">' +
            '<div class="run-name">' + shortId + '</div>' +
            '<div class="run-meta">Iter ' + r.current_iteration + ' &middot; ' + progress + '</div>' +
            '</div>';
    }).join('');
}

function selectRun(runId) {
    loadRun(runId);
}

function renderRunDetail() {
    const r = state.currentRun;
    const stages = r.stages || [];
    const iter = r.iterations || [];

    let html = '';

    // Pipeline
    html += '<div class="pipeline">';
    stages.forEach(s => {
        let cls = '';
        if (s.status === 'completed') cls = 'completed';
        else if (s.status === 'in_progress') cls = 'in_progress';
        else if (s.status === 'failed') cls = 'failed';
        html += '<div class="stage-node ' + cls + '" onclick="selectStage(\'' + s.id + '\')" title="' + s.label + ': ' + s.total_successes + '/' + s.total_attempts + ' attempts passed">' +
            '<span class="stage-icon">' + (ICONS[s.icon] || '') + '</span>' +
            s.label +
            (s.total_attempts > 0 ? ' <span style="opacity:0.7;margin-left:4px">' + s.total_successes + '/' + s.total_attempts + '</span>' : '') +
            '</div>';
    });
    html += '</div>';

    // Stats
    html += '<div class="section">' +
        '<div class="section-body"><div class="stats-grid">' +
        '<div class="stat-card"><div class="stat-label">Current Iteration</div><div class="stat-value info">' + (iter.length || 0) + '</div></div>' +
        '<div class="stat-card"><div class="stat-label">Completed Stages</div><div class="stat-value success">' + stages.filter(s => s.status === 'completed').length + ' / ' + stages.length + '</div></div>' +
        '<div class="stat-card"><div class="stat-label">Total Eval Attempts</div><div class="stat-value">' + stages.reduce((a, s) => a + s.total_attempts, 0) + '</div></div>' +
        '<div class="stat-card"><div class="stat-label">Success Rate</div><div class="stat-value">' +
            (stages.reduce((a, s) => a + s.total_attempts, 0) > 0
                ? Math.round(stages.reduce((a, s) => a + s.total_successes, 0) / Math.max(1, stages.reduce((a, s) => a + s.total_attempts, 0)) * 100) + '%'
                : '-') +
        '</div></div>' +
        '</div></div></div>';

    // Stage detail (if one selected)
    if (state.currentStageId && state.currentStage) {
        html += renderEvalTable(state.currentStage);
    }

    // Iterations overview
    if (iter.length) {
        html += '<div class="section"><div class="section-header" onclick="this.parentElement.querySelector(\'.section-body\').classList.toggle(\'hide\')">Iterations</div>' +
            '<div class="section-body"><table class="eval-table"><thead><tr><th>Iter</th>' +
            stages.map(s => '<th>' + s.label + '</th>').join('') +
            '</tr></thead><tbody>';
        iter.forEach(it => {
            html += '<tr><td>' + it.iteration + '</td>';
            stages.forEach(s => {
                const ss = (it.stages || {})[s.id];
                if (ss && ss.total_attempts > 0) {
                    const color = ss.successes > 0 ? 'var(--success)' : (ss.failures > 0 ? 'var(--danger)' : 'var(--text-secondary)');
                    html += '<td style="color:' + color + '">' + ss.successes + '/' + ss.total_attempts + '</td>';
                } else {
                    html += '<td style="color:var(--text-secondary)">-</td>';
                }
            });
            html += '</tr>';
        });
        html += '</tbody></table></div></div>';
    }

    // Logs
    if (r.logs && r.logs.length) {
        html += '<div class="section"><div class="section-header" onclick="this.parentElement.querySelector(\'.section-body\').classList.toggle(\'hide\')">Live Logs (last 200 lines)</div>' +
            '<div class="section-body"><div class="log-viewer" id="logViewer">' +
            r.logs.map(l => formatLogLine(l)).join('\n') +
            '</div></div></div>';
    }

    // Plan button
    html += '<div style="margin-top:16px"><button class="btn" onclick="loadPlan()">View Strategic Plan</button></div>';

    document.getElementById('content').innerHTML = html;

    // Scroll logs to bottom
    const logEl = document.getElementById('logViewer');
    if (logEl) logEl.scrollTop = logEl.scrollHeight;

    // Re-render sidebar
    renderRunList();
}

function formatLogLine(line) {
    const lower = line.toLowerCase();
    let cls = 'info';
    if (lower.includes('error') || lower.includes('traceback') || lower.includes('fail')) cls = 'error';
    else if (lower.includes('warn')) cls = 'warn';
    else if (lower.includes('success') || lower.includes('passed')) cls = 'success';
    return '<div class="log-line ' + cls + '">' + escapeHtml(line) + '</div>';
}

function renderEvalTable(stage) {
    if (!stage.evals || !stage.evals.length) {
        return '<div class="section"><div class="section-header">' + stage.stage_label + ' Evaluations</div>' +
            '<div class="section-body"><div class="empty-state">No evaluation results yet</div></div></div>';
    }
    let html = '<div class="section"><div class="section-header">' + stage.stage_label + ' Evaluations (' + stage.evals.length + ')</div>' +
        '<div class="section-body"><table class="eval-table"><thead><tr>' +
        '<th>Iter</th><th>Eval ID</th><th>Status</th><th>Score</th><th>Summary</th><th>Files</th>' +
        '</tr></thead><tbody>';
    stage.evals.forEach(ev => {
        const badgeCls = ev.status === 'success' ? 'badge-success' : 'badge-fail';
        const evalShort = ev.eval_id ? ev.eval_id.substring(5, 13) : '';
        html += '<tr>' +
            '<td>' + ev.iteration + '</td>' +
            '<td style="font-family:monospace;font-size:11px">' + evalShort + '</td>' +
            '<td><span class="badge ' + badgeCls + '">' + (ev.status || '?') + '</span></td>' +
            '<td>' + (ev.score !== null && ev.score !== undefined ? ev.score.toFixed(4) : '-') + '</td>' +
            '<td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + escapeHtml(ev.summary || '') + '</td>' +
            '<td>' + (ev.files || []).map(f => '<a href="#" onclick="event.preventDefault();loadFile(' + ev.iteration + ',\'' + stage.stage_id + '\',\'' + ev.eval_id + '\',\'' + f + '\');return false" style="color:var(--primary);font-size:11px;margin-right:6px">' + f + '</a>').join('') + '</td>' +
            '</tr>';
    });
    html += '</tbody></table></div></div>';
    return html;
}

function selectStage(stageId) {
    state.currentStageId = stageId;
    loadStage(stageId);
}

function renderStageDetail() {
    // Re-render run detail with stage table
    renderRunDetail();
    // Scroll to stage section
    setTimeout(() => {
        const el = document.querySelector('.eval-table');
        if (el) el.scrollIntoView({ behavior: 'smooth' });
    }, 100);
}

function renderFileContent(file) {
    const langLabel = file.language === 'python' ? 'Python' : (file.language === 'log' ? 'Log' : file.language.toUpperCase());
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);z-index:1000;display:flex;align-items:center;justify-content:center';
    overlay.onclick = function(e) { if (e.target === overlay) overlay.remove(); };
    overlay.innerHTML = '<div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);width:80vw;max-width:1000px;max-height:80vh;display:flex;flex-direction:column">' +
        '<div style="padding:10px 14px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center">' +
        '<span style="font-weight:600;font-size:12px">' + escapeHtml(file.filename) + ' <span style="color:var(--text-secondary);font-weight:400">(' + langLabel + ')</span></span>' +
        '<button class="btn" onclick="this.closest(\'div[style*=fixed]\').remove()" style="font-size:16px;line-height:1">&times;</button>' +
        '</div>' +
        '<div class="code-block" style="flex:1">' + escapeHtml(file.content) + '</div>' +
        '</div>';
    document.body.appendChild(overlay);
}

function renderPlan(plan) {
    let html = '<div class="section"><div class="section-header">Strategic Plan</div><div class="section-body">';
    if (plan.strategic_analysis) {
        html += '<div class="plan-text">' + escapeHtml(plan.strategic_analysis) + '</div>';
    }
    html += '</div></div>';

    if (plan.stages && Object.keys(plan.stages).length) {
        html += '<div class="section"><div class="section-header">Per-Stage Plans</div><div class="section-body">';
        Object.entries(plan.stages).forEach(([stageId, planText]) => {
            html += '<div style="margin-bottom:16px">';
            html += '<div style="font-weight:600;font-size:12px;margin-bottom:6px;color:var(--primary)">' + stageId + '</div>';
            html += '<div class="plan-text">' + escapeHtml(planText || '') + '</div>';
            html += '</div>';
        });
        html += '</div></div>';
    }

    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);z-index:1000;display:flex;align-items:center;justify-content:center';
    overlay.onclick = function(e) { if (e.target === overlay) overlay.remove(); };
    overlay.innerHTML = '<div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);width:85vw;max-width:1100px;max-height:85vh;overflow-y:auto">' +
        '<div style="padding:10px 14px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;background:var(--surface)">' +
        '<span style="font-weight:600;font-size:13px">Strategic Plan</span>' +
        '<button class="btn" onclick="this.closest(\'div[style*=fixed]\').remove()" style="font-size:16px;line-height:1">&times;</button>' +
        '</div>' +
        '<div style="padding:16px">' + html + '</div>' +
        '</div>';
    document.body.appendChild(overlay);
}

function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ==================== Auto-refresh ====================
function toggleAutoRefresh() {
    state.autoRefresh = !state.autoRefresh;
    const btn = document.getElementById('autoRefreshBtn');
    const label = document.getElementById('autoRefreshLabel');
    if (state.autoRefresh) {
        btn.textContent = 'Pause';
        label.textContent = 'Auto: ON (10s)';
        startAutoRefresh();
    } else {
        btn.textContent = 'Resume';
        label.textContent = 'Auto: OFF';
        stopAutoRefresh();
    }
}

function startAutoRefresh() {
    stopAutoRefresh();
    state.refreshTimer = setInterval(() => {
        if (state.currentRunId) {
            loadRun(state.currentRunId);
            if (state.currentStageId) {
                loadStage(state.currentStageId);
            }
        } else {
            loadRuns();
        }
    }, 10000);
}

function stopAutoRefresh() {
    if (state.refreshTimer) {
        clearInterval(state.refreshTimer);
        state.refreshTimer = null;
    }
}

// ==================== Init ====================
document.getElementById('refreshBtn').addEventListener('click', () => {
    if (state.currentRunId) loadRun(state.currentRunId);
    else loadRuns();
});
document.getElementById('autoRefreshBtn').addEventListener('click', toggleAutoRefresh);

loadRuns();
startAutoRefresh();
