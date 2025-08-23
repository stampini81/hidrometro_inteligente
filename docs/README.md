# Hidrômetro Inteligente — Execução (Flask Unificado)

> Agora apenas Flask + Socket.IO + MQTT. Backend Node removido.

## Estrutura do Projeto (atual)
- `MVC_sistema_leitura_hidrometros/` — Backend Flask (API, Socket.IO, MQTT, modelos)
- `firmware/` — Código ESP32 (publica MQTT JSON)
- `img/` — Screenshots dashboard/controle
- `mosquitto/` — Configuração broker local (docker-compose)
- `scripts/` — Scripts auxiliares
- `docs/` — Documentação

## Requisitos Rápidos
Veja `docs/REQUIREMENTS.md` (atualizar para remover Node). Essencial:
- Python 3.11+
- Docker (opcional, recomendado)
- Broker MQTT (Mosquitto local via compose ou HiveMQ público)
- curl (testes) / MQTT Explorer (debug)

## Configuração do .env
Copie `.env.example` para `.env` e ajuste:
```
DB_ENGINE=sqlite
MQTT_URL=mqtt://broker.hivemq.com:1883
MQTT_TOPIC_DADOS=hidrometro/dados
MQTT_TOPIC_CMD=hidrometro/cmd
SECRET_KEY=changeme
HISTORY_LIMIT=1000
```

## Execução via Docker Compose
```
docker compose up -d --build
# Logs
docker compose logs -f flask
```
Acessos:
- Dashboard: http://localhost:5000/dashboard
- Controle:  http://localhost:5000/control
- Health:    http://localhost:5000/healthz

## Execução Local (Sem Docker)
```
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/requirements.txt
python MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/run.py
```

## Migrações (Banco)
Primeira vez:
```
flask --app MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/app db init
```
Novas mudanças de modelo:
```
flask --app MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/app db migrate -m "alter"
flask --app MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/app db upgrade
```

## Autenticação / Token
```
curl -X POST http://localhost:5000/api/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin"}'
```
Resposta: {"token":"<JWT>"}
Header: `Authorization: Bearer <JWT>`.

## Injetar Leitura Manual
```
TOKEN=$(curl -s -X POST http://localhost:5000/api/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin"}' | python -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -X POST http://localhost:5000/api/data -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"totalLiters":42.5,"flowLmin":3.1,"numeroSerie":"ABC123"}'
```

## Enviar Comando MQTT
```
curl -X POST http://localhost:5000/api/cmd -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"action":"reset"}'
```

## Endpoints Principais
| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | /healthz | - | Status |
| POST | /api/login | - | Obter JWT |
| GET | /api/current | - | Última leitura |
| GET | /api/history | - | Histórico (limite=200 default) |
| POST | /api/data | Bearer | Injetar leitura |
| POST/GET | /api/cmd | Bearer | Publicar comando MQTT |
| GET | /api/debug/history-size | Bearer | Tamanho histórico in-memory |

## Fluxo de Dados
```
ESP32 -> MQTT Broker -> Flask (paho-mqtt) -> (persistência + histórico) -> Socket.IO -> Dashboard
```

## Firmware Payload Exemplo
```
{"totalLiters": 10.2, "flowLmin": 0.8, "numeroSerie": "ABC123"}
```

## Simulação Sem Hardware
- Publicar manualmente usando algum cliente MQTT no tópico configurado.
- Ou usar POST /api/data (JWT requerido).

## Erros Comuns
| Problema | Causa | Ação |
|----------|-------|------|
| 401 em /api/data | JWT ausente | Gerar via /api/login |
| Dashboard vazio | Sem mensagens MQTT | Enviar leitura de teste |
| Falha MySQL | Credenciais erradas | Ajustar .env |

## Roadmap
- Exportação CSV
- Alertas (vazamento / fluxo anômalo)
- API Keys persistentes
- PWA offline

---
Atualizado para backend Flask unificado.
