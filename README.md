# Hidrômetro Inteligente

> Monitoramento e simulação de consumo de água com ESP32 (firmware Arduino), MQTT, backend Node.js + Socket.IO e dashboard web em tempo real.

![Dashboard](./img/dashboard.png)
![Wokwi](./img/wokwi_sim.png)
![Controle](./img/control_page.png)

## Sumário

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Estrutura do Repositório](#estrutura-do-repositório)
- [Pré-Requisitos](#pré-requisitos)
- [Setup Rápido (Docker)](#setup-rápido-docker)
- [Setup Manual (Sem Docker)](#setup-manual-sem-docker)
- [Firmware ESP32](#firmware-esp32)
- [Simulação Wokwi](#simulação-wokwi)
- [APIs e Endpoints](#apis-e-endpoints)
- [Comandos Úteis](#comandos-úteis)
- [Simulação de Dados Sem Hardware](#simulação-de-dados-sem-hardware)
- [Histórico e Armazenamento](#histórico-e-armazenamento)
- [Fluxo de Desenvolvimento](#fluxo-de-desenvolvimento)
- [Erros Comuns e Soluções](#erros-comuns-e-soluções)
- [Roadmap / Próximos Passos](#roadmap--próximos-passos)

## Visão Geral

Este projeto implementa um "hidrômetro inteligente" experimental que:

- Publica leituras (total de litros + vazão em L/min) via MQTT.
- Recebe e retransmite dados em tempo real via WebSocket (Socket.IO).
- Exibe um dashboard com gráfico histórico e controle de simulação.
- Permite simular fluxo de água sem hardware real.

## Arquitetura

```
[ESP32 / Simulação] --MQTT--> [Broker Mosquitto / HiveMQ] --MQTT--> [Backend Node]
                                                     |--> [Socket.IO / REST API] --> [Dashboard Web]
```

## Funcionalidades

- Publicação periódica de consumo e vazão.
- Simulação (botão físico ou comandos HTTP/MQTT).
- Histórico em memória (fallback) ou SQLite (se `better-sqlite3` presente).
- Dashboard com gráfico em tempo real (Chart.js).
- Página de controle para reset/calibração/ajuste de fluxo simulado.

## Tecnologias

- Firmware: Arduino framework (ESP32), PubSubClient, LiquidCrystal_I2C, RTClib.
- Backend: Node.js, Express, Socket.IO, MQTT.js.
- Frontend: HTML/CSS/JS, Chart.js, Socket.IO client.
- Contêineres: Docker, docker-compose (backend + Mosquitto).
- Simulação: Wokwi + script HTTP.

## Estrutura do Repositório

```
backend/        # API + Socket.IO + MQTT bridge
frontend/       # Dashboard (index.html)
firmware/       # Código ESP32 (sketch.ino + config.h)
include/        # Headers compartilhados
docs/           # Documentação adicional
img/            # (adicione screenshots aqui)
mosquitto/      # Configuração broker local
scripts/        # Scripts auxiliares
Dockerfile
docker-compose.yml
diagram.json    # Wokwi (ligações e componentes)
wokwi.toml      # Configuração do simulador
```

## Pré-Requisitos

| Componente                        | Versão sugerida   |
| --------------------------------- | ----------------- |
| Node.js                           | >= 18 LTS         |
| Docker / Compose                  | Atual             |
| VS Code + Extensões               | PlatformIO, Wokwi |
| Python (para build nativo)        | 3.x               |
| ESP32 DevKit V1 (físico ou Wokwi) | -                 |

PowerShell (Windows) e Bash (Linux/macOS) funcionam. Exemplos dados em PowerShell; adapte para Bash se necessário.

## Setup Rápido (Docker)

```powershell
# Clonar
git clone https://github.com/<seu-usuario>/hidrometro_inteligente.git
cd hidrometro_inteligente

# Subir backend + Mosquitto
$env:PORT="3000"; $env:MQTT_URL="mqtt://mosquitto:1883"; docker compose up -d --build

# Logs
docker compose logs -f backend
```

Acesse:

- Dashboard: http://localhost:3000/dashboard/
- Controle: http://localhost:3000/control.html
- Health: http://localhost:3000/healthz
- Broker MQTT: mqtt://localhost:1883 (porta 9001 para WebSockets)

Usando broker público HiveMQ:

```powershell
docker compose down
$env:MQTT_URL="mqtt://broker.hivemq.com:1883"; docker compose up -d --build backend
```

## Setup Manual (Sem Docker)

```powershell
cd backend
npm install
$env:PORT="3000"; $env:MQTT_URL="mqtt://broker.hivemq.com:1883"; node server.js
```

Abrir `frontend/index.html` ou usar rota `/dashboard` servida pelo backend.

## Firmware ESP32

1. Abra `firmware/sketch.ino` (PlatformIO ou Arduino IDE).
2. Ajuste `config.h` (SSID, senha WiFi, tópicos MQTT se desejar).
3. Compile / upload (PlatformIO: `PIO Build` / `Upload`).
4. Botão de simulação alterna modo e LED.
5. Endpoints no microcontrolador:
   - `/api/current` — estado atual
   - `/api/sim?flow=8` — define fluxo simulado
   - `/api/sim?off=1` — desliga simulação

## Simulação Wokwi

- Abrir `diagram.json` em https://wokwi.com/projects/new e colar conteúdo.
- Confirmar: LCD I2C (0x27), RTC DS3231 (opcional — fallback se ausente), botão START.
- Verificar publicação MQTT (console serial imprimiu IP e status?)
- Broker Default (público) já funciona: `mqtt://broker.hivemq.com:1883`.
- Ajuste se quiser usar broker local expondo porta 1883.

## APIs e Endpoints

| Método | Endpoint                | Descrição                                            |
| ------ | ----------------------- | ---------------------------------------------------- |
| GET    | /healthz                | Liveness check                                       |
| GET    | /api/current            | Última leitura atual (JSON)                          |
| POST   | /api/data               | Injeta leitura manual (JSON)                         |
| GET    | /api/history            | Histórico recente (JSON)                             |
| POST   | /api/cmd                | Envia comando MQTT (reset, setCalibration, simulate) |
| GET    | /api/cmd?action=...     | Variante simples via query                           |
| GET    | /api/debug/history-size | Debug (memória vs DB)                                |

Exemplo POST de comando:

```powershell
curl -X POST http://localhost:3000/api/cmd -H "Content-Type: application/json" -d '{"action":"reset"}'
```

## Comandos Úteis

```powershell
# Rebuild containers
docker compose build --no-cache backend
# Subir em modo debug histórico
$env:DEBUG_HISTORY="1"; docker compose up -d --build
# Logs
docker compose logs -f backend
# Injetar leituras sintéticas
for ($i=0;$i -lt 5;$i++){ $t=50+$i; $f=(Get-Random -Minimum 5 -Maximum 12); curl -s -X POST http://localhost:3000/api/data -H "Content-Type: application/json" -d "{`"totalLiters`":$t,`"flowLmin`":$f}" | Out-Null; Start-Sleep -Milliseconds 500 }
```

Bash equivalente:

```bash
for i in {0..4}; do t=$((50+i)); f=$(( (RANDOM%7)+5 )); curl -s -X POST http://localhost:3000/api/data -H 'Content-Type: application/json' -d "{\"totalLiters\":$t,\"flowLmin\":$f}" >/dev/null; sleep 0.5; done
```

## Simulação de Dados Sem Hardware

Script interno:

```powershell
node backend/tools/simulate-http.js --interval 1000 --port 3000
```

Ele oscila vazão e injeta em `/api/data`.

## Histórico e Armazenamento

- Padrão: tenta carregar `better-sqlite3`. Se não disponível, usa memória (`memHistory`, limite 1000).
- Evento Socket.IO `history:init` envia últimos 200 pontos na conexão.
- Para persistir:
  1. Instalar dependência no backend: `npm install better-sqlite3`
  2. Reiniciar backend (em Docker editar Dockerfile para incluir build deps).

## Fluxo de Desenvolvimento

1. Editar código.
2. (Docker) Rebuild: `docker compose build backend && docker compose up -d`.
3. Verificar logs.
4. Testar endpoints e dashboard.

## Erros Comuns e Soluções

| Sintoma                            | Causa                            | Solução                                      |
| ---------------------------------- | -------------------------------- | -------------------------------------------- |
| /api/history vazio                 | Sem leituras recebidas           | Injete via POST ou verifique broker MQTT     |
| DB desabilitado                    | Native module faltando           | Instalar better-sqlite3 (ou aceitar memória) |
| Gráfico vazio mas valores aparecem | `history:init` não enviado ainda | Recarregar após gerar pontos                 |
| MQTT sem mensagens                 | Broker divergente                | Unificar URL (backend e firmware)            |

## Roadmap / Próximos Passos

- Persistência robusta (PostgreSQL ou Timeseries DB).
- Autenticação JWT / API Keys.
- Exportação CSV / Download histórico.
- Alertas (limite de vazão, vazamento).
- Interface PWA / Mobile.

---

Contribuições e melhorias são bem-vindas. Adicione suas screenshots em `img/` com os nomes citados ou ajuste os links.
