const fs = require('fs');
const path = require('path');
const Database = require('better-sqlite3');

const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}
const dbPath = path.join(dataDir, 'hidrometro.db');
const db = new Database(dbPath);

// Melhora concorrência para leitura
try { db.pragma('journal_mode = WAL'); } catch (e) {}

db.exec(`
CREATE TABLE IF NOT EXISTS readings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts INTEGER NOT NULL,
  totalLiters REAL,
  flowLmin REAL
);
CREATE INDEX IF NOT EXISTS idx_readings_ts ON readings (ts);
`);

const stmtInsert = db.prepare('INSERT INTO readings (ts, totalLiters, flowLmin) VALUES (?, ?, ?)');
const stmtRecent = db.prepare('SELECT ts, totalLiters, flowLmin FROM readings ORDER BY ts DESC LIMIT ?');
const stmtRange = db.prepare('SELECT ts, totalLiters, flowLmin FROM readings WHERE ts BETWEEN ? AND ? ORDER BY ts ASC');

function insertReading({ ts, totalLiters, flowLmin }) {
  if (!ts) ts = Date.now();
  try { stmtInsert.run(ts, Number(totalLiters ?? 0), Number(flowLmin ?? 0)); } catch (e) {}
}

function getRecent(limit = 500) {
  const lim = Math.min(Math.max(parseInt(limit || 500, 10), 1), 5000);
  // Retorna em ordem ascendente para gráfico
  const rows = stmtRecent.all(lim).reverse();
  return rows;
}

function getRange(from, to) {
  const f = Number(from) || 0;
  const t = Number(to) || Date.now();
  return stmtRange.all(f, t);
}

module.exports = { insertReading, getRecent, getRange };
