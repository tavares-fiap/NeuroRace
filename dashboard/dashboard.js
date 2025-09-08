/*
 * File: dashboard.js
 * Description: Lógica principal do dashboard NeuroRace (Versão 3.2 - Final e Robusta).
 * Este script é o único ponto de entrada, controlando a inicialização e o fluxo de dados.
 */

class DashboardManager {
    // O construtor agora recebe o gerenciador de gráficos como dependência
    constructor(chartsManager) {
        this.chartsManager = chartsManager;
        this.sessionStartTime = Date.now();
        this.uiElements = {};
        
        this.players = {
            '1': this.createPlayerState(),
            '2': this.createPlayerState()
        };
        
        this.mainPlayerId = '1'; // Player 1 é o padrão
    }
    
    // O método init é o maestro que orquestra toda a inicialização
    init() {
        this.cacheUIElements();
        this.chartsManager.initializeAllCharts();
        this.initializePlayerSelectors();
        this.loadPersistentData();
        this.connectToBroker();
        setInterval(() => this.updateSessionTimer(), 1000);
        console.log("Dashboard Manager inicializado com sucesso.");
    }

    createPlayerState() {
        return {
            currentAttention: 0,
            attentionHistory: [],
            score: 0,
            distance: 0,
            speed: 0,
            peakAttention: 0,
            avgAttention: 0,
            streak: 0
        };
    }
    
    cacheUIElements() {
        this.uiElements = {
            sessionTime: document.getElementById('sessionTime'),
            connectionStatus: document.getElementById('connectionStatus')?.querySelector('span'),
            avgAttention: document.getElementById('avgAttention'),
            gameScore: document.getElementById('gameScore'),
            totalDistance: document.getElementById('totalDistance'),
            peakAttention: document.getElementById('peakAttention'),
            currentSpeed: document.getElementById('currentSpeed'),
            streak: document.getElementById('streak'),
            attentionZone: document.getElementById('attentionZone'),
            energyFill: document.getElementById('energyFill'),
            energyPercentage: document.getElementById('energyPercentage')
        };
    }

    initializePlayerSelectors() {
        const selectors = document.querySelectorAll('.player-selector');
        selectors.forEach(button => {
            button.addEventListener('click', () => {
                selectors.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                this.mainPlayerId = button.dataset.playerId;
                console.log(`Jogador principal alterado para: ${this.mainPlayerId}`);
                
                const currentPlayerState = this.players[this.mainPlayerId];
                this.renderMainUI(currentPlayerState);
            });
        });
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

        socket.on('attention', (data) => {
            const { player, attention } = data;
            if (player && this.players[player]) {
                this.updatePlayerData(player, attention);
            }
        });
    }

    updatePlayerData(playerId, attentionValue) {
        const playerState = this.players[playerId];
        if (!playerState) return;

        playerState.currentAttention = attentionValue;
        playerState.attentionHistory.push(attentionValue);
        if (playerState.attentionHistory.length > 300) playerState.attentionHistory.shift();
        
        const attentionFactor = playerState.currentAttention / 100;
        playerState.speed = attentionFactor * 15;
        playerState.distance += playerState.speed * 0.2;
        playerState.score += Math.floor(attentionFactor * 10);
        if (playerState.currentAttention > playerState.peakAttention) playerState.peakAttention = playerState.currentAttention;
        const sum = playerState.attentionHistory.reduce((a, b) => a + b, 0);
        playerState.avgAttention = playerState.attentionHistory.length > 0 ? sum / playerState.attentionHistory.length : 0;
        playerState.streak = (attentionValue > 80) ? playerState.streak + 1 : 0;
        
        this.chartsManager.updateRealtimeChart(playerId, attentionValue);
        
        if (String(playerId) === String(this.mainPlayerId)) {
            this.renderMainUI(playerState);
        }
    }
    
    renderMainUI(player) {
        this.uiElements.avgAttention.textContent = Math.round(player.avgAttention);
        this.uiElements.gameScore.textContent = Math.round(player.score);
        this.uiElements.totalDistance.textContent = Math.round(player.distance);
        this.uiElements.peakAttention.textContent = Math.round(player.peakAttention);
        this.uiElements.currentSpeed.textContent = player.speed.toFixed(1);
        this.uiElements.streak.textContent = player.streak;
        
        this.updateAttentionZone(player.currentAttention);
        this.updateEnergyBar(player.currentAttention);
    }

    updateAttentionZone(attention) {
        const zoneElement = this.uiElements.attentionZone;
        if (!zoneElement) return;
        const indicator = zoneElement.querySelector('.zone-indicator');
        zoneElement.classList.remove('zone-neutral', 'zone-focus', 'zone-intense');
        if (attention < 50) {
            zoneElement.classList.add('zone-neutral');
            indicator.textContent = 'ZONA NEUTRA';
        } else if (attention < 80) {
            zoneElement.classList.add('zone-focus');
            indicator.textContent = 'FOCO ATIVO';
        } else {
            zoneElement.classList.add('zone-intense');
            indicator.textContent = 'FOCO INTENSO';
        }
    }
    
    updateEnergyBar(attention) {
        if (this.uiElements.energyFill) this.uiElements.energyFill.style.width = `${attention}%`;
        if (this.uiElements.energyPercentage) this.uiElements.energyPercentage.textContent = `${Math.round(attention)}%`;
    }

    updateSessionTimer() {
        if (this.uiElements.sessionTime) {
            const elapsed = Date.now() - this.sessionStartTime;
            const time = new Date(elapsed).toISOString().substr(11, 8);
            this.uiElements.sessionTime.textContent = time;
        }
    }

    loadPersistentData() {
        const rankingData = [
            { name: 'Player 1', score: 1250, avgAttention: 88, isCurrentPlayer: true },
            { name: 'Neural Master', score: 1190, avgAttention: 95, isCurrentPlayer: false },
            { name: 'BrainRunner', score: 1145, avgAttention: 92, isCurrentPlayer: false }
        ];
        this.renderRanking(rankingData);

        const evolutionData = [
            { score: 850, avgAttention: 75 }, { score: 920, avgAttention: 82 },
            { score: 880, avgAttention: 79 }, { score: 1100, avgAttention: 88 },
            { score: 1250, avgAttention: 91 }
        ];
        this.chartsManager.updatePerformanceComparisonChart(evolutionData);
        
        const historyData = Array.from({ length: 50 }, (_, i) => ({
            timestamp: Date.now() - (50 - i) * 60000,
            attention: 60 + Math.sin(i / 5) * 15 + (Math.random() - 0.5) * 10
        }));
        this.chartsManager.updateHistoryChart(historyData);
    }

    renderRanking(rankingData) {
        const rankingList = document.getElementById('rankingList');
        if (!rankingList) return;
        rankingList.innerHTML = '';
        rankingData.forEach((player, index) => {
            const item = document.createElement('div');
            item.className = `ranking-item ${player.isCurrentPlayer ? 'current-player' : ''}`;
            item.innerHTML = `
                <div class="rank-position">${index + 1}</div>
                <div class="player-info">
                    <div class="player-name">${player.name}</div>
                    <div class="player-stats">${player.score} pts</div>
                </div>
                <div class="player-score">${Math.round(player.avgAttention)}%</div>`;
            rankingList.appendChild(item);
        });
    }
}

// ===================================================================================
// PONTO DE ENTRADA ÚNICO E SEGURO
// ===================================================================================
document.addEventListener('DOMContentLoaded', () => {
    // 1. Cria a instância do gerenciador de gráficos.
    const charts = new ChartsManager();
    // 2. Cria a instância do gerenciador do dashboard, passando os gráficos para ele.
    const dashboard = new DashboardManager(charts);
    // 3. Inicia toda a aplicação.
    dashboard.init();
});