
# Hidrômetro Inteligente — Passo a Passo de Execução

## Estrutura do Projeto

- `firmware/` — Código do ESP32 (C++/Arduino, MQTT)
- `backend/` — Backend Node.js/Express para receber dados
- `frontend/` — Dashboard web para visualização
- `docs/` — Documentação e instruções
- `simulacao/` — Scripts e dicas para simulação

---

## Passo a Passo para Executar o Sistema

### 1. Firmware (ESP32)

1. Abra o arquivo `firmware/sketch.ino` na IDE Arduino ou PlatformIO.
2. Instale as bibliotecas necessárias:
   - WiFi.h
   - PubSubClient
3. Configure o WiFi e broker MQTT em `config.h`.
4. Compile e faça upload para o ESP32 físico **ou** simule no Wokwi ([link](https://wokwi.com/)).
5. O ESP32 irá publicar dados em `hidrometro/leandro/dados` no broker MQTT.

### 2. Backend (Node.js)

1. Instale o Node.js ([download aqui](https://nodejs.org/)).
2. Abra o terminal e acesse a pasta `backend/`:
   ```powershell
   cd backend
   ```
3. Instale as dependências e inicie o servidor:
   ```powershell
   npm install
   npm start
   ```
4. Backend disponível em `http://localhost:3000`.
   - Dashboard de controle (envio de comandos MQTT): `http://localhost:3000/control.html`
   - API REST atual: `GET /api/current`
   - API para comandos MQTT: `POST /api/cmd` com JSON `{ "action":"reset" }` ou `{ "action":"setCalibration", "value":7.5 }`

Opcional: rodar com Docker
```powershell
cd c:\Users\Leandro\Desktop\hidrometro_inteligente
docker build -t hidrometro-backend .
docker run --rm -p 3000:3000 hidrometro-backend
```

### 3. Frontend (Dashboard Web)

1. Abra o arquivo `frontend/index.html` em seu navegador.
2. O dashboard irá buscar dados do backend a cada 5 segundos.

### 4. Integração entre as Partes

- O ESP32 publica dados via MQTT.
- O backend pode ser adaptado para receber dados MQTT (usando biblioteca como `mqtt` para Node.js) ou via HTTP.
- O frontend consome dados do backend via API REST (`/api/current`).

### 5. Simulação sem Hardware

- Use o modo SIMULATE_FLOW no firmware para simular pulsos do sensor.
- Teste o código no Wokwi ([https://wokwi.com/](https://wokwi.com/)).
- Para simular MQTT, use brokers públicos como HiveMQ ou Mosquitto.
- Ferramentas úteis: MQTT Explorer, Postman, Wokwi.

Compilar para Wokwi (VS Code)
- Instale a extensão PlatformIO IDE
- No VS Code: PlatformIO: Build (gera `.pio/build/esp32dev/firmware.bin`)
- F1 → Wokwi: Start Simulator

### 6. Exemplos de Teste

- Envie dados manualmente para o backend:
  ```powershell
  curl -X POST http://localhost:3000/api/data -H "Content-Type: application/json" -d "{\"totalLiters\":123.4,\"flowRate\":5.6}"
  ```
- Veja os dados no dashboard (`frontend/index.html`).

### 7. Expansão

- Adicione autenticação nas APIs.
- Integre com banco de dados online (MongoDB, Firebase).
- Crie notificações (Telegram, Email) via backend.

### 8. Referências

- [Wokwi Simulator](https://wokwi.com/)
- [HiveMQ MQTT Broker](https://www.hivemq.com/public-mqtt-broker/)
- [Express.js](https://expressjs.com/)
- [PubSubClient Arduino](https://pubsubclient.knolleary.net/)

---

Dúvidas ou sugestões? Adapte conforme sua necessidade ou peça exemplos específicos!
