/*
 * File: charts.js
 * Description: Gerenciador de gráficos do dashboard NeuroRace usando Chart.js.
 * Responsável por criar e atualizar visualizações de dados em tempo real,
 * histórico de atenção, métricas de performance e análises estatísticas.
 *
 * Author: Ester Silva
 * Created on: 02-09-2025
 *
 * Version: 1.1.0
 * Squad: Neurorace
 */

class NeuroRaceCharts {
    constructor() {
        this.charts = {};
        this.colors = {
            primary: '#00FFFF',      // Neon cyan
            secondary: '#FF1B8D',    // Neon pink
            accent: '#FFD700',       // Neon yellow
            success: '#39FF14',      // Neon green
            background: '#1A1F3A',   // Dark background
            grid: '#2A3054'          // Grid color
        };

        // Espera o DOM carregar para inicializar os gráficos
        document.addEventListener('DOMContentLoaded', () => this.initializeCharts());
    }

    initializeCharts() {
        // Configurar Chart.js defaults
        Chart.defaults.color = '#FFFFFF';
        Chart.defaults.borderColor = this.colors.grid;
        Chart.defaults.font.family = 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif';

        this.createRealtimeChart();
        this.createHistoryChart();
        this.createPerformanceComparisonChart(); // Adicionado novo gráfico
    }

    createRealtimeChart() {
        const ctx = document.getElementById('realtimeChart');
        if (!ctx) return;

        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 200);
        gradient.addColorStop(0, `${this.colors.primary}80`);
        gradient.addColorStop(1, `${this.colors.primary}10`);

        this.charts.realtime = new Chart(ctx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'Atenção (%)', data: [], borderColor: this.colors.primary, backgroundColor: gradient, borderWidth: 3, fill: true, tension: 0.4, pointRadius: 0 }] },
            options: { responsive: true, maintainAspectRatio: false, animation: { duration: 0 }, interaction: { intersect: false, mode: 'index' }, scales: { x: { display: false }, y: { min: 0, max: 100, grid: { color: this.colors.grid }, ticks: { color: '#B0B8C8', callback: (value) => value + '%' } } }, plugins: { legend: { display: false }, tooltip: { backgroundColor: this.colors.background, borderColor: this.colors.primary, borderWidth: 1, displayColors: false } } }
        });
    }

    createHistoryChart() {
        const ctx = document.getElementById('historyChart');
        if (!ctx) return;
        
        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, `${this.colors.secondary}80`);
        gradient.addColorStop(1, `${this.colors.secondary}10`);

        this.charts.history = new Chart(ctx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'Atenção Histórica (%)', data: [], borderColor: this.colors.secondary, backgroundColor: gradient, borderWidth: 2, fill: true, tension: 0.4, pointRadius: 1 }] },
            options: { responsive: true, maintainAspectRatio: false, scales: { x: { grid: { color: this.colors.grid }, ticks: { color: '#B0B8C8', maxTicksLimit: 8 } }, y: { min: 0, max: 100, grid: { color: this.colors.grid }, ticks: { color: '#B0B8C8', callback: (value) => value + '%' } } }, plugins: { legend: { display: false } } }
        });
    }

    createPerformanceComparisonChart() {
        const ctx = document.getElementById('performanceComparisonChart');
        if (!ctx) return;

        this.charts.performanceComparison = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [], // Ex: ['Sessão 1', 'Sessão 2', ...]
                datasets: [{
                    label: 'Pontuação',
                    data: [], // Ex: [850, 920, 880, ...]
                    backgroundColor: `${this.colors.accent}90`,
                    borderColor: this.colors.accent,
                    borderWidth: 2,
                    borderRadius: 5
                },
                {
                    label: 'Atenção Média (%)',
                    data: [], // Ex: [75, 82, 79, ...]
                    backgroundColor: `${this.colors.primary}90`,
                    borderColor: this.colors.primary,
                    borderWidth: 2,
                    borderRadius: 5,
                    yAxisID: 'y1' // Associa a um segundo eixo Y
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: true,
                        grid: { color: this.colors.grid },
                        ticks: { color: '#B0B8C8' },
                        title: { display: true, text: 'Pontuação', color: this.colors.accent }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        min: 0,
                        max: 100,
                        grid: { drawOnChartArea: false }, // Evita linhas de grade duplicadas
                        ticks: { color: '#B0B8C8', callback: (value) => value + '%' },
                        title: { display: true, text: 'Atenção Média', color: this.colors.primary }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#B0B8C8' }
                    }
                },
                plugins: {
                    legend: { position: 'top', labels: { color: '#FFFFFF' } }
                }
            }
        });
    }

    updateRealtimeChart(attentionValue) {
        if (!this.charts.realtime) return;
        const chart = this.charts.realtime;
        const maxPoints = 100;

        chart.data.labels.push(new Date().toLocaleTimeString());
        chart.data.datasets[0].data.push(attentionValue);

        if (chart.data.labels.length > maxPoints) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }
        chart.update('none');
    }
    
    updateHistoryChart(historyData) {
        if (!this.charts.history) return;
        const chart = this.charts.history;
        chart.data.labels = historyData.map(d => new Date(d.timestamp).toLocaleTimeString());
        chart.data.datasets[0].data = historyData.map(d => d.attention);
        chart.update();
    }
    
    updatePerformanceComparisonChart(sessionData) {
        if (!this.charts.performanceComparison) return;
        const chart = this.charts.performanceComparison;
        const recentSessions = sessionData.slice(-7); // Limita para as últimas 7

        chart.data.labels = recentSessions.map((s, i) => `Sessão ${i + 1}`);
        chart.data.datasets[0].data = recentSessions.map(s => s.score);
        chart.data.datasets[1].data = recentSessions.map(s => s.avgAttention);

        chart.update();
    }
}

// Inicializa a classe de gráficos.
// O dashboard.js poderá acessar via window.neuroRaceCharts
const neuroRaceCharts = new NeuroRaceCharts();