// Espera a página carregar completamente para executar o código
window.onload = function() {
    // --- SIMULAÇÃO DE DADOS ---
    // No projeto final, o Jogo deve salvar esses dados no sessionStorage
    // antes de redirecionar para esta página.
    const mockRaceResults = [
        {
            name: 'Ester Silva',
            score: 9850,
            raceId: 'a1b2c3d4-race-1' // ID único da corrida
        },
        {
            name: 'João Victor',
            score: 9540,
            raceId: 'e5f6g7h8-race-2' // ID único da corrida
        }
    ];
    // Salva os dados mockados para o teste
    sessionStorage.setItem('lastRaceResults', JSON.stringify(mockRaceResults));
    // --- FIM DA SIMULAÇÃO ---


    // Tenta buscar os resultados da última corrida do armazenamento da sessão
    const lastRaceResults = JSON.parse(sessionStorage.getItem('lastRaceResults'));

    if (lastRaceResults && lastRaceResults.length >= 2) {
        const player1 = lastRaceResults[0];
        const player2 = lastRaceResults[1];

        // Atualiza as informações do Jogador 1
        document.getElementById('player-1-name').innerText = `Jogador 1: ${player1.name}`;
        document.getElementById('player-1-score').innerText = `Pontuação Final: ${player1.score}`;
        
        // Gera o QR Code para o Jogador 1
        const urlPlayer1 = `https://neurorace-app.web.app/results.html?race_id=${player1.raceId}`;
        new QRCode(document.getElementById("qrcode-player1"), {
            text: urlPlayer1,
            width: 200,
            height: 200,
            colorDark : "#000000",
            colorLight : "#ffffff",
            correctLevel : QRCode.CorrectLevel.H
        });

        // Atualiza as informações do Jogador 2
        document.getElementById('player-2-name').innerText = `Jogador 2: ${player2.name}`;
        document.getElementById('player-2-score').innerText = `Pontuação Final: ${player2.score}`;
        
        // Gera o QR Code para o Jogador 2
        const urlPlayer2 = `https://neurorace-app.web.app/results.html?race_id=${player2.raceId}`;
        new QRCode(document.getElementById("qrcode-player2"), {
            text: urlPlayer2,
            width: 200,
            height: 200,
            colorDark : "#000000",
            colorLight : "#ffffff",
            correctLevel : QRCode.CorrectLevel.H
        });

    } else {
        console.error("Não foi possível encontrar os dados da última corrida.");
        // Opcional: mostrar uma mensagem de erro na tela
    }
};