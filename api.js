async function apiCall(endpoint, method = 'GET', body = null) {
  try {
    const options = { method };
    if (body) {
      options.headers = { 'Content-Type': 'application/json' };
      options.body = JSON.stringify(body);
    }
    const res = await fetch(`http://localhost:3000${endpoint}`, options);
    if (!res.ok) {
      console.error('API ERROR:', await res.text());
      return null;
    }
    return await res.json();
  } catch (err) {
    console.error('FETCH ERROR:', err);
    return null;
  }
}

window.addEventListener('load', async () => {
  const status = await apiCall('/api/status');
  if (status?.ok) {
    setStatus('Connected ✅', 'success');
    refreshDashboard();
    startAutoRefresh();
  } else {
    setStatus('API Connection Failed ❌', 'error');
  }
});

async function refreshDashboard() {
  const el = document.getElementById('dashboardContent');
  el.innerHTML = '<div class="loading">Loading dashboard...</div>';
  
  const [playersData, bansData] = await Promise.all([
    apiCall('/api/players'),
    apiCall('/api/bans')
  ]);
  
  if (!playersData || !bansData) {
    el.innerHTML = '<div class="error-message">Failed to load dashboard</div>';
    return;
  }
  
  el.innerHTML = `
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Online Players</div>
        <div class="stat-value">${playersData.playerCount || 0}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Bans</div>
        <div class="stat-value">${bansData.bans?.length || 0}</div>
      </div>
    </div>
    <div class="table-container">
      <table class="table">
        <thead><tr><th>Player</th><th>ID</th><th>Job</th></tr></thead>
        <tbody>
          ${playersData.players?.map(p => 
            `<tr><td>${p.username || 'Unknown'}</td><td>${p.userid || 'N/A'}</td><td>${p.job || 'N/A'}</td></tr>`
          ).join('') || '<tr><td colspan="3">No players online</td></tr>'}
        </tbody>
      </table>
    </div>
  `;
}

let currentLogs = [];
async function refreshLogs() {
  const el = document.getElementById('logsContent');
  el.innerHTML = '<div class="loading">Loading logs...</div>';
  
  const players = await apiCall('/api/players');
  if (!players) {
    el.innerHTML = '<div class="error-message">Failed to load logs</div>';
    return;
  }
  
  currentLogs = players.players || [];
  renderLogs(currentLogs);
}

function renderLogs(logs) {
  const el = document.getElementById('logsContent');
  if (!logs.length) {
    el.innerHTML = '<div class="empty-state">No recent activity</div>';
    return;
  }
  
  el.innerHTML = `
    <div class="table-container">
      <table class="table">
        <thead><tr><th>Username</th><th>User ID</th><th>Job</th></tr></thead>
        <tbody>${logs.map(p => 
          `<tr><td>${p.username || 'Unknown'}</td><td>${p.userid || 'N/A'}</td><td>${p.job || 'N/A'}</td></tr>`
        ).join('')}</tbody>
      </table>
    </div>
  `;
}

function filterLogs() {
  const q = document.getElementById('logFilter').value.toLowerCase();
  const typeFilter = document.getElementById('logTypeFilter').value;
  renderLogs(currentLogs.filter(p => 
    p.username?.toLowerCase().includes(q) || 
    String(p.userid).includes(q)
  ));
}

async function refreshStaff() {
  const el = document.getElementById('staffContent');
  el.innerHTML = '<div class="loading">Loading staff list...</div>';
  
  const staffData = await apiCall('/api/staff');
  if (!staffData || !staffData.staff) {
    el.innerHTML = '<div class="error-message">Failed to load staff</div>';
    return;
  }
  
  const allStaff = [];
  const staff = staffData.staff;
  
  if (staff.CoOwners) {
    staff.CoOwners.forEach(id => allStaff.push({ id, role: 'Co-Owner' }));
  }
  if (staff.Admins) {
    Object.entries(staff.Admins).forEach(([id, username]) => 
      allStaff.push({ id, username, role: 'Admin' })
    );
  }
  if (staff.Mods) {
    Object.entries(staff.Mods).forEach(([id, username]) => 
      allStaff.push({ id, username, role: 'Moderator' })
    );
  }
  
  el.innerHTML = `
    <div class="table-container">
      <table class="table">
        <thead><tr><th>Username</th><th>Role</th><th>ID</th></tr></thead>
        <tbody>
          ${allStaff.map(s => 
            `<tr><td>${s.username || s.id}</td><td>${s.role}</td><td>${s.id}</td></tr>`
          ).join('') || '<tr><td colspan="3">No staff members</td></tr>'}
        </tbody>
      </table>
    </div>
  `;
}

async function executeCommand(cmd) {
  if (!cmd || !cmd.trim()) {
    showError('Command cannot be empty');
    return;
  }
  
  showSuccess(`Executing: ${cmd}`);
  const res = await apiCall('/api/command', 'POST', { command: cmd });
  
  if (res) {
    showSuccess(`${cmd} executed`);
    addCommandToHistory(cmd);
  } else {
    showError(`Command failed: ${cmd}`);
  }
}

function promoteUser(role) {
  const username = document.getElementById(`${role}Username`).value.trim();
  if (username) executeCommand(`${role} ${username}`);
}

function kickPlayer() {
  const user = document.getElementById('kickUsername').value.trim();
  const reason = document.getElementById('kickReason').value.trim() || 'No reason';
  executeCommand(`:kick ${user} ${reason}`);
}

function banPlayer() {
  const user = document.getElementById('banUsername').value.trim();
  const reason = document.getElementById('banReason').value.trim() || 'No reason';
  executeCommand(`:ban ${user} ${reason}`);
}

function warnPlayer() {
  const user = document.getElementById('warnUsername').value.trim();
  const reason = document.getElementById('warnReason').value.trim() || 'No reason';
  executeCommand(`:warn ${user} ${reason}`);
}

function changeWeather() {
  const weather = document.getElementById('weatherSelect').value;
  executeCommand(`:weather ${weather}`);
}

function announceServer() {
  const msg = document.getElementById('announceText').value.trim();
  if (msg) executeCommand(`:h ${msg}`);
}

function restartServer() {
  const delay = document.getElementById('restartDelay').value || 60;
  executeCommand(`:restart ${delay}`);
}

function setPeaceTimer() {
  const minutes = document.getElementById('peaceTimerMinutes').value || 5;
  executeCommand(`:pt ${minutes}`);
}

function executeCustomCommand() {
  const cmd = document.getElementById('customCommand').value.trim();
  executeCommand(cmd);
}

// UI HELPERS
let refreshInterval = parseInt(localStorage.getItem('refreshInterval'), 10) || 30000;
let autoRefreshTimer = null;
let commandHistory = [];

function showPage(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function startAutoRefresh() {
  clearInterval(autoRefreshTimer);
  autoRefreshTimer = setInterval(refreshDashboard, refreshInterval);
}

function updateRefreshInterval() {
  refreshInterval = parseInt(document.getElementById('refreshInterval').value, 10) || 30;
  refreshInterval = Math.max(5000, Math.min(300000, refreshInterval * 1000));
  localStorage.setItem('refreshInterval', refreshInterval);
  startAutoRefresh();
  showSuccess('Refresh interval updated');
}

function addCommandToHistory(cmd) {
  commandHistory.unshift({ cmd, time: new Date().toLocaleTimeString() });
  commandHistory = commandHistory.slice(0, 20);
  
  const historyList = document.getElementById('commandHistoryList');
  if (historyList) {
    historyList.innerHTML = commandHistory.map(c => 
      `<div><strong>${c.cmd}</strong><br><small>${c.time}</small></div>`
    ).join('');
  }
}

function setStatus(msg, type) {
  const statusEl = document.getElementById('connectionStatus');
  statusEl.innerHTML = `<span class="${type}">${msg}</span>`;
}

function showError(msg) {
  setStatus(msg, 'error');
  setTimeout(() => setStatus('Connected ✅', 'success'), 3000);
}

function showSuccess(msg) {
  setStatus(msg, 'success');
  setTimeout(() => setStatus('Connected ✅', 'success'), 3000);
}
