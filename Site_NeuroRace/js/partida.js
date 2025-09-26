// Espera o conteúdo da página carregar
document.addEventListener('DOMContentLoaded', () => {
    // Seleciona os elementos da página
    const startRaceBtn = document.getElementById('start-race-btn');
    const p1PhoneInput = document.getElementById('p1-phone');
    const p2PhoneInput = document.getElementById('p2-phone');
    const statusMessage = document.getElementById('status-message');

    // Adiciona o evento de clique ao botão
    startRaceBtn.addEventListener('click', async () => {
        // Pega os números de telefone dos inputs
        const p1Phone = p1PhoneInput.value;
        const p2Phone = p2PhoneInput.value;

        // --- Validação no Front-end ---
        if (!validatePhone(p1Phone) || !validatePhone(p2Phone)) {
            statusMessage.textContent = 'Formato de telefone inválido. Use (00) 9 0000-0000.';
            return; // Para a execução se o formato for inválido
        }

        // --- Verificação no Back-end ---
        statusMessage.textContent = 'Verificando jogadores...';
        startRaceBtn.disabled = true; // Desabilita o botão para evitar múltiplos cliques

        try {
            // Prepara as duas chamadas de API
            const promiseP1 = fetch(`URL_DA_API_DO_JOAO/players/search?phone=${encodeURIComponent(p1Phone)}`);
            const promiseP2 = fetch(`URL_DA_API_DO_JOAO/players/search?phone=${encodeURIComponent(p2Phone)}`);

            // Executa as duas chamadas ao mesmo tempo e espera a resposta de ambas
            const responses = await Promise.all([promiseP1, promiseP2]);

            // Verifica se alguma das respostas deu erro (ex: jogador não encontrado)
            for (const response of responses) {
                if (!response.ok) {
                    throw new Error('Um ou mais jogadores não foram encontrados.');
                }
            }

            // Se ambas as respostas foram OK, extrai os dados JSON
            const [player1Data, player2Data] = await Promise.all(responses.map(res => res.json()));

            // --- Sucesso! Armazena os dados e navega ---
            statusMessage.textContent = 'Jogadores encontrados! Iniciando...';

            // Guarda os dados dos jogadores no localStorage para usar na próxima página
            localStorage.setItem('player1', JSON.stringify(player1Data));
            localStorage.setItem('player2', JSON.stringify(player2Data));

            // Redireciona para a página de início da corrida
            window.location.href = 'iniciando-corrida.html';

        } catch (error) {
            // Em caso de erro, exibe a mensagem e reabilita o botão
            statusMessage.textContent = error.message;
            startRaceBtn.disabled = false;
        }
    });

    // Aplica a máscara de telefone aos inputs (requer validation.js)
    if (typeof applyPhoneMask === 'function') {
        p1PhoneInput.addEventListener('input', applyPhoneMask);
        p2PhoneInput.addEventListener('input', applyPhoneMask);
    }
});