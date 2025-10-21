// ============================================================
// 🛒 MÓDULO DE CARRITO - CASA EN EL ÁRBOL
// Adaptado a Flask-Login (app.py) — cada usuario tiene su carrito
// ============================================================

// ------------------------------------------------------------
// 🔸 Obtener ID de usuario desde Flask (inyectado en HTML)
// ------------------------------------------------------------
// En tu plantilla base (por ejemplo base.html), debes tener:
// <script>const FLASK_USER_ID = "{{ current_user.id if current_user.is_authenticated else null }}";</script>

let currentUserId = typeof FLASK_USER_ID !== "undefined" && FLASK_USER_ID ? String(FLASK_USER_ID) : null;

// ------------------------------------------------------------
// 🔸 Clave única de carrito por usuario
// ------------------------------------------------------------
function getCartKey() {
  return currentUserId ? `cart_${currentUserId}` : "cart_guest";
}

// ------------------------------------------------------------
// 🔸 Cargar carrito del usuario actual
// ------------------------------------------------------------
let cart = JSON.parse(localStorage.getItem(getCartKey())) || [];

function saveCart() {
  localStorage.setItem(getCartKey(), JSON.stringify(cart));
}

// ------------------------------------------------------------
// 🔸 Renderizar página del carrito
// ------------------------------------------------------------
function renderCartPage() {
  const itemsContainer = document.getElementById("cart-items");
  const totalEl = document.getElementById("cart-total");

  if (!itemsContainer || !totalEl) return;

  if (cart.length === 0) {
    itemsContainer.innerHTML = `
      <div class="alert alert-info text-center">
        Tu carrito está vacío. 
        <a href="/catalogo" class="alert-link">Ir al catálogo</a>
      </div>`;
    totalEl.textContent = "$0.00";
    return;
  }

  let total = 0;

  // Agrupar productos por ID
  const grouped = {};
  cart.forEach(p => {
    const id = String(p.id);
    if (!grouped[id]) {
      grouped[id] = { ...p, quantity: p.quantity || 1 };
    } else {
      grouped[id].quantity += p.quantity || 1;
    }
  });

  // Renderizar productos agrupados
  itemsContainer.innerHTML = Object.values(grouped)
    .map(p => {
      const price = parseFloat(p.price) || 0;
      const subtotal = price * p.quantity;
      total += subtotal;

      return `
        <div class="card mb-3 shadow-sm p-3">
          <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center">
              <img src="${p.image}" alt="${p.name}"
                   style="width:90px; height:90px; object-fit:cover; border-radius:10px; margin-right:15px;">
              <div>
                <h5 class="mb-1">${p.name}</h5>
                <p class="mb-0 text-muted">Material: ${p.material}</p>
                <div class="input-group input-group-sm mt-2" style="width:130px;">
                  <button class="btn btn-outline-secondary" onclick="changeQuantity('${p.id}', -1)">-</button>
                  <input type="text" class="form-control text-center" value="${p.quantity}" readonly>
                  <button class="btn btn-outline-secondary" onclick="changeQuantity('${p.id}', 1)">+</button>
                </div>
              </div>
            </div>
            <div>
              <span class="fw-bold text-success">$${subtotal.toFixed(2)}</span>
              <button class="btn btn-sm btn-outline-danger ms-3" onclick="removeFromCart('${p.id}')">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </div>
        </div>
      `;
    })
    .join("");

  totalEl.textContent = "$" + total.toFixed(2);
}

// ------------------------------------------------------------
// 🔸 Agregar producto al carrito
// ------------------------------------------------------------
function addToCart(product) {
  if (!currentUserId) {
    alert("⚠️ Debes iniciar sesión para agregar productos al carrito.");
    window.location.href = "/login"; // Redirigir al login de Flask
    return;
  }

  product.id = String(product.id);
  const exists = cart.find(p => p.id === product.id);

  if (exists) {
    exists.quantity += 1;
  } else {
    product.quantity = 1;
    cart.push(product);
  }

  saveCart();
  updateCartCount();
  alert(`🛍️ ${product.name} agregado al carrito`);
}

// ------------------------------------------------------------
// 🔸 Cambiar cantidad
// ------------------------------------------------------------
function changeQuantity(id, delta) {
  id = String(id);
  const item = cart.find(p => p.id === id);
  if (!item) return;

  item.quantity += delta;
  if (item.quantity <= 0) {
    removeFromCart(id);
    return;
  }

  saveCart();
  renderCartPage();
  updateCartCount();
}

// ------------------------------------------------------------
// 🔸 Eliminar producto
// ------------------------------------------------------------
function removeFromCart(id) {
  id = String(id);
  cart = cart.filter(p => p.id !== id);
  saveCart();
  renderCartPage();
  updateCartCount();
}

// ------------------------------------------------------------
// 🔸 Finalizar compra (enviar al backend si quieres)
// ------------------------------------------------------------
function checkoutCart() {
  if (!currentUserId) {
    alert("⚠️ Debes iniciar sesión para finalizar la compra.");
    window.location.href = "/login";
    return;
  }

  if (cart.length === 0) {
    alert("Tu carrito está vacío.");
    return;
  }

  alert("✅ Compra procesada correctamente.");
  localStorage.removeItem(getCartKey());
  cart = [];
  renderCartPage();
  updateCartCount();
}

// ------------------------------------------------------------
// 🔸 Agregar desde botón HTML (usando data-attributes)
// ------------------------------------------------------------
function addToCartFromButton(button) {
  const product = {
    id: String(button.getAttribute("data-id")),
    name: button.getAttribute("data-name"),
    price: parseFloat(button.getAttribute("data-price")) || 0,
    image: button.getAttribute("data-image"),
    material: button.getAttribute("data-material")
  };
  addToCart(product);
}

// ------------------------------------------------------------
// 🔸 Contador de carrito global
// ------------------------------------------------------------
function updateCartCount() {
  const countElement = document.getElementById("cart-count");
  const currentCart = JSON.parse(localStorage.getItem(getCartKey())) || [];
  const totalCount = currentCart.reduce((sum, item) => sum + (item.quantity || 1), 0);
  if (countElement) countElement.textContent = totalCount;
}

// ------------------------------------------------------------
// 🔸 Inicialización al cargar la página
// ------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  cart = JSON.parse(localStorage.getItem(getCartKey())) || [];
  updateCartCount();
  renderCartPage();
});
