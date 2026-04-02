const express = require('express');
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));
const cors = require('cors');
const path = require('path');
const app = express();

// CONFIG - Replace with your actual ERLC private server API key
const SERVER_KEY = '';
const ERLC_BASE = 'https://api.policeroleplay.community/v1';

// midware
app.use(cors({ origin: '*', credentials: true }));
app.use(express.json());
app.use(express.static(__dirname));

// help func
async function erlcRequest(endpoint, method = 'GET', body = null) {
  const options = {
    method,
    headers: {
      'Server-Key': SERVER_KEY,
      'Content-Type': 'application/json'
    }
  };
  if (body) options.body = JSON.stringify(body);

  try {
    const res = await fetch(`${ERLC_BASE}${endpoint}`, options);
    if (!res.ok) {
      const text = await res.text();
      console.error('ERLC API Error', res.status, text);
      throw new Error(`HTTP ${res.status}: ${text}`);
    }
    return await res.json();
  } catch (error) {
    console.error('ERLC Request failed', endpoint, error.message);
    throw error;
  }
}

// routes
app.get('/api/status', async (req, res) => {
  try {
    await erlcRequest('/server');
    res.json({ ok: true });
  } catch (e) {
    console.error('Status check failed', e.message);
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.get('/api/players', async (req, res) => {
  try {
    const data = await erlcRequest('/server/players');
    res.json({ 
      players: data || [],
      playerCount: data?.length || 0 
    });
  } catch (e) {
    console.error('Players fetch failed', e.message);
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/staff', async (req, res) => {
  try {
    const data = await erlcRequest('/server/staff');
    res.json({ staff: data || {} });
  } catch (e) {
    console.error('Staff fetch failed', e.message);
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/bans', async (req, res) => {
  try {
    const data = await erlcRequest('/server/bans');
    res.json({ bans: data || [] });
  } catch (e) {
    console.error('Bans fetch failed', e.message);
    res.status(500).json({ error: e.message });
  }
});

app.post('/api/command', async (req, res) => {
  try {
    const { command } = req.body;
    if (!command || typeof command !== 'string') {
      return res.status(400).json({ error: 'Command is required' });
    }
    console.log('Executing ERLC command:', command);
    const data = await erlcRequest('/server/command', 'POST', { command });
    res.json(data);
  } catch (e) {
    console.error('Command execution failed', e.message);
    res.status(500).json({ error: e.message });
  }
});

// serve front end
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'Frontend.html'));
});

// start
const PORT = 3000;
app.listen(PORT, () => {
  console.log(`\n🚀 ERLC Dashboard running at http://localhost:${PORT}`);
  console.log('📁 Serving files from:', __dirname);
  console.log('🔑 Make sure SERVER_KEY is your actual ERLC API key!\n');
});
