const API_BASE_URL = "http://127.0.0.1:5000";

// Toast Notification
function showToast(message, type = "info") {
    const toastContainer = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast align-items-center text-bg-${type} border-0 show mb-2`;
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto"
                data-bs-dismiss="toast"></button>
        </div>
    `;
    toastContainer.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Cart Functions
function addToCart(productId, productName, productPrice) {
    let cart = JSON.parse(localStorage.getItem("cart")) || [];
    const existingProduct = cart.find(item => item.id === productId);

    if (existingProduct) {
        existingProduct.quantity++;
    } else {
        cart.push({ id: productId, name: productName, price: productPrice, quantity: 1 });
    }

    localStorage.setItem("cart", JSON.stringify(cart));
    updateCartCount();
    showToast(`${productName} agregado al carrito`, "success");
}

function updateCartCount() {
    const cart = JSON.parse(localStorage.getItem("cart")) || [];
    const count = cart.reduce((acc, item) => acc + item.quantity, 0);
    document.getElementById("cart-count").textContent = count;
}

function toggleCart() {
    const cart = JSON.parse(localStorage.getItem("cart")) || [];
    let cartHTML = "<ul class='list-group'>";
    let total = 0;

    cart.forEach(item => {
        total += item.price * item.quantity;
        cartHTML += `
            <li class="list-group-item d-flex justify-content-between align-items-center">
                ${item.name} (x${item.quantity})
                <span>$${(item.price * item.quantity).toLocaleString()}</span>
            </li>`;
    });

    cartHTML += `</ul><div class="mt-3"><strong>Total: $${total.toLocaleString()}</strong></div>`;

    document.getElementById("cart-items").innerHTML = cartHTML;
    new bootstrap.Modal(document.getElementById("cartModal")).show();
}

// Favorites Functions
function toggleFavorite(productId, productName) {
    let favorites = JSON.parse(localStorage.getItem("favorites")) || [];
    const index = favorites.indexOf(productId);

    if (index > -1) {
        favorites.splice(index, 1);
        showToast(`${productName} eliminado de favoritos`, "warning");
    } else {
        favorites.push(productId);
        showToast(`${productName} agregado a favoritos`, "success");
    }

    localStorage.setItem("favorites", JSON.stringify(favorites));
    updateFavoriteUI(productId);
}

function updateFavoriteUI(productId) {
    const favoriteBtn = document.querySelector(`[onclick*="${productId}"]`);
    if (!favoriteBtn) return;

    let favorites = JSON.parse(localStorage.getItem("favorites")) || [];
    favoriteBtn.classList.toggle("btn-danger", favorites.includes(productId));
}

function loadFavorites() {
    let favorites = JSON.parse(localStorage.getItem("favorites")) || [];
    favorites.forEach(id => updateFavoriteUI(id));
}

// Chatbot Functions
async function sendMessage() {
    const input = document.getElementById("user-input");
    const message = input.value.trim();
    if (!message) return;

    addMessageToChat("user", message);
    input.value = "";

    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });

        const data = await response.json();
        addMessageToChat("bot", formatBotMessage(data.reply));
    } catch (error) {
        addMessageToChat("bot", "Error: No se pudo conectar con el servidor.");
    }
}

function addMessageToChat(sender, message) {
    const chatMessages = document.getElementById("chat-messages");
    const messageDiv = document.createElement("div");
    messageDiv.className = `message message-${sender}`;
    messageDiv.innerHTML = message;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatBotMessage(message) {
    return message
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")  // **texto**
        .replace(/\*(.*?)\*/g, "<em>$1</em>")              // *texto*
        .replace(/\n/g, "<br>");                           // saltos de línea
}

// Toggle Chatbot
function toggleChatbot() {
    const chatbot = document.getElementById("chatbot");
    chatbot.style.display = chatbot.style.display === "none" ? "flex" : "none";
}

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    updateCartCount();
    loadFavorites();
});
