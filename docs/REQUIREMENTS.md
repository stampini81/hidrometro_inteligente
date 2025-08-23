# Requisitos do Projeto (Flask Unificado)

## 1) Sistema Operacional
- Windows 10/11 (ou Linux/macOS com ajustes equivalentes)

## 2) Ferramentas Essenciais
- Git
- Python 3.11+
- VS Code (extensões recomendadas: Python, PlatformIO, Wokwi)
- (Opcional) Docker Desktop + WSL2
- Broker MQTT: usar público (HiveMQ) ou local (Mosquitto via docker-compose)

## 3) Dependências Python
Arquivo: `MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/requirements.txt`
Instalação local:
```
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/requirements.txt
```

Principais libs:
- Flask / Flask-SocketIO
- SQLAlchemy / Flask-Migrate
- paho-mqtt
- PyJWT
- python-dotenv

## 4) MQTT
Variáveis relevantes (.env):
```
MQTT_URL=mqtt://broker.hivemq.com:1883
MQTT_TOPIC_DADOS=hidrometro/dados
MQTT_TOPIC_CMD=hidrometro/cmd
```
Para broker local (docker-compose):
```
docker compose up -d mosquitto
```
Portas: 1883 (TCP), 9001 (WebSockets se configurado).

## 5) Banco de Dados
Default: SQLite arquivo (instância local). Para MySQL configure no .env:
```
DB_ENGINE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=usuario
DB_PASSWORD=senha
DB_NAME=hidrometro
```
Criar migrações após alterar modelos:
```
flask --app MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/app db migrate -m "alter"
flask --app MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/app db upgrade
```

## 6) Firmware / Wokwi
- Editar `firmware/config.h` (SSID/WiFi, tópicos se mudar)
- Payload JSON publicado conforme exemplo: `{ "totalLiters": 12.3, "flowLmin": 0.7, "numeroSerie": "ABC123" }`
- Simulação Wokwi: abra `diagram.json`.

## 7) Execução Rápida (Docker)
```
cp .env.example .env
# Ajustar variáveis
docker compose up -d --build
```
Acessar: http://localhost:5000/dashboard

## 8) Execução Local (Sem Docker)
```
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/requirements.txt
python MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/run.py
```

## 9) Testes Rápidos
```
curl -X GET http://localhost:5000/healthz
curl -X POST http://localhost:5000/api/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin"}'
```

## 10) Solução de Problemas
| Sintoma | Causa | Solução |
|---------|-------|---------|
| Sem dados | Firmware não publica | Verificar tópico / broker |
| 401 em POST | Sem token | Obter via /api/login |
| Socket falha | Portas bloqueadas | Liberar 5000 / firewall |
| MySQL erro | Credenciais erradas | Ajustar .env |

## 11) Próximos (Roadmap)
- Export CSV
- Alertas e regras
- API Keys / refresh tokens
- PWA offline

---
Documento atualizado para versão Flask unificada.
