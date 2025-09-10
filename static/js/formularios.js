document.addEventListener('DOMContentLoaded', function() {
    // Aquí tu código que manipula la página
    const overlay = document.querySelector('.auth-overlay');

    // Ejemplo: abrir overlay automáticamente
    overlay.style.display = 'flex';

    // Cerrar overlay con botón si lo tienes
    const closeBtn = document.getElementById('close-login-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            overlay.style.display = 'none';
        });
    }
});
