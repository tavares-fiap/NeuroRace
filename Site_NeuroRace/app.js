// --- LÓGICA PARA PÁGINA DE CADASTRO (acesso.html) ---

// Adiciona o listener de evento para o formulário de registro
const registerForm = document.getElementById('register-form');
if (registerForm) {
    registerForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Previne o recarregamento da página

        // Seleciona os elementos do formulário
        const nameInput = document.getElementById('reg-name');
        const phoneInput = document.getElementById('reg-phone');
        const nameError = document.getElementById('name-error');
        const phoneError = document.getElementById('phone-error');
        const statusMessage = document.getElementById('register-status');

        // Limpa mensagens de erro e status anteriores
        nameError.textContent = '';
        phoneError.textContent = '';
        statusMessage.textContent = '';
        nameInput.style.borderColor = 'var(--border-color)';
        phoneInput.style.borderColor = 'var(--border-color)';

        // Pega os valores e valida (assumindo que validation.js está carregado)
        const nameValue = nameInput.value.trim();
        const phoneValue = phoneInput.value;
        let isValid = true;

        if (!validateName(nameValue)) {
            nameError.textContent = 'Nome inválido. Use apenas letras e espaços.';
            nameInput.style.borderColor = 'var(--neon-pink)';
            isValid = false;
        }

        if (!validatePhone(phoneValue)) {
            phoneError.textContent = 'Telefone inválido. O formato deve ser (00) 9 0000-0000.';
            phoneInput.style.borderColor = 'var(--neon-pink)';
            isValid = false;
        }

        if (!isValid) return; // Se a validação falhar, para a execução

        statusMessage.textContent = 'Cadastrando...';
        
        // --- INTEGRAÇÃO COM O BACK-END (API) ---
        try {
            // O código antigo que falava com o Firestore foi removido.
            // No lugar dele, entrará a chamada para a API do João usando fetch.
            
            /*
            // DESCOMENTE E AJUSTE ESTE BLOCO QUANDO TIVER A URL DO JOÃO
            const response = await fetch('URL_DA_API_DO_JOAO/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    fullName: nameValue,
                    phone: phoneValue
                })
            });

            if (!response.ok) {
                // Se a API retornar um erro (ex: telefone já existe), ele será capturado aqui
                const errorResult = await response.json();
                throw new Error(errorResult.error || 'Erro no servidor. Tente novamente.');
            }

            const result = await response.json();
            console.log('Resposta do servidor:', result);
            */

            // SIMULAÇÃO DE SUCESSO PARA TESTES (remover após integrar de verdade)
            await new Promise(resolve => setTimeout(resolve, 1000)); // Simula espera da rede
            
            // Exibe mensagem de sucesso
            statusMessage.style.color = 'var(--neon-cyan)';
            statusMessage.textContent = 'Cadastro realizado com sucesso!';
            registerForm.reset();

        } catch (error) {
            console.error("Erro ao cadastrar:", error);
            statusMessage.textContent = error.message || 'Erro ao cadastrar. Tente novamente.';
        }
    });
}