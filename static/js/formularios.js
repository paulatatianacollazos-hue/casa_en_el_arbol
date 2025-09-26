document.addEventListener('DOMContentLoaded', function() {
    
    const overlay = document.querySelector('.auth-overlay');

    
    overlay.style.display = 'flex';

   
    const closeBtn = document.getElementById('close-login-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            overlay.style.display = 'none';
        });
    }
});
