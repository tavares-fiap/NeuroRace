# Gamifying Concentration with NeuroSky (MVP)

Este projeto apresenta um **MVP ultra-simplificado** para gamificar a concentração de usuários usando dados de EEG simulados — e, no futuro, reais vindos de um headset NeuroSky MindWave Mobile. A ideia é medir o nível de atenção de dois jogadores e, a partir dele, controlar a velocidade de seus personagens em um jogo competitivo.

---

## 🚀 Visão Geral

1. **Simulador de EEG** (`eeg_acquisition/simulator.py`): gera dados JSON parecidos com os do NeuroSky e os envia por TCP.
2. **Serviço de Aquisição** (`eeg_acquisition/acquisition_service.py`): lê o fluxo TCP, filtra e suaviza (_rolling window_), e publica via Socket.IO no Broker.
3. **Data Broker** (`data_broker/index.js`): serviço Node.js que recebe eventos `attention` e faz broadcast para qualquer cliente conectado (jogo, dashboard, analytics).

> 🔜 **Próximos passos**:  
> - Implementar o **jogo** (Unity / Unreal/ Phaser / Godot) capaz de receber eventos de atenção e ajustar a velocidade dos personagens.  
> - Adicionar um **Dashboard** web para monitorar métricas em tempo real e histórico de concentração.  
> - Substituir o simulador pelo **ThinkGear Connector** e headset NeuroSky real.

---

## 📁 Estrutura de Pastas

```text
.
├── eeg_acquisition/
│   ├── config.py
│   ├── simulator.py
│   └── acquisition_service.py
└── data_broker/
    ├── index.js
    └── package.json
````

* **`eeg_acquisition/`**

  * `config.py` — endereços, portas e constantes de configuração.
  * `simulator.py` — servidor TCP que emula o NeuroSky.
  * `acquisition_service.py` — cliente TCP + Socket.IO que filtra e publica atenção.

* **`data_broker/`**

  * `index.js` — servidor Socket.IO que recebe e retransmite eventos.
  * `package.json` — dependências Node.js (Socket.IO).

---

## 🛠️ Pré-requisitos

* **Python 3.8+**
* **Node.js 14+** e **npm**
* (Opcional) **ThinkGear Connector** e headset NeuroSky MindWave Mobile

---

## ⚙️ Como Rodar o MVP

Abra **três** terminais distintos:

### 1. Subir o Broker (Node.js)

```bash
cd data_broker
npm install          # instala socket.io
node index.js        # inicia em ws://localhost:3000
```

Você deverá ver:

```
Broker conectado, aguardando conexao...
```

### 2. Iniciar o Simulador de EEG

```bash
cd eeg_acquisition
python simulator.py
```

Saída esperada:

```
TGC Simulator ouvindo em 127.0.0.1:13854
[+] Conectado em ('127.0.0.1', XXXXX)
Iniciando stream de dados...
-----sent data-----
{"poorSignalLevel": ...}
```

### 3. Iniciar o Serviço de Aquisição

Em outro terminal:

```bash
cd eeg_acquisition
pip install python-socketio         # instale se ainda não tiver
pip install "python-socketio[client]"
python acquisition_service.py
```

Saída esperada:

```
-----received data----
{ "poorSignalLevel": 0, "eSense": { "attention": 72, ... } }
-----sent attention=----
68.4
```

> **Obs.** certifique-se de que os valores de `HOST`, `ACQUISITION_PORT` e `BROKER_URL` em `config.py` correspondam ao simulador e ao broker.

---

## 🔍 Como Testar

1. **Verificar logs** do Broker (`data_broker/index.js`):

   * Sempre que receber um evento, vai imprimir o JSON com `player` e `attention`.

2. **Adicionar um cliente de teste**:

   ```js
   // test-client.js
   const io = require('socket.io-client');
   const socket = io('http://localhost:3000');
   socket.on('attention', data => {
     console.log('Evento recebido no cliente de teste:', data);
   });
   ```

   ```bash
   node test-client.js
   ```

3. **Substituir o simulador**: quando o ThinkGear Connector e o headset estiverem prontos, basta:

   * Remover o simulador ou desligar `simulator.py`.
   * No `acquisition_service.py`, implementar a conexão ao TGC real lendo do socket TCP 13854 após o handshake.
   * Ajustar `POOR_SIGNAL_LEVEL_THRESHOLD = 0` em `config.py`.

---

## 🎮 Próximos Passos

* **Módulo de Jogo**:

  * Conectar-se via Socket.IO e mover sprites/personagens conforme `attention`.
  * Implementar lógica de competição e linha de chegada.

* **Dashboard e Analytics**:

  * Serviço dedicado para armazenar dados em série temporal (InfluxDB / TimescaleDB).
  * Frontend React para visualizar gráficos em tempo real e históricos.

* **Integração Completa**:

  * Calibração inicial do NeuroSky (baseline de atenção).
  * Tratamento de artefatos (piscadas, movimento).
  * Autenticação e configuração de múltiplos jogadores.

---

## 📄 Licença

Este projeto está sob a [MIT License](LICENSE). Sinta-se à vontade para clonar, modificar e contribuir!
