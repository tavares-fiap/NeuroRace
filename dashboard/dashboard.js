/*
 * File: dashboard.js
 * Description: Lógica principal do dashboard NeuroRace (Versão adaptada para layout com 2 players lado a lado).
 * Atualiza os status, atenção média, pico máximo e gráfico em tempo real de ambos os jogadores.
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
            status: "Aguardando..."
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

            // Player 2
            avgAttention2: document.getElementById('avgAttention2'),
            peakAttention2: document.getElementById('peakAttention2'),
            status2: document.getElementById('status-player2')
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

        // Dados de atenção recebidos
        socket.on('attention', (data) => {
            const { player, attention } = data;
            if (player && this.players[player]) {
                this.updatePlayerData(player, attention);
            }
        });

        // Status vindo do pacote eSense
        socket.on('status', (data) => {
            const { player, status } = data;
            if (player && this.players[player]) {
                this.players[player].status = status;
                this.updatePlayerStatus(player, status);
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

    updatePlayerStatus(playerId, status) {
        const el = document.getElementById(`status-player${playerId}`);
        if (el) el.textContent = status;
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
