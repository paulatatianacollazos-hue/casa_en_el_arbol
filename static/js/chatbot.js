// JavaScript para el chatbot de Casa en el Árbol
class ChatbotManager {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.sessionId = null;
        this.messageHistory = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.typingTimeout = null;
        this.lastActivity = Date.now();
        
        this.initializeChat();
    }

    initializeChat() {
        console.log('Inicializando chatbot...');
        this.connectToServer();
        this.setupEventListeners();
        this.setupHeartbeat();
    }

    connectToServer() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                timeout: 10000,
                reconnection: true,
                reconnectionAttempts: this.maxReconnectAttempts,
                reconnectionDelay: 1000
            });

            this.setupSocketEvents();
        } catch (error) {
            console.error('Error conectando al servidor:', error);
            this.handleConnectionError();
        }
    }

    setupSocketEvents() {
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.sessionId = this.socket.id;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
            console.log('Conectado al servidor de chat:', this.sessionId);
        });

        this.socket.on('disconnect', (reason) => {
            this.isConnected = false;
            this.updateConnectionStatus(false);
            console.log('Desconectado del servidor:', reason);
            
            if (reason === 'io server disconnect') {
                // El servidor desconectó al cliente, reconectar manualmente
                this.socket.connect();
            }
        });

        this.socket.on('connect_error', (error) => {
            console.error('Error de conexión:', error);
            this.handleConnectionError();
        });

        this.socket.on('bot_message', (data) => {
            this.handleBotMessage(data);
        });

        this.socket.on('typing_start', () => {
            this.showTypingIndicator();
        });

        this.socket.on('typing_stop', () => {
            this.hideTypingIndicator();
        });

        this.socket.on('reconnect', (attemptNumber) => {
            console.log('Reconectado después de', attemptNumber, 'intentos');
            this.showNotification('Conexión restaurada', 'El chat se ha reconectado correctamente.');
        });
    }

    setupEventListeners() {
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('chatSendBtn');

        // Auto-resize del textarea
        chatInput.addEventListener('input', (e) => {
            this.handleInputChange(e);
        });

        // Manejar teclas
        chatInput.addEventListener('keydown', (e) => {
            this.handleKeyDown(e);
        });

        // Prevenir envío de formulario
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Click en botón de envío
        sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        // Detectar actividad del usuario
        document.addEventListener('click', () => {
            this.updateActivity();
        });

        document.addEventListener('keypress', () => {
            this.updateActivity();
        });
    }

    handleInputChange(e) {
        const input = e.target;
        const sendBtn = document.getElementById('chatSendBtn');
        const charCount = document.getElementById('charCount');

        // Auto-resize
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';

        // Actualizar contador de caracteres
        const count = input.value.length;
        charCount.textContent = count;

        // Actualizar estilo del contador
        if (count > 450) {
            charCount.className = 'text-warning';
        } else if (count > 500) {
            charCount.className = 'text-danger';
        } else {
            charCount.className = 'text-muted';
        }

        // Habilitar/deshabilitar botón de envío
        const canSend = this.isConnected && count > 0 && count <= 500;
        sendBtn.disabled = !canSend;

        // Indicador de escritura (opcional para futuras mejoras)
        this.handleTypingIndicator();
    }

    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        } else if (e.key === 'Escape') {
            e.target.blur();
        }
    }

    handleTypingIndicator() {
        // Limpiar timeout anterior
        clearTimeout(this.typingTimeout);
        
        // Aquí podrías emitir evento de "usuario escribiendo"
        // this.socket.emit('user_typing', { typing: true });
        
        this.typingTimeout = setTimeout(() => {
            // this.socket.emit('user_typing', { typing: false });
        }, 1000);
    }

    sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();

        if (!message || !this.isConnected) {
            return;
        }

        if (message.length > 500) {
            this.showNotification('Mensaje muy largo', 'El mensaje no puede exceder 500 caracteres.');
            return;
        }

        try {
            // Agregar mensaje del usuario al chat
            this.addMessageToChat(message, 'user');

            // Enviar mensaje al servidor
            this.socket.emit('user_message', { message: message });

            // Limpiar input
            this.clearInput();

            // Actualizar actividad
            this.updateActivity();

        } catch (error) {
            console.error('Error enviando mensaje:', error);
            this.showNotification('Error', 'No se pudo enviar el mensaje. Intenta de nuevo.');
        }
    }

    sendQuickReply(reply) {
        if (!this.isConnected) {
            this.showNotification('Sin conexión', 'No hay conexión al servidor.');
            return;
        }

        try {
            // Agregar como mensaje del usuario
            this.addMessageToChat(reply, 'user');

            // Enviar al servidor
            this.socket.emit('quick_reply', { reply: reply });

            // Limpiar respuestas rápidas
            this.updateQuickReplies([]);

        } catch (error) {
            console.error('Error enviando respuesta rápida:', error);
        }
    }

    addMessageToChat(message, sender, timestamp = null) {
        const chatBody = document.getElementById('chatBody');
        const typingIndicator = document.getElementById('typingIndicator');
        const now = timestamp || new Date().toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${sender}`;

        if (sender === 'bot') {
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <i class="bi bi-robot"></i>
                </div>
                <div class="message-wrapper">
                    <div class="message-content">${this.formatMessage(message)}</div>
                    <div class="message-time">${now}</div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-wrapper">
                    <div class="message-content">${this.formatMessage(message)}</div>
                    <div class="message-time">${now}</div>
                </div>
            `;
        }

        // Insertar antes del indicador de escritura
        chatBody.insertBefore(messageDiv, typingIndicator);

        // Scroll al final con animación suave
        this.scrollToBottom();

        // Guardar en historial
        this.messageHistory.push({ 
            message, 
            sender, 
            timestamp: now,
            id: Date.now() + Math.random()
        });

        // Verificar si la página está oculta para notificaciones
        if (sender === 'bot' && document.hidden) {
            this.showBrowserNotification('Nuevo mensaje', message.substring(0, 100));
        }
    }

    formatMessage(message) {
        // Formatear markdown básico y emojis
        return message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/~~(.*?)~~/g, '<del>$1</del>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>')
            .replace(/•/g, '•'); // Mantener bullets
    }

    handleBotMessage(data) {
        this.addMessageToChat(data.text, 'bot', data.timestamp);

        if (data.quick_replies && data.quick_replies.length > 0) {
            this.updateQuickReplies(data.quick_replies);
        }

        if (data.suggestions && data.suggestions.length > 0) {
            console.log('Sugerencias recibidas:', data.suggestions);
            // Aquí podrías implementar lógica para mostrar sugerencias
        }
    }

    updateQuickReplies(replies) {
        const container = document.getElementById('quickReplies');
        container.innerHTML = '';

        replies.forEach(reply => {
            const button = document.createElement('button');
            button.className = 'quick-reply-btn';
            button.textContent = reply;
            button.onclick = () => this.sendQuickReply(reply);
            
            // Agregar animación de entrada
            button.style.opacity = '0';
            button.style.transform = 'translateY(10px)';
            container.appendChild(button);
            
            // Animar entrada
            setTimeout(() => {
                button.style.opacity = '1';
                button.style.transform = 'translateY(0)';
            }, 100);
        });
    }

    showTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        indicator.classList.add('show');
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        indicator.classList.remove('show');
    }

    updateConnectionStatus(connected) {
        const statusIndicator = document.getElementById('connectionStatus');
        const statusText = document.getElementById('statusText');
        const sendBtn = document.getElementById('chatSendBtn');
        const connectedUsers = document.getElementById('connectedUsers');

        if (connected) {
            statusIndicator.className = 'status-indicator connected';
            statusText.textContent = 'En línea - Respuesta inmediata';
            sendBtn.disabled = false;
            
            // Simular usuarios conectados (en una app real esto vendría del servidor)
            connectedUsers.textContent = Math.floor(Math.random() * 15) + 1;
        } else {
            statusIndicator.className = 'status-indicator disconnected';
            statusText.textContent = 'Desconectado - Reconectando...';
            sendBtn.disabled = true;
            connectedUsers.textContent = '0';
        }
    }

    handleConnectionError() {
        this.reconnectAttempts++;
        
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.showConnectionError();
        } else {
            setTimeout(() => {
                console.log(`Intento de reconexión ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
                this.connectToServer();
            }, 2000 * this.reconnectAttempts);
        }
    }

    showConnectionError() {
        const chatBody = document.getElementById('chatBody');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <i class="bi bi-exclamation-triangle me-2"></i>
            No se pudo conectar al servidor de chat.
            <br>
            <button class="retry-btn" onclick="chatbot.retryConnection()">
                <i class="bi bi-arrow-clockwise me-1"></i>Reintentar
            </button>
        `;
        
        chatBody.appendChild(errorDiv);
        this.scrollToBottom();
    }

    retryConnection() {
        this.reconnectAttempts = 0;
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        this.connectToServer();
    }

    clearInput() {
        const input = document.getElementById('chatInput');
        const charCount = document.getElementById('charCount');
        const sendBtn = document.getElementById('chatSendBtn');

        input.value = '';
        input.style.height = 'auto';
        charCount.textContent = '0';
        charCount.className = 'text-muted';
        sendBtn.disabled = true;
    }

    scrollToBottom(smooth = true) {
        const chatBody = document.getElementById('chatBody');
        
        if (smooth) {
            chatBody.scrollTo({
                top: chatBody.scrollHeight,
                behavior: 'smooth'
            });
        } else {
            chatBody.scrollTop = chatBody.scrollHeight;
        }
    }

    clearChat() {
        if (confirm('¿Estás seguro de que quieres limpiar la conversación?')) {
            const chatBody = document.getElementById('chatBody');
            const typingIndicator = document.getElementById('typingIndicator');

            // Limpiar mensajes pero mantener el indicador de escritura
            const messages = chatBody.querySelectorAll('.message');
            messages.forEach(msg => msg.remove());

            // Limpiar respuestas rápidas
            this.updateQuickReplies([]);

            // Limpiar historial local
            this.messageHistory = [];

            // Notificar al servidor
            if (this.isConnected && this.sessionId) {
                fetch(`/api/chat/clear/${this.sessionId}`, { method: 'POST' })
                    .catch(error => console.error('Error limpiando chat en servidor:', error));
            }

            this.showNotification('Conversación limpiada', 'La conversación se ha reiniciado correctamente.');
        }
    }

    exportChat() {
        if (this.messageHistory.length === 0) {
            this.showNotification('Sin mensajes', 'No hay conversación para exportar.');
            return;
        }

        const chatData = {
            session_id: this.sessionId,
            export_timestamp: new Date().toISOString(),
            messages: this.messageHistory,
            total_messages: this.messageHistory.length,
            export_version: '1.0'
        };

        const blob = new Blob([JSON.stringify(chatData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-casa-arbol-${Date.now()}.json`;
        a.style.display = 'none';
        
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showNotification('Exportado', 'Conversación exportada correctamente.');
    }

    showNotification(title, message, type = 'info') {
        const toastElement = document.getElementById('notificationToast');
        const toastBody = document.getElementById('toastBody');
        const toastTime = document.getElementById('toastTime');
        
        // Actualizar contenido
        toastBody.textContent = message;
        toastTime.textContent = new Date().toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        // Cambiar icono según el tipo
        const icon = toastElement.querySelector('.toast-header i');
        switch(type) {
            case 'success':
                icon.className = 'bi bi-check-circle text-success me-2';
                break;
            case 'error':
                icon.className = 'bi bi-exclamation-triangle text-danger me-2';
                break;
            case 'warning':
                icon.className = 'bi bi-exclamation-circle text-warning me-2';
                break;
            default:
                icon.className = 'bi bi-info-circle text-primary me-2';
        }

        const toast = new bootstrap.Toast(toastElement);
        toast.show();
    }

    showBrowserNotification(title, body) {
        if ('Notification' in window && 
            Notification.permission === 'granted' && 
            window.chatNotificationsEnabled) {
            
            try {
                new Notification(title, {
                    body: body,
                    icon: '/static/favicon.ico',
                    tag: 'chatbot-notification',
                    silent: false
                });
            } catch (error) {
                console.error('Error mostrando notificación:', error);
            }
        }
    }

    setupHeartbeat() {
        // Enviar ping cada 30 segundos para mantener conexión
        setInterval(() => {
            if (this.isConnected) {
                this.socket.emit('ping');
            }
        }, 30000);

        // Verificar inactividad del usuario
        setInterval(() => {
            const now = Date.now();
            const timeSinceActivity = now - this.lastActivity;
            
            // Si han pasado 5 minutos sin actividad
            if (timeSinceActivity > 300000 && this.messageHistory.length > 0 && this.isConnected) {
                this.addMessageToChat(
                    '¿Hay algo más en lo que pueda ayudarte? 😊', 
                    'bot'
                );
                this.updateActivity(); // Reset timer
            }
        }, 60000); // Verificar cada minuto
    }

    updateActivity() {
        this.lastActivity = Date.now();
    }

    // Métodos de utilidad
    getSessionStats() {
        return {
            sessionId: this.sessionId,
            isConnected: this.isConnected,
            messageCount: this.messageHistory.length,
            userMessages: this.messageHistory.filter(m => m.sender === 'user').length,
            botMessages: this.messageHistory.filter(m => m.sender === 'bot').length,
            lastActivity: new Date(this.lastActivity).toISOString()
        };
    }

    downloadChatHistory() {
        // Método alternativo para descargar historial en formato texto
        if (this.messageHistory.length === 0) {
            this.showNotification('Sin mensajes', 'No hay conversación para descargar.');
            return;
        }

        let textContent = `CONVERSACIÓN - CASA EN EL ÁRBOL\n`;
        textContent += `Fecha: ${new Date().toLocaleDateString('es-ES')}\n`;
        textContent += `Sesión ID: ${this.sessionId}\n`;
        textContent += `Total de mensajes: ${this.messageHistory.length}\n\n`;
        textContent += '='.repeat(50) + '\n\n';

        this.messageHistory.forEach(msg => {
            const sender = msg.sender === 'user' ? 'TÚ' : 'ASISTENTE';
            textContent += `[${msg.timestamp}] ${sender}: ${msg.message}\n\n`;
        });

        const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversacion-casa-arbol-${Date.now()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Inicializar el chatbot cuando se cargue la página
let chatbot;

document.addEventListener('DOMContentLoaded', function() {
    chatbot = new ChatbotManager();
    
    // Funciones globales para compatibilidad
    window.sendMessage = () => chatbot.sendMessage();
    window.sendQuickReply = (reply) => chatbot.sendQuickReply(reply);
    window.clearChat = () => chatbot.clearChat();
    window.exportChat = () => chatbot.exportChat();
    
    // Solicitar permisos de notificación después de 3 segundos
    setTimeout(() => {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    console.log('Notificaciones habilitadas');
                }
            });
        }
    }, 3000);

    // Manejar visibilidad de la página
    document.addEventListener('visibilitychange', function() {
        window.chatNotificationsEnabled = document.hidden;
    });

    // Agregar indicador de estado de la aplicación
    window.addEventListener('online', () => {
        chatbot.showNotification('Conexión restaurada', 'Ya tienes conexión a internet.', 'success');
    });

    window.addEventListener('offline', () => {
        chatbot.showNotification('Sin conexión', 'Se perdió la conexión a internet.', 'error');
    });
});

// Funciones de utilidad adicionales
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

function toggleFullscreen() {
    const chatContainer = document.getElementById('chatContainer');
    
    if (chatContainer.classList.contains('fullscreen')) {
        chatContainer.classList.remove('fullscreen');
    } else {
        chatContainer.classList.add('fullscreen');
    }
}

// Funciones de análisis (para futuras mejoras)
function trackChatEvent(event, data = {}) {
    console.log('Chat Event:', event, data);
    
    // Aquí podrías integrar con Google Analytics o similar
    if (typeof gtag !== 'undefined') {
        gtag('event', event, {
            event_category: 'Chatbot',
            event_label: JSON.stringify(data),
            custom_map: {'custom_parameter_1': 'session_id'}
        });
    }
}

// Manejo de errores globales
window.addEventListener('error', function(e) {
    console.error('Error en la aplicación:', e.error);
    
    if (chatbot) {
        chatbot.showNotification(
            'Error inesperado', 
            'Se produjo un error. La página se recargará automáticamente.', 
            'error'
        );
        
        // Recargar página después de 5 segundos
        setTimeout(() => {
            window.location.reload();
        }, 5000);
    }
});

// Prevenir envío accidental al recargar
window.addEventListener('beforeunload', function(e) {
    if (chatbot && chatbot.messageHistory.length > 0) {
        const message = '¿Estás seguro de que quieres salir? Se perderá la conversación.';
        e.returnValue = message;
        return message;
    }
});

// Compatibilidad con navegadores antiguos
if (!window.console) {
    window.console = {
        log: function() {},
        error: function() {},
        warn: function() {}
    };
}