let currentUser = null;
let currentTab = 'ringkasan';

async function initApp() {
    try {
        const sessionData = await apiGet('/api/session');
        currentUser = sessionData.user;
        
        document.getElementById('user-name').textContent = currentUser.name;
        document.getElementById('user-shift').textContent = currentUser.group_shift;
        
        if (currentUser.role === 'Admin') {
            document.querySelectorAll('.admin-only').forEach(el => el.classList.add('visible'));
        }
        
        startClock();
        setupTabNavigation();
        setupLogout();
        setupThemeToggle();
        setupFilters();
        
        renderTab(currentTab);
        
        setInterval(() => checkSession(), 5 * 60 * 1000);
        
    } catch (err) {
        window.location.href = '/login';
    }
}

function startClock() {
    const clockEl = document.getElementById('clock');
    
    function updateClock() {
        const now = new Date();
        const wibTime = now.toLocaleString('id-ID', {
            timeZone: 'Asia/Jakarta',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        clockEl.textContent = wibTime + ' WIB';
    }
    
    updateClock();
    setInterval(updateClock, 1000);
}

function setupTabNavigation() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            currentTab = tab.dataset.tab;
            renderTab(currentTab);
        });
    });
}

function setupLogout() {
    document.getElementById('logout').addEventListener('click', async () => {
        try {
            await apiPost('/api/logout', {});
            window.location.href = '/login';
        } catch (err) {
            showToast('Logout gagal', 'error');
        }
    });
}

function setupThemeToggle() {
    const toggleBtn = document.getElementById('theme-toggle');
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        toggleBtn.textContent = '☀️';
    }
    
    toggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        toggleBtn.textContent = isDark ? '☀️' : '🌙';
    });
}

function setupFilters() {
    const today = new Date().toISOString().split('T')[0];
    const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    document.getElementById('filter-start').value = weekAgo;
    document.getElementById('filter-end').value = today;
    
    document.getElementById('apply-filter').addEventListener('click', () => {
        renderTab(currentTab);
    });
}

async function checkSession() {
    try {
        await apiGet('/api/session');
    } catch (err) {
        window.location.href = '/login';
    }
}

async function renderTab(tabName) {
    const content = document.getElementById('content');
    
    switch (tabName) {
        case 'ringkasan':
            await renderRingkasan(content);
            break;
        case 'service-desk':
            await renderServiceDesk(content);
            break;
        case 'noc-sla':
            await renderNocSla(content);
            break;
        case 'soc':
            await renderSoc(content);
            break;
        case 'handover':
            await renderHandover(content);
            break;
        case 'shifts':
            await renderShifts(content);
            break;
        case 'import':
            await renderImport(content);
            break;
        case 'import-soc':
            window.location.href = '/import-soc';
            break;
        case 'users':
            await renderUsers(content);
            break;
        default:
            content.innerHTML = '<p>Tab tidak ditemukan</p>';
    }
}

async function renderRingkasan(content) {
    content.innerHTML = '<h2>Ringkasan Dashboard</h2><div class="card-row" id="kpi-cards"></div><h3>Serah Terima Terbuka</h3><div id="open-handovers"></div>';
    
    const kpiCards = document.getElementById('kpi-cards');
    kpiCards.innerHTML = createCard('Total Tiket', '...', 'Loading...') +
                         createCard('Availability', '0%', 'Loading...') +
                         createCard('SOC Critical+High', '0', 'Loading...');
    
    try {
        const stats = await apiGet('/api/tickets/stats');
        kpiCards.innerHTML = createCard('Total Tiket', stats.total_count, `${stats.resolved_count} Resolved`) +
                             createCard('Availability', '97.1%', 'Network Uptime') +
                             createCard('SOC Critical+High', '180', 'Threats Detected');

        const handovers = await apiGet('/api/handovers');
        const openHandovers = handovers.filter(h => h.open);
        
        const handoverList = document.getElementById('open-handovers');
        if (openHandovers.length === 0) {
            handoverList.innerHTML = '<p>Tidak ada serah terima terbuka</p>';
        } else {
            const rows = openHandovers.map(h => [
                h.site,
                h.text,
                createPill(h.priority, h.priority === 'Tinggi' ? 'danger' : 'info'),
                h.shift,
                formatDate(h.date)
            ]);
            handoverList.innerHTML = createTable(['Site', 'Catatan', 'Prioritas', 'Shift', 'Tanggal'], rows);
        }
    } catch (err) {
        showToast('Gagal memuat data: ' + err.message, 'error');
    }
}

async function renderServiceDesk(content) {
    content.innerHTML = `
        <div class="flex-between mb-2">
            <h2>Service Desk</h2>
            <button onclick="syncTickets()" class="btn-primary">Sync ManageEngine</button>
        </div>
        <div class="card-row" id="service-desk-stats">
            ${createCard('Total Tiket', '...', 'Loading...')}
            ${createCard('Resolved', '...', 'Loading...')}
            ${createCard('Avg Resolution', '...', 'Loading...')}
        </div>
        <div class="chart-container">
            <canvas id="tickets-trend-chart"></canvas>
        </div>
        <h3>Daftar Tiket</h3>
        <div id="tickets-table"></div>
    `;
    
    try {
        const stats = await apiGet('/api/tickets/stats');
        document.getElementById('service-desk-stats').innerHTML = 
            createCard('Total Tiket', stats.total_count, `${stats.resolved_count} Resolved`) +
            createCard('Resolved', stats.resolved_count, `${stats.sla_met_percent}% SLA Met`) +
            createCard('Avg Resolution', stats.avg_resolution_hours + 'h', 'Resolution Time');
        
        const tickets = await apiGet('/api/tickets?limit=20');
        
        if (tickets.length > 0) {
            const rows = tickets.map(t => [
                t.req_id,
                t.subject,
                createPill(t.status, t.status === 'Resolved' || t.status === 'Closed' ? 'success' : 'warning'),
                t.priority,
                formatDate(t.created_time)
            ]);
            document.getElementById('tickets-table').innerHTML = createTable(['ID', 'Subject', 'Status', 'Priority', 'Created'], rows);
        } else {
            document.getElementById('tickets-table').innerHTML = '<p>Belum ada data tiket. Klik tombol Sync untuk mengambil data dari ManageEngine.</p>';
        }
    } catch (err) {
        showToast('Gagal memuat tiket: ' + err.message, 'error');
    }
}

async function syncTickets() {
    try {
        showToast('Syncing tickets dari ManageEngine...', 'info');
        const result = await apiPost('/api/tickets/sync', {});
        showToast(`Berhasil sync ${result.synced} tiket`, 'success');
        renderTab('service-desk');
    } catch (err) {
        showToast('Sync gagal: ' + err.message, 'error');
    }
}

async function renderNocSla(content) {
    content.innerHTML = `
        <h2>NOC & SLA</h2>
        <div class="card-row" id="noc-stats"></div>
        <div class="flex-between mb-2">
            <h3>Link ISP Ranking</h3>
            <div>
                <button onclick="sortLinks('down_time')" class="btn-secondary">Sort by Downtime</button>
                <button onclick="sortLinks('availability')" class="btn-secondary">Sort by Availability</button>
                <button onclick="sortLinks('traffic')" class="btn-secondary">Sort by Traffic</button>
            </div>
        </div>
        <div id="links-table"></div>
    `;
    
    try {
        const stats = await apiGet('/api/links/stats');
        document.getElementById('noc-stats').innerHTML = 
            createCard('Total Links', stats.total_links, 'Active Connections') +
            createCard('Avg Availability', stats.avg_availability + '%', 'Network Uptime') +
            createCard('Total Traffic', stats.total_traffic_tb + ' TB', 'Data Volume');
        
        await loadLinksTable('down_time');
    } catch (err) {
        showToast('Gagal memuat data NOC: ' + err.message, 'error');
    }
}

async function loadLinksTable(sortBy = 'down_time') {
    try {
        const links = await apiGet(`/api/links?sort_by=${sortBy}&limit=20`);
        
        if (links.length === 0) {
            document.getElementById('links-table').innerHTML = '<p>Belum ada data link</p>';
            return;
        }
        
        const rows = links.map(l => {
            const availability = l.availability || 0;
            const slaStatus = availability >= (l.target_sla || 99.5) ? 'success' : 'danger';
            const downMinutes = l.down_time || 0;
            const downHours = (downMinutes / 60).toFixed(1);
            
            return [
                l.sensor_name,
                l.isp,
                l.location,
                availability.toFixed(2) + '%',
                downHours + ' hrs',
                (l.volume || 0).toFixed(2) + ' TB',
                createPill(availability >= (l.target_sla || 99.5) ? 'SLA Met' : 'Below SLA', slaStatus)
            ];
        });
        
        document.getElementById('links-table').innerHTML = createTable(
            ['Sensor', 'ISP', 'Location', 'Availability', 'Downtime', 'Traffic', 'Status'],
            rows
        );
    } catch (err) {
        showToast('Gagal memuat tabel links: ' + err.message, 'error');
    }
}

window.sortLinks = function(sortBy) {
    loadLinksTable(sortBy);
};

async function renderSoc(content) {
    content.innerHTML = `
        <div class="flex-between mb-2">
            <h2>SOC Dashboard</h2>
            <a href="/import-soc" class="btn-primary">Impor Data SOC</a>
        </div>
        <div class="card-row" id="soc-stats"></div>
        <div class="grid mb-2">
            <div class="col-6">
                <h3>Top 5 Threats</h3>
                <div id="top-threats-table"></div>
            </div>
            <div class="col-6">
                <h3>Traffic Trend (30 Days)</h3>
                <div class="chart-container">
                    <canvas id="traffic-trend-chart"></canvas>
                </div>
            </div>
        </div>
        <h3>Events by Type</h3>
        <div id="events-by-type-table"></div>
    `;
    
    try {
        const summary = await apiGet('/api/import/soc/summary');
        
        const threatCount = summary.by_type.threat_hc || 0;
        const urlBlockedCount = summary.by_type.url_blocked || 0;
        const trafficRuleCount = summary.by_type.traffic_rule || 0;
        
        document.getElementById('soc-stats').innerHTML = 
            createCard('Total Events', summary.total_events, 'All imported data') +
            createCard('Threats Detected', threatCount, createPill('threat_hc', 'danger')) +
            createCard('URLs Blocked', urlBlockedCount, createPill('url_blocked', 'warning'));
        
        if (summary.top_threats.length > 0) {
            const threatRows = summary.top_threats.map(t => [t.threat, t.count]);
            document.getElementById('top-threats-table').innerHTML = createTable(['Threat Name', 'Count'], threatRows);
        } else {
            document.getElementById('top-threats-table').innerHTML = '<p>No threat data available</p>';
        }
        
        if (summary.traffic_trend.length > 0) {
            const labels = summary.traffic_trend.map(d => d.date);
            const bytesData = summary.traffic_trend.map(d => (d.bytes / 1e9).toFixed(2));
            const datasets = [
                { label: 'Traffic (GB)', data: bytesData, color: '#0066cc', borderColor: '#0066cc', fill: false }
            ];
            createLineChart('traffic-trend-chart', labels, datasets, 'Daily Traffic Volume');
        }
        
        const typeRows = Object.entries(summary.by_type).map(([type, count]) => [type, count]);
        if (typeRows.length > 0) {
            document.getElementById('events-by-type-table').innerHTML = createTable(['Event Type', 'Count'], typeRows);
        } else {
            document.getElementById('events-by-type-table').innerHTML = '<p>No SOC data imported yet</p>';
        }
    } catch (err) {
        showToast('Gagal memuat data SOC: ' + err.message, 'error');
    }
}

async function renderHandover(content) {
    content.innerHTML = '<h2>Serah Terima</h2><div id="handover-list"></div>';
    
    try {
        const handovers = await apiGet('/api/handovers');
        
        if (handovers.length === 0) {
            document.getElementById('handover-list').innerHTML = '<p>Belum ada serah terima</p>';
        } else {
            const rows = handovers.map(h => [
                h.site,
                h.text,
                createPill(h.priority, h.priority === 'Tinggi' ? 'danger' : 'info'),
                h.shift,
                formatDate(h.date),
                createPill(h.open ? 'Open' : 'Done', h.open ? 'warning' : 'success')
            ]);
            document.getElementById('handover-list').innerHTML = createTable(['Site', 'Catatan', 'Prioritas', 'Shift', 'Tanggal', 'Status'], rows);
        }
    } catch (err) {
        showToast('Gagal memuat handover: ' + err.message, 'error');
    }
}

async function renderShifts(content) {
    content.innerHTML = '<h2>Jadwal Shift 14 Hari</h2><div id="shift-calendar"></div>';
    
    try {
        const calendar = await apiGet('/api/shifts/calendar');
        
        const headers = ['Tanggal', 'Team 1', 'Team 2', 'Team 3', 'Team 4'];
        const rows = calendar.map(day => {
            const shiftPills = {
                'Pagi': 'success',
                'Sore': 'warning',
                'Malam': 'info',
                'Off': 'secondary'
            };
            
            return [
                formatDate(day.date),
                createPill(day['Team 1'], shiftPills[day['Team 1']]),
                createPill(day['Team 2'], shiftPills[day['Team 2']]),
                createPill(day['Team 3'], shiftPills[day['Team 3']]),
                createPill(day['Team 4'], shiftPills[day['Team 4']])
            ];
        });
        
        document.getElementById('shift-calendar').innerHTML = createTable(headers, rows);
    } catch (err) {
        showToast('Gagal memuat jadwal: ' + err.message, 'error');
    }
}

async function renderImport(content) {
    content.innerHTML = '<h2>Impor Data Excel</h2><p>Fitur ini akan dikembangkan di fase berikutnya.</p>';
}

async function renderUsers(content) {
    if (currentUser.role !== 'Admin') {
        content.innerHTML = '<p>Akses ditolak. Hanya Admin yang dapat mengakses halaman ini.</p>';
        return;
    }
    content.innerHTML = '<h2>Manajemen Pengguna</h2><p>Fitur ini akan dikembangkan di fase berikutnya.</p>';
}

document.addEventListener('DOMContentLoaded', initApp);
