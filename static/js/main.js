// Variables globales
let cartItems = JSON.parse(localStorage.getItem('cartItems')) || [];
let cartCount = cartItems.length;
let isChatOpen = false;
let chatMessages = [];
let favorites = JSON.parse(localStorage.getItem('favorites')) || [];

// API Base URL
const API_BASE_URL = window.location.origin;

// Funciones de utilidad
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    const toastId = 'toast-' + Date.now();
    
    const iconMap = {
        'success': 'bi-check-circle text-success',
        'error': 'bi-exclamation-circle text-danger',
        'info': 'bi-info-circle text-info',
        'warning': 'bi-exclamation-triangle text-warning'
    };
    
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert">
            <div class="toast-header">
                <i class="bi ${iconMap[type]} me-2"></i>
                <strong class="me-auto">Notificación</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    const toast = new bootstrap.Toast(document.getElementById(toastId));
    toast.show();
    
    // Remover el toast después de que se oculte
    setTimeout(() => {
        document.getElementById(toastId)?.remove();
    }, 5000);
}

// Funciones de navegación
function mostrarSeccion(id) {
    cerrarModal();
    setTimeout(() => {
        document.getElementById(id).classList.add('show');
    }, 100);
}

function cerrarModal() {
    document.querySelectorAll('.overlay').forEach(el => {
        el.classList.remove('show');
    });
}

function scrollToCatalog() {
    document.getElementById('catalogo').scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

// Funciones de filtrado de productos
function filterProducts(category) {
    const products = document.querySelectorAll('[data-category]');
    
    products.forEach(product => {
        if (category === 'all' || product.getAttribute('data-category') === category) {
            product.style.display = 'block';
            product.classList.add('fade-in');
        } else {
            product.style.display = 'none';
        }
    });

    // Actualizar título
    const title = document.querySelector('.section-title');
    switch(category) {
        case 'ofertas':
            title.textContent = 'OFERTAS ESPECIALES';
            break;
        case 'jardin':
            title.textContent = 'PRODUCTOS DE JARDÍN';
            break;
        default:
            title.textContent = 'TODOS LOS PRODUCTOS';
    }
}

// Funciones del carrito
function addToCart(productName, price, productId) {
    const existingItem = cartItems.find(item => item.id === productId);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cartItems.push({
            id: productId,
            name: productName,
            price: price,
            quantity: 1
        });
    }
    
    cartCount = cartItems.reduce((total, item) => total + item.quantity, 0);
    
    // Actualizar localStorage
    localStorage.setItem('cartItems', JSON.stringify(cartItems));
    
    // Actualizar UI
    document.getElementById('cartCount').textContent = cartCount;
    
    // Mostrar notificación
    showToast(${productName} agregado al carrito, 'success');
    
    // Animación del botón
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="bi bi-check2 me-1"></i>¡Agregado!';
    button.classList.add('btn-success');
    button.disabled = true;
    
    setTimeout(() => {
        button.innerHTML = originalText;
        button.classList.remove('btn-success');
        button.disabled = false;
    }, 2000);
}

function toggleCart() {
    if (cartItems.length === 0) {
        showToast('Tu carrito está vacío', 'info');
        return;
    }
    
    let cartHTML = '<h3>Carrito de Compras</h3><ul class="list-group">';
    let total = 0;
    
    cartItems.forEach(item => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;
        cartHTML += `
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <strong>${item.name}</strong><br>
                    <small>Cantidad: ${item.quantity} x $${item.price.toLocaleString()}</small>
                </div>
                <span class="badge bg-primary rounded-pill">$${itemTotal.toLocaleString()}</span>
            </li>
        `;
    });
    
    cartHTML += </ul><div class="mt-3"><strong>Total: $${total.toLocaleString()}</strong></div>;
    
    // Crear modal temporal para mostrar el carrito
    const cartModal = document.createElement('div');
    cartModal.className = 'overlay show';
    cartModal.innerHTML = `
        <div class="modal-card" style="max-width: 500px;">
            <button class="close-btn" onclick="this.closest('.overlay').remove()">&times;</button>
            ${cartHTML}
            <div class="mt-3">
                <button class="btn btn-success w-100 mb-2" onclick="checkout()">
                    <i class="bi bi-credit-card me-2"></i>Proceder al Pago
                </button>
                <button class="btn btn-outline-danger w-100" onclick="clearCart()">
                    <i class="bi bi-trash me-2"></i>Vaciar Carrito
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(cartModal);
}

function clearCart() {
    cartItems = [];
    cartCount = 0;
    localStorage.removeItem('cartItems');
    document.getElementById('cartCount').textContent = cartCount;
    document.querySelector('.overlay').remove();
    showToast('Carrito vaciado', 'info');
}

function checkout() {
    // Simular proceso de checkout
    showToast('Redirigiendo al proceso de pago...', 'info');
    document.querySelector('.overlay').remove();
    
    // Aquí podrías integrar con una pasarela de pago real
    setTimeout(() => {
        showToast('¡Gracias por tu compra! Procesando pedido...', 'success');
        clearCart();
    }, 2000);
}

// Funciones de favoritos
function toggleFavorite(button, productId) {
    const icon = button.querySelector('i');
    const isFavorite = favorites.includes(productId);
    
    if (isFavorite) {
        favorites = favorites.filter(id => id !== productId);
        icon.classList.remove('bi-heart-fill');
        icon.classList.add('bi-heart');
        button.style.color = '';
        showToast('Producto removido de favoritos', 'info');
    } else {
        favorites.push(productId);
        icon.classList.remove('bi-heart');
        icon.classList.add('bi-heart-fill');
        button.style.color = '#e74c3c';
        showToast('Producto agregado a favoritos', 'success');
    }
    
    localStorage.setItem('favorites', JSON.stringify(favorites));
}

// FUNCIONES DEL CHATBOT
function toggleChat() {
    const chatContainer = document.getElementById('chatContainer');
    const chatIcon = document.getElementById('chatIcon');
    const notification = document.getElementById('chatNotification');
    
    isChatOpen = !isChatOpen;
    
    if (isChatOpen) {
        chatContainer.classList.add('show');
        chatIcon.className = 'bi bi-x';
        notification.style.display = 'none';
        
        // Enfocar el input cuando se abre el chat
        setTimeout(() => {
            document.getElementById('chatInput').focus();
        }, 300);
    } else {
        chatContainer.classList.remove('show');
        chatIcon.className = 'bi bi-chat-dots';
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Agregar mensaje del usuario
    addMessageToChat(message, 'user');
    input.value = '';
    
    // Mostrar indicador de escritura
    showTypingIndicator();
    
    try {
        // Enviar mensaje al backend
        const response = await fetch(${API_BASE_URL}/api/chat, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }
        
        const data = await response.json();
        
        // Simular delay de respuesta
        setTimeout(() => {
            hideTypingIndicator();
            addMessageToChat(data.response, 'bot');
        }, 1000);
        
    } catch (error) {
        console.error('Error:', error);
        hideTypingIndicator();
        addMessageToChat('Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta de nuevo.', 'bot');
        showToast('Error al conectar con el chatbot', 'error');
    }
}

function sendQuickReply(message) {
    addMessageToChat(message, 'user');
    
    // Ocultar botones de respuesta rápida temporalmente
    document.getElementById('quickReplies').style.display = 'none';
    
    setTimeout(async () => {
        showTypingIndicator();
        
        try {
            const response = await fetch(${API_BASE_URL}/api/chat, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            setTimeout(() => {
                hideTypingIndicator();
                addMessageToChat(data.response, 'bot');
                // Mostrar botones de respuesta rápida nuevamente
                document.getElementById('quickReplies').style.display = 'flex';
            }, 1500);
            
        } catch (error) {
            console.error('Error:', error);
            hideTypingIndicator();
            addMessageToChat('Lo siento, hubo un error. Por favor, intenta de nuevo.', 'bot');
            document.getElementById('quickReplies').style.display = 'flex';
        }
    }, 500);
}

function addMessageToChat(message, sender) {
    const chatBody = document.getElementById('chatBody');
    const now = new Date();
    const time = now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    
    const messageDiv = document.createElement('div');
    messageDiv.className = message message-${sender};
    
    if (sender === 'bot') {
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="bi bi-robot"></i>
            </div>
            <div>
                <div class="message-content">${formatBotMessage(message)}</div>
                <div class="message-time">${time}</div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-content">${escapeHtml(message)}</div>
            <div class="message-time">${time}</div>
        `;
    }
    
    // Insertar antes del indicador de escritura
    const typingIndicator = document.getElementById('typingIndicator');
    chatBody.insertBefore(messageDiv, typingIndicator);
    
    // Scroll al final
    chatBody.scrollTop = chatBody.scrollHeight;
    
    // Guardar mensaje
    chatMessages.push({ message, sender, time });
}

function formatBotMessage(message) {
    // Convertir markdown básico a HTML
    return message
        .replace(/\\(.?)\\*/g, '<strong>$1</strong>')
        .replace(/\(.?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showTypingIndicator() {
    document.getElementById('typingIndicator').classList.add('show');
    const chatBody = document.getElementById('chatBody');
    chatBody.scrollTop = chatBody.scrollHeight;
}

function hideTypingIndicator() {
    document.getElementById('typingIndicator').classList.remove('show');
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Funciones de formularios
async function handleRegisterForm(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    // Validar contraseñas
    if (formData.get('password') !== formData.get('confirm_password')) {
        showToast('Las contraseñas no coinciden', 'error');
        return;
    }
    
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Registrando...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch(${API_BASE_URL}/api/register, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: formData.get('name'),
                email: formData.get('email'),
                phone: formData.get('phone'),
                address: formData.get('address')
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('¡Registro exitoso! Bienvenido a Casa en el Árbol', 'success');
            cerrarModal();
            form.reset();
        } else {
            showToast(data.error || 'Error al registrar usuario', 'error');
        }
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Error de conexión. Intenta de nuevo.', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Búsqueda en tiempo real
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const products = document.querySelectorAll('.product-card');
            
            products.forEach(card => {
                const title = card.querySelector('.product-title').textContent.toLowerCase();
                const description = card.querySelector('.product-description').textContent.toLowerCase();
                
                if (title.includes(searchTerm) || description.includes(searchTerm)) {
                    card.closest('.col').style.display = 'block';
                } else {
                    card.closest('.col').style.display = 'none';
                }
            });
        });
    }
}

// Auto-resize del textarea del chat
function initializeChatInput() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 80) + 'px';
        });
    }
}

// Inicialización de eventos
function initializeEventListeners() {
    // Cerrar modales con ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (isChatOpen) {
                toggleChat();
            } else {
                cerrarModal();
            }
        }
    });

    // Cerrar modales clickeando fuera
    document.querySelectorAll('.overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                cerrarModal();
            }
        });
    });

    // Formulario de registro
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegisterForm);
    }

    // Formulario de login (simulado)
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            showToast('Función de login en desarrollo', 'info');
            cerrarModal();
        });
    }

    // Formulario de recuperación (simulado)
    const recoveryForm = document.getElementById('recoveryForm');
    if (recoveryForm) {
        recoveryForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const successMessage = document.getElementById('recoverySuccessMessage');
            successMessage.classList.add('show');
            setTimeout(() => {
                successMessage.classList.remove('show');
                cerrarModal();
            }, 3000);
        });
    }
}

// Efectos visuales
function initializeAnimations() {
    // Observador para animaciones al hacer scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);

    // Observar elementos para animaciones
    document.querySelectorAll('.col[data-category]').forEach(el => {
        observer.observe(el);
    });

    // Efecto parallax en el navbar
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const navbar = document.querySelector('.navbar');
        
        if (navbar) {
            if (scrolled > 100) {
                navbar.style.background = 'rgba(255, 255, 255, 0.98)';
                navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.15)';
            } else {
                navbar.style.background = 'rgba(255, 255, 255, 0.95)';
                navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.08)';
            }
        }
    });
}

// Cargar favoritos al inicializar
function loadFavorites() {
    favorites.forEach(productId => {
        const favoriteBtn = document.querySelector([onclick*="${productId}"]);
        if (favoriteBtn) {
            const icon = favoriteBtn.querySelector('i');
            if (icon) {
                icon.classList.remove('bi-heart');
                icon.classList.add('bi-heart-fill');
                favoriteBtn.style.color = '#e74c3c';
            }
        }
    });
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Actualizar contador del carrito
    document.getElementById('cartCount').textContent = cartCount;
    
    // Configurar hora del mensaje de bienvenida del chat
    const now = new Date();
    const welcomeTime = now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    const welcomeTimeElement = document.getElementById('welcomeTime');
    if (welcomeTimeElement) {
        welcomeTimeElement.textContent = welcomeTime;
    }

    // Mostrar notificación del chat después de 5 segundos
    setTimeout(() => {
        if (!isChatOpen) {
            const notification = document.getElementById('chatNotification');
            const toggleBtn = document.getElementById('chatToggleBtn');
            if (notification && toggleBtn) {
                notification.style.display = 'block';
                toggleBtn.classList.add('has-notification');
            }
        }
    }, 5000);

    // Inicializar componentes
    initializeEventListeners();
    initializeSearch();
    initializeChatInput();
    initializeAnimations();
    loadFavorites();

    // Mostrar elementos con delay para mejor UX
    setTimeout(() => {
        document.querySelectorAll('.fade-in').forEach((el, index) => {
            setTimeout(() => {
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }, 300);
});

// Exportar funciones globales para uso en HTML
window.mostrarSeccion = mostrarSeccion;
window.cerrarModal = cerrarModal;
window.scrollToCatalog = scrollToCatalog;
window.filterProducts = filterProducts;
window.addToCart = addToCart;
window.toggleCart = toggleCart;
window.toggleFavorite = toggleFavorite;
window.toggleChat = toggleChat;
window.sendMessage = sendMessage;
window.sendQuickReply = sendQuickReply;
window.handleChatKeyPress = handleChatKeyPress;
window.clearCart = clearCart;
window.checkout = checkout;

document.addEventListener('DOMContentLoaded', function () {
  var form = document.getElementById('chat-form');
  var input = document.getElementById('chat-input');
  var box = document.getElementById('chat-box');
  if (form && input && box) {
    form.addEventListener('submit', async function (e) {
      e.preventDefault();
      const msg = input.value.trim();
      if (!msg) return;
      append('Tú', msg); input.value = '';
      try {
        const r = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message: msg})});
        const data = await r.json();
        append('Bot', data.reply || '...');
      } catch { append('Bot', 'Error de conexión.'); }
    });
  }
  function append(who, text){
    const div = document.createElement('div'); div.className='msg'; div.textContent = who + ': ' + text;
    document.getElementById('chat-box').appendChild(div);
  }
});
