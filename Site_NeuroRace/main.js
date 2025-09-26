document.addEventListener('DOMContentLoaded', function() {
    // ---- LÓGICA PARA MARCAR LINK ATIVO NO MENU (VERSÃO CORRIGIDA E FINAL) ----
    const navLinks = document.querySelectorAll('.site-nav a');
    const currentPagePath = window.location.pathname;

    navLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname;

        if (currentPagePath === linkPath) {
            link.classList.add('active');
        }

        if (currentPagePath === '/' && linkPath.endsWith('/index.html')) {
            link.classList.add('active');
        }
    });

    // ---- LÓGICA PARA MENU MOBILE ----
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const closeBtn = document.getElementById('close-btn');

    if (hamburgerBtn && mobileMenu && closeBtn) {
        hamburgerBtn.addEventListener('click', () => {
            mobileMenu.classList.add('active');
        });

        closeBtn.addEventListener('click', () => {
            mobileMenu.classList.remove('active');
        });

        const mobileNavLinks = mobileMenu.querySelectorAll('a');
        mobileNavLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileMenu.classList.remove('active');
            });
        });
    }
});