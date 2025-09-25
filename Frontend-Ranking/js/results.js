// Função para pegar o ID da corrida da URL
function getRaceIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('race_id');
}

// Função principal que será executada quando a página carregar
async function loadRaceResults() {
    const raceId = getRaceIdFromUrl();
    if (!raceId) {
        document.body.innerHTML = '<h1>ID da corrida não encontrado!</h1>';
        return;
    }

    // Busca o documento específico da corrida no Firestore
    const raceDocRef = db.collection('races').doc(raceId);
    const docSnap = await raceDocRef.get();

    if (docSnap.exists) {
        const raceData = docSnap.data();

        // Preenche os elementos HTML com os dados da corrida
        document.getElementById('greeting').innerText = `Parabéns, ${raceData.playerName}!`;
        document.getElementById('behavioral-profile').innerText = raceData.behavioral_profile;
        document.getElementById('summary').innerHTML = `
            <p>Você manteve uma média de atenção de <strong>${raceData.average_attention}%</strong>, com picos de <strong>${raceData.peak_attention}%</strong> nos momentos decisivos. Isso mostra que você brilha sob pressão!</p>
        `; // [cite: 107]

        // Renderiza o gráfico de performance
        renderPerformanceChart(raceData.attention_data_points);

    } else {
        document.body.innerHTML = '<h1>Resultados da corrida não encontrados!</h1>';
    }
}

// Função para criar o gráfico com Chart.js
function renderPerformanceChart(dataPoints) {
    const ctx = document.getElementById('performance-chart').getContext('2d');
    
    // Prepara os dados para o formato que o Chart.js espera
    const labels = dataPoints.map(p => p.time); // Eixo X (tempo)
    const data = dataPoints.map(p => p.value);  // Eixo Y (valor da atenção)

    new Chart(ctx, {
        type: 'line', // Tipo de gráfico
        data: {
            labels: labels,
            datasets: [{
                label: 'Nível de Atenção',
                data: data,
                borderColor: 'rgba(75, 192, 192, 1)',
                tension: 0.1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

// Inicia o processo quando a página é carregada
loadRaceResults();