/**
 * File: dashboard.js
 * Description: Script principal do dashboard NeuroRace responsável por gerenciar
 * a lógica de negócio, atualização de métricas em tempo real e interação com o usuário.
 * * Author: Ester Silva
 * Created on: 02-09-2025
 * * Version: 1.1.0 
 * Squad: Neurorace
 */

class NeuroRaceDashboard {
    constructor() {
        this.sessionStartTime = Date.now();
        this.currentAttention = 0;
        this.attentionHistory = [];
        this.gameMetrics = { score: 0, distance: 0, speed: 0, peakAttention: 0, avgAttention: 0, streak: 0 };
        this.achievementFlags = { concentrationExtreme: false, speedster: false };

        document.addEventListener('DOMContentLoaded', () => this.init());
    }

    init() {
        this.updateSessionTimer();
        this.initializeEventListeners();
        this.startSimulation(); // Simula dados em tempo real
        this.loadMockData(); // Carrega dados de exemplo para os gráficos

        setInterval(() => this.updateSessionTimer(), 1000);
    }

    initializeEventListeners() {
        // Time filter buttons
        document.querySelectorAll('.time-filter').forEach(button => {
            button.addEventListener('click', (e) => {
                document.querySelectorAll('.time-filter').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                // Lógica para atualizar gráfico de histórico aqui...
            });
        });

        // Criar tooltips dinamicamente
        document.querySelectorAll('.metric-card[data-tooltip]').forEach(card => {
            const tooltipText = card.getAttribute('data-tooltip');
            if (tooltipText) {
                const tooltipElement = document.createElement('span');
                tooltipElement.className = 'tooltip-text';
                tooltipElement.textContent = tooltipText;
                card.appendChild(tooltipElement);
            }
        });
    }

    updateSessionTimer() {
        const elapsed = Date.now() - this.sessionStartTime;
        const time = new Date(elapsed).toISOString().substr(11, 8);
        document.getElementById('sessionTime').textContent = time;
    }

    startSimulation() {
        setInterval(() => {
            const baseAttention = 60 + Math.sin(Date.now() / 10000) * 20;
            const noise = (Math.random() - 0.5) * 30;
            this.currentAttention = Math.max(0, Math.min(100, baseAttention + noise));
            
            this.attentionHistory.push({ timestamp: Date.now(), attention: this.currentAttention });
            if (this.attentionHistory.length > 1000) this.attentionHistory.shift();

            this.updateLiveMetrics();
            neuroRaceCharts.updateRealtimeChart(this.currentAttention);
        }, 100);
    }

    updateLiveMetrics() {
        const attentionFactor = this.currentAttention / 100;
        this.gameMetrics.speed = attentionFactor * 15;
        this.gameMetrics.distance += this.gameMetrics.speed * 0.1;
        this.gameMetrics.score += Math.floor(attentionFactor * 10);
        if (this.currentAttention > this.gameMetrics.peakAttention) {
            this.gameMetrics.peakAttention = this.currentAttention;
        }
        
        const sum = this.attentionHistory.reduce((acc, item) => acc + item.attention, 0);
        this.gameMetrics.avgAttention = sum / this.attentionHistory.length;

        this.updateStreak();
        this.checkAchievements();
        this.renderMetrics();
    }
    
    renderMetrics() {
        document.getElementById('avgAttention').textContent = Math.round(this.gameMetrics.avgAttention);
        document.getElementById('gameScore').textContent = Math.round(this.gameMetrics.score);
        document.getElementById('totalDistance').textContent = Math.round(this.gameMetrics.distance);
        document.getElementById('peakAttention').textContent = Math.round(this.gameMetrics.peakAttention);
        document.getElementById('currentSpeed').textContent = this.gameMetrics.speed.toFixed(1);
        document.getElementById('streak').textContent = this.gameMetrics.streak;
        
        this.updateAttentionZone();
        this.updateEnergyBar();
    }

    updateStreak() {
        const highAttentionThreshold = 80;
        if (this.currentAttention > highAttentionThreshold) {
            this.gameMetrics.streak++;
        } else {
            this.gameMetrics.streak = 0;
        }
    }

    checkAchievements() {
        if (this.gameMetrics.speed >= 14.5 && !this.achievementFlags.speedster) {
            this.achievementFlags.speedster = true;
            this.showAchievement('Velocista Mental');
        }
    }

    showAchievement(achievementName) {
        // Criar notificação
        const notification = document.createElement('div');
        notification.className = 'achievement-notification'; // Estilo injetado via JS
        notification.innerHTML = `<i class="fas fa-trophy"></i><div><div class="achievement-title">Nova Conquista!</div><div class="achievement-name">${achievementName}</div></div>`;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);

        // Animar o badge correspondente
        document.querySelectorAll('.badge-name').forEach(badge => {
            if (badge.textContent === achievementName) {
                const parentBadge = badge.closest('.achievement-badge');
                if (parentBadge && parentBadge.classList.contains('locked')) {
                    parentBadge.classList.remove('locked');
                    parentBadge.classList.add('earned', 'newly-earned');
                    setTimeout(() => parentBadge.classList.remove('newly-earned'), 10000); // Remove o brilho
                }
            }
        });
    }

    updateAttentionZone() {
        const zoneElement = document.getElementById('attentionZone');
        const indicator = zoneElement.querySelector('.zone-indicator');
        zoneElement.classList.remove('zone-neutral', 'zone-focus', 'zone-intense');

        if (this.currentAttention < 50) {
            zoneElement.classList.add('zone-neutral');
            indicator.textContent = 'ZONA NEUTRA';
        } else if (this.currentAttention < 80) {
            zoneElement.classList.add('zone-focus');
            indicator.textContent = 'FOCO ATIVO';
        } else {
            zoneElement.classList.add('zone-intense');
            indicator.textContent = 'FOCO INTENSO';
        }
    }

    updateEnergyBar() {
        const energyFill = document.getElementById('energyFill');
        const energyPercentage = document.getElementById('energyPercentage');
        energyFill.style.width = `${this.currentAttention}%`;
        energyPercentage.textContent = `${Math.round(this.currentAttention)}%`;
    }

    loadMockData() {
        // Dados para Ranking
        const rankingData = [
            { name: 'Você', score: 2450, distance: 1250, avgAttention: 98, isCurrentPlayer: true },
            { name: 'Neural Master', score: 2380, distance: 1190, avgAttention: 95, isCurrentPlayer: false },
            { name: 'BrainRunner', score: 2290, distance: 1145, avgAttention: 92, isCurrentPlayer: false },
            { name: 'NeuroNinja', score: 2150, distance: 1080, avgAttention: 88, isCurrentPlayer: false }
        ];
        this.updateRanking(rankingData);
        
        // Dados para o novo gráfico de comparação de sessões
        const mockSessionData = [
            {score: 850, avgAttention: 75}, {score: 920, avgAttention: 82},
            {score: 880, avgAttention: 79}, {score: 1100, avgAttention: 88},
            {score: 1050, avgAttention: 85}, {score: 1250, avgAttention: 91}
        ];
        neuroRaceCharts.updatePerformanceComparisonChart(mockSessionData);
    }

    updateRanking(rankingData) {
        const rankingList = document.getElementById('rankingList');
        rankingList.innerHTML = '';
        rankingData.forEach((player, index) => {
            const item = document.createElement('div');
            item.className = `ranking-item ${player.isCurrentPlayer ? 'current-player' : ''}`;
            item.innerHTML = `
                <div class="rank-position">${index + 1}</div>
                <div class="player-info">
                    <div class="player-name">${player.name}</div>
                    <div class="player-stats">${player.score} pts • ${player.distance}m</div>
                </div>
                <div class="player-score">${Math.round(player.avgAttention)}%</div>`;
            rankingList.appendChild(item);
        });
    }
}

// Injetar estilos de notificação para não precisar de outro arquivo CSS
const achievementStyles = `
.achievement-notification {
    position: fixed; top: 20px; right: 20px; background: var(--gradient-secondary);
    color: white; padding: 1rem 1.5rem; border-radius: 12px; display: flex;
    align-items: center; gap: 1rem; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    animation: slideIn 0.5s ease, slideOut 0.5s ease 2.5s; z-index: 1000;
}
.achievement-notification i { font-size: 2rem; color: var(--neon-yellow); }
.achievement-title { font-weight: 600; font-size: 0.9rem; }
.achievement-name { font-weight: 900; font-size: 1.1rem; }
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
@keyframes slideOut { from { transform: translateX(0); opacity: 1; } to { transform: translateX(100%); opacity: 0; } }
`;
const styleSheet = document.createElement("style");
styleSheet.textContent = achievementStyles;
document.head.appendChild(styleSheet);


// Inicializar a classe principal do dashboard
new NeuroRaceDashboard();