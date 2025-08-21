// Simulador simples: envia leituras para /api/data do backend
// Uso: node tools/simulate-http.js --port 3002 --interval 1000

const args = process.argv.slice(2);
function getArg(name, def) {
  const i = args.indexOf(`--${name}`);
  if (i >= 0 && args[i + 1]) return args[i + 1];
  return def;
}

const port = Number(getArg('port', process.env.PORT || 3000));
const interval = Number(getArg('interval', 1000));

let total = 0;
let t = 0;

async function tick() {
  try {
    // Vazão oscilando entre 0 e ~12 L/min
    const flow = Math.max(0, 6 + 6 * Math.sin(t / 10) + (Math.random() - 0.5));
    total += (flow / 60) * (interval / 1000); // L acumulado
    t++;
    const body = {
      ts: Date.now(),
      totalLiters: Number(total.toFixed(3)),
      flowLmin: Number(flow.toFixed(2))
    };
    await fetch(`http://localhost:${port}/api/data`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (t % 10 === 0) console.log(`[sim] total=${body.totalLiters} L flow=${body.flowLmin} L/min`);
  } catch (e) {
    console.error('[sim] erro ao enviar:', e.message);
  }
}

console.log(`[sim] Enviando leituras para http://localhost:${port}/api/data a cada ${interval}ms...`);
setInterval(tick, interval);
