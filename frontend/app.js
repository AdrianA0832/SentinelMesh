const API_URL = 'http://127.0.0.1:8000';

// Safety fetch wrapper
async function safeFetch(url, options = {}) {
    const timeout = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Timeout')), 5000)
    );
    try {
        const res = await Promise.race([fetch(url, options), timeout]);
        return res;
    } catch (e) {
        // Just rethrow, the caller handles UI or logic
        throw e;
    }
}

// State
let charts = { risk: null, conn: null };

// Init
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('save-env-btn').addEventListener('click', saveEnvironmentName);
    fetchData();
    setInterval(fetchData, 10000); // 10s poll
});

async function fetchData() {
    try {
        // Use Promise.all checking or just sequential - keeping sequential as per original structure,
        // but failures in one shouldn't crash all if possible, or maybe catch all?
        // User said: "If fetch fails: show text: 'Backend reachable but no data yet'"
        // If I limit the catch block:

        await fetchHealth();
        await fetchDevices();
        await fetchTimeline();
        await fetchHistory();
        await fetchEnvironment();

        // If we reach here, at least one success? 
        // Actually fetchHealth throws if safeFetch fails.

    } catch (e) {
        updateBanner("Backend reachable but no data yet", "warning"); // User requested specific text
        console.error(e);
        // Ensure no eternal loading state if any
    }
}

// 1. Health & Risk
async function fetchHealth() {
    const res = await safeFetch(`${API_URL}/`);
    const data = await res.json();

    // Header
    const mode = data.mode ? data.mode.toUpperCase() : "UNKNOWN";
    document.getElementById('env-mode').textContent = mode;

    // Status Dot
    // Status Logic
    const risk = data.risk_score;
    let color = '#22C55E';
    let statusText = 'System Normal';
    let bannerType = 'normal';

    if (risk > 50) {
        color = '#EF4444';
        statusText = 'Attention Required';
        bannerType = 'critical';
    } else if (risk > 0) {
        color = '#F59E0B';
        statusText = 'Minor Anomalies Detected';
        bannerType = 'warning';
    }

    // Update UI elements
    document.getElementById('sys-color').style.backgroundColor = color;
    document.getElementById('risk-score').textContent = risk;
    document.getElementById('risk-score').style.color = color;
    document.getElementById('risk-status').textContent = statusText;

    updateBanner(statusText, bannerType);

    // Risk Recs
    const recs = document.getElementById('recommendations');
    recs.innerHTML = '';
    if (data.explanations && data.explanations.risk) {
        let li = document.createElement('li');
        li.textContent = data.explanations.risk;
        recs.appendChild(li);
    }
}

// 2. Devices
async function fetchDevices() {
    const res = await safeFetch(`${API_URL}/devices`);
    const devices = await res.json();

    // Update count
    document.getElementById('count-devices').textContent = devices.length;

    // Table
    // Table Handling
    const table = document.getElementById('device-table');
    const container = table.parentElement;
    let msg = container.querySelector('.no-data-msg');

    if (devices.length === 0) {
        table.classList.add('hidden');
        if (!msg) {
            msg = document.createElement('div');
            msg.className = 'no-data-msg';
            msg.style.color = '#9CA3AF';
            msg.style.padding = '1rem';
            msg.style.fontFamily = 'monospace';
            msg.textContent = 'No local devices detected within scan window.';
            container.appendChild(msg);
        }
        msg.classList.remove('hidden');
    } else {
        table.classList.remove('hidden');
        if (msg) msg.classList.add('hidden');

        const tbody = table.querySelector('tbody');
        tbody.innerHTML = '';

        devices.slice(0, 10).forEach(d => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="text-mono">${d.ip}</td>
                <td class="text-mono">${d.mac}</td>
                <td>${d.mac_vendor || 'Unknown'}</td>
                <td><span class="status-badge ${d.status === 'active' ? '' : 'warning'}">${d.status}</span></td>
                <td class="text-mono" style="font-size: 0.75rem">${new Date(d.first_seen).toLocaleTimeString()}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    // Last Scan Card (using current time if success)
    document.getElementById('last-scan').textContent = new Date().toLocaleTimeString();
}

// 2.5 Environment
async function fetchEnvironment() {
    try {
        const res = await safeFetch(`${API_URL}/environment`);
        const env = await res.json();

        // Update Label
        const label = document.getElementById('env-mode');
        // If we have a name, show it. Else show "Unnamed"
        if (env.name) {
            label.textContent = env.name.toUpperCase();
            label.classList.add('text-green');
        } else {
            label.textContent = "UNNAMED ENVIRONMENT";
            label.classList.remove('text-green');
        }

        // Check user prompt
        const modal = document.getElementById('env-modal');
        if (env.needs_name && !localStorage.getItem('env_prompt_dismissed')) {
            modal.classList.remove('hidden');
        } else {
            modal.classList.add('hidden');
        }

    } catch (e) {
        console.error("Env fetch failed", e);
    }
}

async function saveEnvironmentName() {
    const input = document.getElementById('env-name-input');
    const name = input.value.trim();
    if (!name) return;

    try {
        const res = await safeFetch(`${API_URL}/environment/name`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });

        if (res.ok) {
            document.getElementById('env-modal').classList.add('hidden');
            fetchEnvironment(); // Refresh UI
            updateBanner(`Environment profile saved: ${name}`, "normal");
        }
    } catch (e) {
        console.error("Failed to save env name", e);
    }
}

// 3. Timeline
async function fetchTimeline() {
    const res = await safeFetch(`${API_URL}/timeline?source=audit`); // Get all? Timeline endpoint does filtering
    // Actually main.py endpoint takes ?source param but default is None (all).
    // Let's verify backend... yes, calling without param gets all but limit 100.

    const resAll = await safeFetch(`${API_URL}/timeline`); // Get unified
    const events = await resAll.json();

    const container = document.getElementById('timeline-feed');
    container.innerHTML = '';

    if (events.length === 0) {
        container.innerHTML = '<div style="color: #9CA3AF; padding: 0.5rem 0;">No events logged recently.</div>';
    } else {
        events.slice(0, 6).forEach(e => {
            const div = document.createElement('div');
            div.className = 'timeline-item';
            // Parse time
            const time = new Date(e.timestamp).toLocaleTimeString();
            div.innerHTML = `
                <span class="timeline-time">${time}</span>
                <span class="timeline-source">[${e.source.toUpperCase()}]</span>
                <span class="timeline-msg">${e.message}</span>
            `;
            container.appendChild(div);
        });
    }
}

// 4. History (CSV Parsing for Charts)
async function fetchHistory() {
    const res = await safeFetch(`${API_URL}/export/history`);
    if (!res.ok) return;

    const text = await res.text();
    const rows = text.trim().split('\n').slice(1); // skip header
    const data = rows.map(r => {
        const cols = r.split(',');
        return {
            time: cols[0],
            total: parseInt(cols[1]),
            dns: parseInt(cols[2]),
            risk: parseInt(cols[3])
        };
    }).slice(-20); // Last 20 points

    updateCharts(data);
}

function updateCharts(data) {
    if (!window.Chart) return;

    if (!data || data.length === 0) {
        if (charts.risk) charts.risk.destroy();
        if (charts.conn) charts.conn.destroy();
        document.getElementById('riskChart').style.display = 'none';
        document.getElementById('connChart').style.display = 'none';
        return;
    }

    const labels = data.map(d => new Date(d.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));

    // Risk Chart
    const ctxRisk = document.getElementById('riskChart');
    if (ctxRisk) {
        ctxRisk.style.display = 'block';
        if (charts.risk) charts.risk.destroy();
        charts.risk = new Chart(ctxRisk, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Risk Score',
                    data: data.map(d => d.risk),
                    borderColor: '#F59E0B',
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: getChartOptions()
        });
    }

    // Conn Chart
    const ctxConn = document.getElementById('connChart');
    if (ctxConn) {
        ctxConn.style.display = 'block';
        if (charts.conn) charts.conn.destroy();
        charts.conn = new Chart(ctxConn, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Valid Connections',
                    data: data.map(d => d.total),
                    backgroundColor: '#1F2933',
                    borderColor: '#22C55E',
                    borderWidth: 1
                }]
            },
            options: getChartOptions()
        });
    }
}

function getChartOptions() {
    return {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
            x: { display: false },
            y: {
                grid: { color: '#1F2933' },
                ticks: { color: '#6B7280' }
            }
        },
        animation: false
    };
}

function updateBanner(msg, type = "normal") {
    const b = document.getElementById('status-banner');
    b.textContent = `> ${msg}`;
    b.className = `banner ${type}`;
}
