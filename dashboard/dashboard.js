/*
 * File: dashboard.js
 * Description: Lógica principal do dashboard NeuroRace (Versão adaptada para eSense).
 * Atualiza atenção, status do NeuroSky e nível de sinal para ambos os jogadores.
 */

class DashboardManager {
    constructor(chartsManager) {
        this.chartsManager = chartsManager;
        this.sessionStartTime = Date.now();
        this.uiElements = {};

        this.players = {
            '1': this.createPlayerState(),
            '2': this.createPlayerState()
        };
    }

    init() {
        this.cacheUIElements();
        this.chartsManager.initializeAllCharts();
        this.connectToBroker();
        setInterval(() => this.updateSessionTimer(), 1000);
        console.log("Dashboard Manager inicializado no modo comparativo (2 players).");
    }

    createPlayerState() {
        return {
            currentAttention: 0,
            attentionHistory: [],
            peakAttention: 0,
            avgAttention: 0,
            status: "unknown",
            poorSignalLevel: null
        };
    }

    cacheUIElements() {
        this.uiElements = {
            sessionTime: document.getElementById('sessionTime'),
            connectionStatus: document.getElementById('connectionStatus')?.querySelector('span'),

            // Player 1
            avgAttention1: document.getElementById('avgAttention1'),
            peakAttention1: document.getElementById('peakAttention1'),
            status1: document.getElementById('status-player1'),
            signal1: document.getElementById('signal-player1'),

            // Player 2
            avgAttention2: document.getElementById('avgAttention2'),
            peakAttention2: document.getElementById('peakAttention2'),
            status2: document.getElementById('status-player2'),
            signal2: document.getElementById('signal-player2')
        };
    }

    connectToBroker() {
        const socketUrl = "ws://localhost:3000";
        const socket = io(socketUrl);

        socket.on('connect', () => {
            if (this.uiElements.connectionStatus) this.uiElements.connectionStatus.textContent = 'Conectado';
        });

        socket.on('disconnect', () => {
            if (this.uiElements.connectionStatus) this.uiElements.connectionStatus.textContent = 'Desconectado';
        });

        socket.on('connect_error', () => {
            if (this.uiElements.connectionStatus) this.uiElements.connectionStatus.textContent = 'Erro';
        });

        // Agora recebemos tudo via eSense
        socket.on('eSense', (data) => {
            const { player, attention, status, poorSignalLevel } = data;

            if (player && this.players[player]) {
                // Atualiza atenção
                this.updatePlayerData(player, attention);

                // Atualiza status e sinal
                this.players[player].status = status;
                this.players[player].poorSignalLevel = poorSignalLevel;
                this.updatePlayerStatus(player, status, poorSignalLevel);
            }
        });
    }

    updatePlayerData(playerId, attentionValue) {
        const playerState = this.players[playerId];
        if (!playerState) return;

        playerState.currentAttention = attentionValue;
        playerState.attentionHistory.push(attentionValue);
        if (playerState.attentionHistory.length > 300) playerState.attentionHistory.shift();

        // Média e Pico
        const sum = playerState.attentionHistory.reduce((a, b) => a + b, 0);
        playerState.avgAttention = sum / playerState.attentionHistory.length;
        if (attentionValue > playerState.peakAttention) {
            playerState.peakAttention = attentionValue;
        }

        // Atualiza DOM
        document.getElementById(`avgAttention${playerId}`).textContent = Math.round(playerState.avgAttention);
        document.getElementById(`peakAttention${playerId}`).textContent = Math.round(playerState.peakAttention);

        // Atualiza gráfico
        this.chartsManager.updateRealtimeChart(playerId, attentionValue);
    }

    updatePlayerStatus(playerId, status, poorSignalLevel) {
        const statusEl = document.getElementById(`status-player${playerId}`);
        const signalEl = document.getElementById(`signal-player${playerId}`);

        if (statusEl) statusEl.textContent = status || "unknown";
        if (signalEl) signalEl.textContent = poorSignalLevel !== null ? poorSignalLevel : "-";
    }

    updateSessionTimer() {
        if (this.uiElements.sessionTime) {
            const elapsed = Date.now() - this.sessionStartTime;
            const time = new Date(elapsed).toISOString().substr(11, 8);
            this.uiElements.sessionTime.textContent = time;
        }
    }
}

// ===================================================================================
// PONTO DE ENTRADA
// ===================================================================================
document.addEventListener('DOMContentLoaded', () => {
    const charts = new ChartsManager();
    const dashboard = new DashboardManager(charts);
    dashboard.init();
});
