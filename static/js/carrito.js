// =========================
//   CARRITO LATERAL
// =========================

// Cargar carrito desde localStorage (si existe)
let cart = JSON.parse(localStorage.getItem('cart')) || [];

// =========================
//   MOSTRAR / OCULTAR PANEL
// =========================
function toggleCart() {
  document.getElementById('cart-panel').classList.toggle('active');
}

// =========================
//   AGREGAR DESDE BOTÓN
// =========================
function addToCartFromButton(btn) {
  const product = {
    id: btn.dataset.id,
    name: btn.dataset.name,
    price: parseFloat(btn.dataset.price),
    image: btn.dataset.image,
    material: btn.dataset.material
  };
  addToCart(product);
}

// =========================
//   AGREGAR AL CARRITO
// =========================
function addToCart(product) {
  const exists = cart.find(p => p.id === product.id);
  if (exists) {
    alert("⚠️ Este producto ya está en tu carrito.");
    return;
  }

  cart.push(product);
  localStorage.setItem('cart', JSON.stringify(cart));
  updateCartUI();
  showCartNotification(product.name);
}

// =========================
//   ACTUALIZAR INTERFAZ
// =========================
function updateCartUI() {
  const count = document.getElementById('cart-count');
  const itemsContainer = document.getElementById('cart-items');

  if (count) count.textContent = cart.length;

  if (!itemsContainer) return;

  if (cart.length === 0) {
    itemsContainer.innerHTML = `<p class="text-muted text-center mt-3">🛒 Tu carrito está vacío</p>`;
    return;
  }

  itemsContainer.innerHTML = cart.map(p => `
    <div class="cart-item d-flex align-items-center border-bottom py-2" onclick="showProductDetail('${p.id}')">
      <img src="${p.image}" alt="${p.name}" 
           class="me-2" style="width:60px; height:60px; object-fit:cover; border-radius:8px;">
      <div class="flex-grow-1">
        <strong>${p.name}</strong><br>
        <span class="text-muted">$${p.price.toFixed(2)}</span>
      </div>
      <button class="btn btn-sm btn-outline-danger ms-2" 
              onclick="removeFromCart('${p.id}'); event.stopPropagation();">
        <i class="bi bi-trash"></i>
      </button>
    </div>
  `).join('');
}

// =========================
//   ELIMINAR PRODUCTO
// =========================
function removeFromCart(id) {
  cart = cart.filter(p => p.id !== id);
  localStorage.setItem('cart', JSON.stringify(cart));
  updateCartUI();
}

// =========================
//   MOSTRAR DETALLE
// =========================
function showProductDetail(id) {
  const product = cart.find(p => p.id === id);
  if (!product) return;

  alert(`📦 ${product.name}\n💲${product.price}\n🪵 Material: ${product.material}`);
}

// =========================
//   CHECKOUT (SIMULADO)
// =========================
function checkoutCart() {
  if (cart.length === 0) {
    alert("Tu carrito está vacío.");
    return;
  }

  alert("🛒 Procesando compra...");
  // Aquí podrías redirigir a una página de pago o limpiar el carrito
}

// =========================
//   NOTIFICACIÓN VISUAL
// =========================
function showCartNotification(productName) {
  const notif = document.createElement("div");
  notif.textContent = `✅ ${productName} agregado al carrito`;
  notif.className = "cart-toast";
  document.body.appendChild(notif);
  setTimeout(() => notif.remove(), 2000);
}

// =========================
//   INICIALIZAR AL CARGAR
// =========================
document.addEventListener('DOMContentLoaded', updateCartUI);

// =========================
//   ESTILOS BÁSICOS
// =========================
const style = document.createElement("style");
style.textContent = `
.cart-panel {
  position: fixed;
  top: 0;
  right: -400px;
  width: 350px;
  height: 100vh;
  background: #fff;
  box-shadow: -2px 0 10px rgba(0,0,0,0.1);
  transition: right 0.3s ease;
  z-index: 1050;
  display: flex;
  flex-direction: column;
}
.cart-panel.active { right: 0; }

.cart-toast {
  position: fixed;
  bottom: 30px;
  right: 30px;
  background: #198754;
  color: #fff;
  padding: 10px 18px;
  border-radius: 10px;
  box-shadow: 0 3px 8px rgba(0,0,0,0.2);
  animation: fadeInOut 2s ease;
}
@keyframes fadeInOut {
  0% { opacity: 0; transform: translateY(10px); }
  10%, 90% { opacity: 1; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(10px); }
}
`;
document.head.appendChild(style);
