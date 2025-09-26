// Espera todo o conteúdo da página carregar antes de executar o código
document.addEventListener('DOMContentLoaded', () => {

    // --- DADOS DE EXEMPLO (MOCK) ---
    // No futuro, estes dados virão da sua corrida ou da API.
    const dadosJogador1 = {
        nome: "Ester Silva",
        pontos: 9850,
        // URL que será embutida no QR Code
        url: "https://tavares-fiap.github.io/NeuroRace/resultados.html?player=Ester" 
    };
    const dadosJogador2 = {
        nome: "João Victor",
        pontos: 9540,
        // URL que será embutida no QR Code
        url: "https://tavares-fiap.github.io/NeuroRace/resultados.html?player=Joao"
    };
    // ---------------------------------

    // Atualiza os nomes e as pontuações na tela com os dados de exemplo
    document.getElementById('p1-name').textContent = dadosJogador1.nome;
    document.getElementById('p1-score').textContent = dadosJogador1.pontos;
    document.getElementById('p2-name').textContent = dadosJogador2.nome;
    document.getElementById('p2-score').textContent = dadosJogador2.pontos;

    // Pega os 'divs' que servirão de container para os QR Codes
    const qrcodeContainer1 = document.getElementById("qrcode-p1");
    const qrcodeContainer2 = document.getElementById("qrcode-p2");

    // --- GERAÇÃO DOS QR CODES ---
    // Verifica se os containers existem antes de tentar gerar os códigos
    if (qrcodeContainer1 && qrcodeContainer2) {
        
        // Limpa os containers caso já tenham algo dentro (boa prática)
        qrcodeContainer1.innerHTML = "";
        qrcodeContainer2.innerHTML = "";

        // Usa a biblioteca QRCode.js para gerar um QR Code para cada jogador
        new QRCode(qrcodeContainer1, {
            text: dadosJogador1.url,
            width: 128,
            height: 128,
            colorDark: "#000000",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });

        new QRCode(qrcodeContainer2, {
            text: dadosJogador2.url,
            width: 128,
            height: 128,
            colorDark: "#000000",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });
    }
});