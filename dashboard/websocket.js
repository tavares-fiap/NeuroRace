/**
 * File: websocket.js
 * Description: Gerenciador de WebSocket para comunicação em tempo real com o backend
 * do NeuroRace. Responsável por receber dados do NeuroSky, enviar comandos e
 * manter sincronização entre dashboard e servidor.
 * 
 * Responsabilidades:
 * - Estabelecer e manter conexão WebSocket
 * - Processar mensagens em tempo real do NeuroSky
 * - Gerenciar reconexão automática
 * - Sincronizar estado entre cliente e servidor
 * - Tratar diferentes tipos de mensagens (atenção, jogo, ranking)
 * 
 * Author: Ester Silva
 * Created on: 02-09-2025
 * 
 * Version: 1.0.0
 * Squad: Neurorace
 */

class NeuroRaceWebSocket {
    constructor(url, dashboard) {
        this.url = url;
        this.dashboard = dashboard;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 1000; // 1 segundo
        this.isConnected = false;
        this.messageHandlers = new Map();
        
        this.setupMessageHandlers();
    }

    setupMessageHandlers() {
        // Registrar handlers para diferentes tipos de mensagem
        this.messageHandlers.set('attention', this.handleAttentionData.bind(this));
        this.messageHandlers.set('gameMetrics', this.handleGameMetrics.bind(this));
        this.messageHandlers.set('playerRanking', this.handleRankingUpdate.bind(this));
        this.messageHandlers.set('systemStatus', this.handleSystemStatus.bind(this));
        this.messageHandlers.set('neuroskyStatus', this.handleNeuroskyStatus.bind(this));
        this.messageHandlers.set('raceStart', this.handleRaceStart.bind(this));
        this.messageHandlers.set('raceEnd', this.handleRaceEnd.bind(this));
    }

    connect() {
        try {
            console.log(`Connecting to WebSocket: ${this.url}`);
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = this.onOpen.bind(this);
            this.ws.onmessage = this.onMessage.bind(this);
            this.ws.onclose = this.onClose.bind(this);
            this.ws.onerror = this.onError.bind(this);
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.scheduleReconnect();
        }
    }

    onOpen(event) {
        console.log('WebSocket connected successfully');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        
        // Atualizar status no dashboard
        this.dashboard.updateConnectionStatus(true);
        
        // Enviar handshake inicial
        this.send({
            type: 'handshake',
            clientType: 'dashboard',
            timestamp: Date.now()
        });
        
        // Solicitar estado atual
        this.requestCurrentState();
    }

    onMessage(event) {
        try {
            const message = JSON.parse(event.data);
            console.log('WebSocket message received:', message);
            
            // Verificar se existe handler para o tipo de mensagem
            const handler = this.messageHandlers.get(message.type);
            if (handler) {
                handler(message.data);
            } else {
                console.warn('No handler found for message type:', message.type);
            }
            
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }

    onClose(event) {
        console.log('WebSocket connection closed:', event.code, event.reason);
        this.isConnected = false;
        this.dashboard.updateConnectionStatus(false);
        
        // Tentar reconectar se não foi fechamento intencional
        if (event.code !== 1000) {
            this.scheduleReconnect();
        }
    }

    onError(error) {
        console.error('WebSocket error:', error);
        this.dashboard.updateConnectionStatus(false);
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1); // Backoff exponencial
            
            console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
            
            setTimeout(() => {
                if (!this.isConnected) {
                    this.connect();
                }
            }, delay);
        } else {
            console.error('Max reconnection attempts reached');
            this.dashboard.showError('Conexão perdida. Verifique sua internet e recarregue a página.');
        }
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, message not sent:', message);
        }
    }

    requestCurrentState() {
        this.send({
            type: 'requestState',
            timestamp: Date.now()
        });
    }

    // Message Handlers
    handleAttentionData(data) {
        /*
         * Esperado formato dos dados:
         * {
         *   attention: number (0-100),
         *   meditation: number (0-100),
         *   timestamp: number,
         *   playerId: string
         * }
         */
        
        if (data.attention !== undefined) {
            this.dashboard.updateAttention(data.attention);
        }
        
        if (data.meditation !== undefined) {
            this.dashboard.updateMeditation(data.meditation);
        }
        
        // Armazenar no histórico
        this.dashboard.addToHistory({
            attention: data.attention,
            meditation: data.meditation,
            timestamp: data.timestamp || Date.now()
        });
    }

    handleGameMetrics(data) {
        /*
         * Esperado formato dos dados:
         * {
         *   score: number,
         *   distance: number,
         *   speed: number,
         *   position: {x: number, y: number},
         *   playerId: string
         * }
         */
        
        this.dashboard.updateGameMetrics(data);
    }

    handleRankingUpdate(data) {
        /*
         * Esperado formato dos dados:
         * {
         *   ranking: [
         *     {
         *       playerId: string,
         *       name: string,
         *       score: number,
         *       distance: number,
         *       avgAttention: number,
         *       isCurrentPlayer: boolean
         *     }
         *   ]
         * }
         */
        
        this.dashboard.updateRanking(data.ranking);
    }

    handleSystemStatus(data) {
        /*
         * Esperado formato dos dados:
         * {
         *   status: 'online' | 'offline' | 'maintenance',
         *   message: string,
         *   activeUsers: number
         * }
         */
        
        console.log('System status update:', data);
        
        if (data.status === 'maintenance') {
            this.dashboard.showWarning('Sistema em manutenção: ' + data.message);
        }
    }

    handleNeuroskyStatus(data) {
        /*
         * Esperado formato dos dados:
         * {
         *   connected: boolean,
         *   signalQuality: number (0-4),
         *   batteryLevel: number (0-100),
         *   deviceId: string
         * }
         */
        
        this.dashboard.updateNeuroskyStatus(data);
        
        if (!data.connected) {
            this.dashboard.showWarning('NeuroSky desconectado. Verifique o dispositivo.');
        } else if (data.signalQuality < 2) {
            this.dashboard.showWarning('Qualidade do sinal baixa. Ajuste o headset.');
        }
    }

    handleRaceStart(data) {
        /*
         * Esperado formato dos dados:
         * {
         *   raceId: string,
         *   players: [string],
         *   startTime: number,
         *   duration: number
         * }
         */
        
        console.log('Race started:', data);
        this.dashboard.startRace(data);
        this.dashboard.showInfo('Corrida iniciada! Concentre-se para acelerar!');
    }

    handleRaceEnd(data) {
        /*
         * Esperado formato dos dados:
         * {
         *   raceId: string,
         *   results: [
         *     {
         *       playerId: string,
         *       position: number,
         *       finalScore: number,
         *       finalDistance: number,
         *       avgAttention: number
         *     }
         *   ]
         * }
         */
        
        console.log('Race ended:', data);
        this.dashboard.endRace(data);
        
        // Encontrar resultado do jogador atual
        const currentPlayerResult = data.results.find(r => r.playerId === this.dashboard.currentPlayerId);
        if (currentPlayerResult) {
            this.dashboard.showRaceResult(currentPlayerResult);
        }
    }

    // Métodos para enviar comandos ao servidor
    startRace() {
        this.send({
            type: 'startRace',
            timestamp: Date.now()
        });
    }

    stopRace() {
        this.send({
            type: 'stopRace',
            timestamp: Date.now()
        });
    }

    calibrateNeurosky() {
        this.send({
            type: 'calibrateDevice',
            timestamp: Date.now()
        });
    }

    resetMetrics() {
        this.send({
            type: 'resetMetrics',
            timestamp: Date.now()
        });
    }

    // Cleanup
    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
        }
    }
}

// Função para inicializar WebSocket quando o dashboard estiver pronto
function initializeWebSocket(dashboardInstance) {
    // URL do WebSocket - ajustar conforme configuração do backend
    const wsUrl = `ws://${window.location.hostname}:8080/ws/dashboard`;
    
    const webSocket = new NeuroRaceWebSocket(wsUrl, dashboardInstance);
    
    // Conectar automaticamente
    webSocket.connect();
    
    // Expor WebSocket globalmente para debug
    window.neuroRaceWS = webSocket;
    
    return webSocket;
}

// Event listeners para controles do WebSocket
document.addEventListener('DOMContentLoaded', () => {
    // Botões de controle (adicionar ao HTML se necessário)
    const startRaceBtn = document.getElementById('startRaceBtn');
    const stopRaceBtn = document.getElementById('stopRaceBtn');
    const calibrateBtn = document.getElementById('calibrateBtn');
    
    if (startRaceBtn) {
        startRaceBtn.addEventListener('click', () => {
            if (window.neuroRaceWS) {
                window.neuroRaceWS.startRace();
            }
        });
    }
    
    if (stopRaceBtn) {
        stopRaceBtn.addEventListener('click', () => {
            if (window.neuroRaceWS) {
                window.neuroRaceWS.stopRace();
            }
        });
    }
    
    if (calibrateBtn) {
        calibrateBtn.addEventListener('click', () => {
            if (window.neuroRaceWS) {
                window.neuroRaceWS.calibrateNeurosky();
            }
        });
    }
});

// Cleanup ao fechar a página
window.addEventListener('beforeunload', () => {
    if (window.neuroRaceWS) {
        window.neuroRaceWS.disconnect();
    }
});