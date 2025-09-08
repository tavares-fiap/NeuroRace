

# NeuroRace — EEG Runner (MVP, Dockerized)

MVP para **gamificar a concentração** usando dados de EEG (simulados por enquanto e, em breve, reais com NeuroSky ThinkGear). Medimos o nível de atenção de **dois jogadores** e usamos esse valor para controlar a velocidade dos personagens em um **jogo runner** (Unreal) em **tela dividida** com obstáculos.

---

## 🧩 Arquitetura (alto nível)

1. **Simulador de EEG** (`eeg_acquisition/simulator.py`)
   Emula pacotes JSON no formato “ThinkGear-like” via **TCP** (porta configurável), incluindo `eSense.attention`, `eegPower`, `poorSignalLevel`, etc.

2. **Serviço de Aquisição** (`eeg_acquisition/acquisition_service.py`)
   Conecta no simulador via TCP, faz **suavização** do `attention` por janela móvel e publica o valor médio via **Socket.IO** para o **Broker**.

3. **Data Broker** (`data_broker/index.js`)
   Servidor **Socket.IO** em Node.js que recebe eventos `attention` e faz **broadcast** para qualquer cliente (jogo, dashboard, etc.).

> **Status do Jogo (Unreal):** em implementação — runner com **tela dividida**, obstáculos e **recebendo dados simulados** do Broker.
> **Status do Dashboard:** protótipo em teste (UI sendo definida). Será um projeto separado.

---

## 📁 Estrutura de Pastas

```text
.
├── docker-compose.yml
├── eeg_acquisition/
│   ├── acquisition_service.py
│   ├── simulator.py
│   └── Dockerfile
└── data_broker/
    ├── index.js
    ├── package.json
    └── Dockerfile
```

---

## 🐳 Pré-requisitos (Docker)

* **Docker** e **Docker Compose**
* Verifique a instalação:

  ```bash
  docker --version
  docker compose version   # ou: docker-compose --version
  ```

---

## ⚙️ Subindo tudo com Docker (passo a passo)

Na raiz do projeto:

1. **Build** das imagens

```bash
docker compose build
```

2. **Subir** os serviços em segundo plano

```bash
docker compose up -d
```

Isso iniciará:

* `broker` (Node/Socket.IO) em **:3000**
* `simulator-a` (TCP **:13854**) e `simulator-b` (TCP **:13855**)
* `acquisition-a` (PLAYER\_ID=1) lendo `simulator-a` e publicando no broker
* `acquisition-b` (PLAYER\_ID=2) lendo `simulator-b` e publicando no broker

> Subimos **duas instâncias** de simulador e aquisição para **simular dois dispositivos**/jogadores.

---

## 🔍 Acompanhando Logs

* Todos os serviços:

  ```bash
  docker compose logs -f
  ```

* Serviço específico (ex.: broker):

  ```bash
  docker compose logs -f broker
  ```

* Via **Docker Desktop**: selecione o container e abra a aba de **Logs**.

**O que esperar:**

* `broker` imprimirá eventos `attention` recebidos e rebroadcasts
* `simulator-*` mostrará pacotes JSON enviados (`-----sent data-----`)
* `acquisition-*` mostrará pacotes recebidos e o `attention` suavizado emitido (`-----sent attention=----`)

---

## 🧪 Teste rápido do Broker (cliente de exemplo)

Opcional, fora do Docker (requer Node instalado localmente):

```js
// test-client.js
const io = require('socket.io-client');
const socket = io('http://localhost:3000');
socket.on('connect', () => console.log('Cliente teste conectado'));
socket.on('attention', (data) => console.log('attention recebido:', data));
```

```bash
node test-client.js
```

Você deverá ver eventos `attention` com `{ player: 1|2, attention: <float> }`.

---

## ⚙️ Variáveis de Ambiente (principais)

**eeg\_acquisition/simulator.py**

* `ACQ_PORT` (default `13854`) — porta TCP do simulador
* `PACKET_INTERVAL` (default `1.0`) — intervalo entre pacotes (s)

**eeg\_acquisition/acquisition\_service.py**

* `PLAYER_ID` (default `1`) — id do jogador
* `ACQ_PORT` (default `13854`) — porta do simulador alvo
* `EEG_HOST` (default `127.0.0.1`) — host do simulador (em Docker usamos `simulator-a`/`simulator-b`)
* `BROKER_URL` (default `http://broker:3000`) — URL do Socket.IO
* `N_READINGS` (default `5`) — janela da média móvel do attention
* `POOR_SIGNAL_LEVEL_THRESHOLD` (default `100`) — ignora pacotes com `poorSignalLevel` acima do limite (no real, tende a `0`)

**data\_broker/index.js**

* Porta **3000** exposta (configurada no código)

> Todas já estão definidas no `docker-compose.yml` para o cenário com 2 jogadores.

---

## 🧯 Troubleshooting (BOs comuns)

Se algo não subir/atualizar corretamente, tente:

```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

Dicas:

* Verifique conflitos de porta locais (`3000`, `13854`, `13855`)
* Inspecione os logs do container com erro (`docker compose logs <serviço>`)
* Em redes corporativas/proxy, valide acesso entre containers (resolução de hostnames `simulator-a`, `broker` etc.)

---

## 🎮 Jogo (Unreal) — Status & Integração

**Status:** em desenvolvimento. O jogo é um **runner** com **tela dividida** e obstáculos. Já **recebe dados simulados** do Broker e ajusta a velocidade dos personagens conforme `attention`.

**Conexão esperada (lado do jogo):** cliente Socket.IO para `ws://<HOST_DO_BROKER>:3000`, escutando o evento:

```json
{ "player": 1 | 2, "attention": <float> }
```

> ![Jogo — Tela dividida](./images/game2.png)
> *Legenda: Imagens do jogo em desenvolvimento.*

---

## 📊 Dashboard — Status & Demonstrações

**Status:** protótipo em teste (UI/estética em definição) — **não está neste repositório** ainda.

> ![Dashboard — UI A](./images/dashboard1.gif)
> *Legenda: Prototipo do dashboard*


---

## 🔄 Fluxo de Dados (detalhe)

1. `simulator.py` gera pacotes como:

   ```json
   {
     "poorSignalLevel": 0..200,
     "eSense": { "attention": 0..100, "meditation": 0..100 },
     "eegPower": { "delta": ..., "theta": ..., "lowAlpha": ... },
     "rawEeg": -2048..2047,
     "blinkStrength": 0 ou 50..255
   }
   ```
2. `acquisition_service.py` lê do TCP, **filtra/suaviza** `attention` (média móvel com `N_READINGS`) e emite via Socket.IO:

   ```json
   { "player": 1|2, "attention": <float> }
   ```
3. `data_broker/index.js` rebroadcasta `attention` para todos os clientes conectados.

---

## 🧪 Rodar componentes sem Docker (opcional, dev)

> Recomendamos Docker para reproducibilidade.

* **Broker**

  ```bash
  cd data_broker
  npm install
  node index.js   # ws://localhost:3000
  ```

* **Simulador**

  ```bash
  cd eeg_acquisition
  python simulator.py
  ```

* **Aquisição**

  ```bash
  cd eeg_acquisition
  pip install "python-socketio[client]"
  python acquisition_service.py
  ```

Ajuste `EEG_HOST`, `ACQ_PORT` e `BROKER_URL` conforme seu ambiente.

---

## 🗺️ Roadmap / Próximos Passos

* **Jogo (Unreal)**

  * Finalizar assets (sprites), HUD, **progress bar**, feedback visual e polimento de UI/UX.
  * Parametrizar aceleração/atrito por `attention`, calibrar curvas.

* **Dashboard**

  * Fechar estética, consolidar telas e métricas.
  * (Futuro) Persistência (ex.: InfluxDB/Timescale) para histórico e análises.

* **NeuroSky Real**

  * Integrar ao **ThinkGear Connector** (socket TCP).
  * Ajustar `POOR_SIGNAL_LEVEL_THRESHOLD` (próximo de `0` no real).
  * Calibração de baseline e tratamento de artefatos (piscadas/movimento).

---

## 📄 Licença

Este projeto está sob a [MIT License](LICENSE).


