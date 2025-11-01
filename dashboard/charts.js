/*
 * File: charts.js
 * Description: Gerenciador de gráficos (Versão 3.2 - Passiva e Robusta).
 * Esta classe agora é um serviço que apenas cria e atualiza gráficos quando instruída.
 */

class ChartsManager {
    constructor() {
        this.charts = {};
        this.colors = {
            player1: '#0066FF',
            player2: '#FF1B1B',
            history: '#FFD700',
            performanceScore: '#39FF14',
            background: '#1A1F3A',
            grid: '#2A3054'
        };
    }

    // Método chamado pelo DashboardManager após o DOM estar pronto.
    initializeAllCharts() {
        Chart.defaults.color = '#FFFFFF';
        Chart.defaults.borderColor = this.colors.grid;
        Chart.defaults.font.family = 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif';
        
        this.createRealtimeChart();
        this.createHistoryChart();
        this.createPerformanceComparisonChart();
    }

    createRealtimeChart() {
        const ctx = document.getElementById('realtimeChart');
        if (!ctx) return;
        const gradientP1 = ctx.getContext('2d').createLinearGradient(0, 0, 0, 200);
        gradientP1.addColorStop(0, `${this.colors.player1}80`);
        gradientP1.addColorStop(1, `${this.colors.player1}10`);
        const gradientP2 = ctx.getContext('2d').createLinearGradient(0, 0, 0, 200);
        gradientP2.addColorStop(0, `${this.colors.player2}80`);
        gradientP2.addColorStop(1, `${this.colors.player2}10`);
        this.charts.realtime = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { label: 'Player 1 - Atenção (%)', data: [], borderColor: this.colors.player1, backgroundColor: gradientP1, borderWidth: 3, fill: true, tension: 0.4, pointRadius: 0 },
                    { label: 'Player 2 - Atenção (%)', data: [], borderColor: this.colors.player2, backgroundColor: gradientP2, borderWidth: 3, fill: true, tension: 0.4, pointRadius: 0 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, animation: { duration: 0 }, scales: { x: { display: false }, y: { min: 0, max: 100, grid: { color: this.colors.grid }, ticks: { color: '#B0B8C8' } } }, plugins: { legend: { display: true, position: 'top', labels: { color: '#FFFFFF' } }, tooltip: { mode: 'index', intersect: false, backgroundColor: this.colors.background } } }
        });
    }

    updateRealtimeChart(playerId, attentionValue) {
        const chart = this.charts.realtime;
        if (!chart) return;
        const datasetIndex = parseInt(playerId) - 1;
        if (datasetIndex < 0 || datasetIndex >= chart.data.datasets.length) return;
        const maxPoints = 100;
        chart.data.datasets[datasetIndex].data.push(attentionValue);
        if (chart.data.labels.length < maxPoints) chart.data.labels.push('');
        if (chart.data.datasets[datasetIndex].data.length > maxPoints) chart.data.datasets[datasetIndex].data.shift();
        if (chart.data.labels.length > maxPoints) chart.data.labels.shift();
        chart.update('none');
    }

    createHistoryChart() {
        const ctx = document.getElementById('historyChart');
        if (!ctx) return;
        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, `${this.colors.history}80`);
        gradient.addColorStop(1, `${this.colors.history}10`);
        this.charts.history = new Chart(ctx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'Atenção Histórica (%)', data: [], borderColor: this.colors.history, backgroundColor: gradient, borderWidth: 2, fill: true, tension: 0.4 }] },
            options: { responsive: true, maintainAspectRatio: false, scales: { x: { grid: { color: this.colors.grid }, ticks: { color: '#B0B8C8', maxTicksLimit: 8 } }, y: { min: 0, max: 100, grid: { color: this.colors.grid }, ticks: { color: '#B0B8C8' } } }, plugins: { legend: { display: false } } }
        });
    }

    updateHistoryChart(historyData) {
        if (!this.charts.history) return;
        this.charts.history.data.labels = historyData.map(d => new Date(d.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }));
        this.charts.history.data.datasets[0].data = historyData.map(d => d.attention);
        this.charts.history.update();
    }

    createPerformanceComparisonChart() {
        const ctx = document.getElementById('performanceComparisonChart');
        if (!ctx) return;
        this.charts.performance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [
                    { label: 'Pontuação', data: [], backgroundColor: `${this.colors.performanceScore}90`, borderColor: this.colors.performanceScore, borderWidth: 2, borderRadius: 5 },
                    { label: 'Atenção Média (%)', data: [], backgroundColor: `${this.colors.player1}90`, borderColor: this.colors.player1, borderWidth: 2, borderRadius: 5, yAxisID: 'y1' }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { type: 'linear', display: true, position: 'left', beginAtZero: true, grid: { color: this.colors.grid }, ticks: { color: '#B0B8C8' }, title: { display: true, text: 'Pontuação', color: this.colors.performanceScore } }, y1: { type: 'linear', display: true, position: 'right', min: 0, max: 100, grid: { drawOnChartArea: false }, ticks: { color: '#B0B8C8' }, title: { display: true, text: 'Atenção Média', color: this.colors.player1 } }, x: { grid: { display: false }, ticks: { color: '#B0B8C8' } } }, plugins: { legend: { position: 'top', labels: { color: '#FFFFFF' } } } }
        });
    }

    updatePerformanceComparisonChart(sessionData) {
        if (!this.charts.performance) return;
        const chart = this.charts.performance;
        const recentSessions = sessionData.slice(-7);
        chart.data.labels = recentSessions.map((s, i) => `Sessão ${i + 1}`);
        chart.data.datasets[0].data = recentSessions.map(s => s.score);
        chart.data.datasets[1].data = recentSessions.map(s => s.avgAttention);
        chart.update();
    }
}