const racesCollection = db.collection('races');
const rankingListContainer = document.getElementById('ranking-list');

racesCollection.orderBy('final_score', 'desc').limit(10).onSnapshot(querySnapshot => {
    rankingListContainer.innerHTML = '';

    let rank = 1;
    
    querySnapshot.forEach(doc => {
        const raceData = doc.data();

        // Define a classe e o ícone de coroa para o primeiro lugar
        const isFirstPlace = rank === 1;
        const itemClass = isFirstPlace ? 'ranking-item first-place' : 'ranking-item';
        const crownIcon = isFirstPlace ? '<span class="crown">👑</span>' : '';

        // Cria a nova estrutura HTML para cada item
        const rankingItem = `
            <div class="${itemClass}">
                <div class="rank-info-group">
                    <div class="rank-position">
                        ${crownIcon}
                        <span>${rank}</span>
                    </div>
                    <div class="player-info">
                        <span class="player-name">${raceData.playerName}</span>
                        <span class="player-attention">Atenção Média: ${raceData.average_attention}%</span>
                    </div>
                </div>
                <span class="player-score">${raceData.final_score.toLocaleString('pt-BR')} PTS</span>
            </div>
        `;
        
        rankingListContainer.innerHTML += rankingItem;
        rank++;
    });
});