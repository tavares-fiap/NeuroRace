// Referência para a coleção 'races' no Firestore
const racesCollection = db.collection('races');

// Referência ao elemento HTML onde a lista será exibida
const rankingListContainer = document.getElementById('ranking-list');

// Criamos um "ouvinte" (listener) para a coleção de corridas
// Ordenamos por 'final_score' em ordem decrescente e pegamos os 10 melhores (limit)
racesCollection.orderBy('final_score', 'desc').limit(10).onSnapshot(querySnapshot => {
    // Limpa a lista antiga para não duplicar
    rankingListContainer.innerHTML = '';

    let rank = 1; // Para numerar as posições
    
    // Para cada corrida (documento) retornada na consulta...
    querySnapshot.forEach(doc => {
        const raceData = doc.data();

        // Cria o HTML para este item do ranking
        const rankingItem = `
            <div class="ranking-item">
                <span class="rank-position">${rank}</span>
                <div class="player-info">
                    <span class="player-name">${raceData.playerName}</span>
                    <span class="player-attention">Atenção Média: ${raceData.average_attention}%</span>
                </div>
                <span class="player-score">${raceData.final_score} PTS</span>
            </div>
        `;
        
        // Adiciona o item criado ao container da lista
        rankingListContainer.innerHTML += rankingItem;
        rank++;
    });
});