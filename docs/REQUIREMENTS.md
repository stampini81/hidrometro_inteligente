# Requisitos do Projeto (Windows)

Este documento reúne tudo o que você precisa instalar/configurar para rodar o projeto em três cenários: Docker, Wokwi (simulação) e execução local sem Docker.

## 1) Sistema operacional
- Windows 10 (build 19041+) ou Windows 11
- Acesso de administrador para instalar ferramentas

## 2) Ferramentas essenciais
- VS Code (obrigatório)
- Git (recomendado)
- Extensões VS Code (recomendadas):
  - PlatformIO IDE (compilar firmware ESP32)
  - Wokwi Simulator (simular ESP32 e periféricos)

## 3) Backend (escolha 1 dos caminhos)

### Caminho A — Docker (recomendado)
- Docker Desktop for Windows (WSL2 recomendado)
- Verificações rápidas (PowerShell):
  - `docker --version`
  - `docker compose version`
  - `docker info` (Docker Desktop deve estar “Running”)
- Portas livres: 3000 (backend), 1883/9001 (Mosquitto, se usar broker local)

### Caminho B — Sem Docker (local)
- Node.js LTS 18+ (ou 20+)
- Verificações:
  - `node -v` → v18.x ou v20.x
  - `npm -v`
- Observação: `better-sqlite3` pode exigir ferramentas de build (Windows Build Tools). O projeto funciona sem BD (histórico), mas recomendado.

## 4) Firmware e Wokwi (ESP32)
Duas formas de compilar o firmware para o Wokwi:

### Opção 1 — VS Code + PlatformIO IDE (GUI)
- Instale a extensão “PlatformIO IDE”.
- No VS Code: PlatformIO: Build → gera `.pio/build/esp32dev/firmware.bin` e `.elf`.
- Depois: F1 → “Wokwi: Start Simulator”.

### Opção 2 — PlatformIO Core (CLI)
- Requer Python 3.10+
- Instale o PIO Core:
  - `py -m pip install --user platformio`
- Compilar:
  - `py -m platformio run` (na raiz do projeto)
- Depois inicie o Wokwi.

### Conectividade
- Wokwi (firmware) usa WiFi Wokwi-GUEST (sem senha) por padrão.
- Broker MQTT público (HiveMQ) para integração com o backend: `broker.hivemq.com:1883`.

## 5) Ferramentas úteis (opcional)
- MQTT Explorer (inspecionar tópicos MQTT)
- Postman / curl (testar APIs)

## 6) Variáveis de ambiente
O backend aceita estas variáveis (via `.env` ou compose):
- `PORT` (padrão: 3000)
- `MQTT_URL` (ex.: `mqtt://broker.hivemq.com:1883` ou `mqtt://mosquitto:1883`)
- `MQTT_TOPIC` (padrão: `hidrometro/leandro/dados`)
- `MQTT_CMD_TOPIC` (padrão: `hidrometro/leandro/cmd`)

## 7) Checklists rápidos

### Docker + Broker público (Wokwi)
1. Docker Desktop em execução (Running)
2. `.env` na raiz com:
```
PORT=3000
MQTT_URL=mqtt://broker.hivemq.com:1883
MQTT_TOPIC=hidrometro/leandro/dados
MQTT_CMD_TOPIC=hidrometro/leandro/cmd
```
3. `docker compose up --build -d backend`
4. Dashboard: http://localhost:3000/dashboard

### Wokwi
1. PlatformIO: Build → cria `.pio/build/esp32dev/firmware.bin`
2. F1 → Wokwi: Start Simulator
3. Botão IO4 (verde): Start/Stop simulação + LED IO13
4. LCD (I2C 0x27) mostra total e vazão

### Local sem Docker
1. `cd backend && npm install`
2. `setx PORT 3000` (ou `$env:PORT='3000'` para sessão atual)
3. `npm start`
4. Dashboard: http://localhost:3000/dashboard

## 8) Solução de problemas
- Wokwi erro “firmware.bin not found”: rode PlatformIO: Build. Verifique se o arquivo existe em `.pio/build/esp32dev/`.
- Docker avisa sobre `config.json` com caractere ‘ï’: remova o BOM do arquivo `C:\Users\SEU_USUARIO\.docker\config.json`.
- `docker` não reconhecido: abra Docker Desktop e reinicie o PowerShell; verifique PATH.
- Sem dados no dashboard: confira broker/tópico no `.env` e no firmware (ambos devem usar `hidrometro/leandro/dados`).
