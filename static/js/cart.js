// ============================================================
// 🛒 MÓDULO DE CARRITO - CASA EN EL ÁRBOL (versión por usuario)
// ============================================================

// ------------------------------------------------------------
// 🔸 Manejo de usuario actual
// ------------------------------------------------------------
let currentUserId = localStorage.getItem('currentUserId') || null;

// Función para obtener la clave de carrito asociada al usuario actual
function getCartKey() {
  return currentUserId ? `cart_${currentUserId}` : 'cart';
}

// ------------------------------------------------------------
// 🔸 Cargar carrito inicial desde localStorage
// ------------------------------------------------------------
let cart = JSON.parse(localStorage.getItem(getCartKey())) || [];

// Guardar carrito del usuario actual
function saveCart() {
  localStorage.setItem(getCartKey(), JSON.stringify(cart));
}

// ------------------------------------------------------------
// 🔸 Renderizar página del carrito (cada producto distinto en su propio div)
// ------------------------------------------------------------
function renderCartPage() {
  const itemsContainer = document.getElementById('cart-items');
  const totalEl = document.getElementById('cart-total');

  if (!itemsContainer || !totalEl) return;

  if (cart.length === 0) {
    itemsContainer.innerHTML = `
      <div class="alert alert-info text-center">
        Tu carrito está vacío. 
        <a href="/cliente/catalogo" class="alert-link">Ir al catálogo</a>
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

  // Renderizar productos
  itemsContainer.innerHTML = Object.values(grouped).map(p => {
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
  }).join('');

  totalEl.textContent = "$" + total.toFixed(2);
}

// ------------------------------------------------------------
// 🔸 Agregar producto al carrito
// ------------------------------------------------------------
function addToCart(product) {
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
}

// ------------------------------------------------------------
// 🔸 Cambiar cantidad de un producto
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
// 🔸 Eliminar producto del carrito
// ------------------------------------------------------------
function removeFromCart(id) {
  id = String(id);
  cart = cart.filter(p => p.id !== id);
  saveCart();
  renderCartPage();
  updateCartCount();
}

// ------------------------------------------------------------
// 🔸 Finalizar compra
// ------------------------------------------------------------
function checkoutCart() {
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
// 🔸 Añadir producto desde botón con data attributes
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
// 🔸 Actualizar contador del carrito globalmente
// ------------------------------------------------------------
function updateCartCount() {
  const countElement = document.getElementById('cart-count');
  const currentCart = JSON.parse(localStorage.getItem(getCartKey())) || [];
  const totalCount = currentCart.reduce((sum, item) => sum + (item.quantity || 1), 0);
  if (countElement) countElement.textContent = totalCount;
}

// ------------------------------------------------------------
// 🔸 Manejo de sesión de usuario
// ------------------------------------------------------------
function loginUser(userId) {
  currentUserId = userId;
  localStorage.setItem('currentUserId', userId);
  cart = JSON.parse(localStorage.getItem(getCartKey())) || [];
  updateCartCount();
  renderCartPage();
  alert(`🔓 Sesión iniciada como: ${userId}`);
}

function logoutUser() {
  if (!currentUserId) return;
  localStorage.removeItem(getCartKey());
  localStorage.removeItem('currentUserId');
  cart = [];
  currentUserId = null;
  updateCartCount();
  renderCartPage();
  alert("👋 Sesión cerrada. Tu carrito ha sido vaciado.");
}

// ------------------------------------------------------------
// 🔸 Inicialización al cargar la página
// ------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  currentUserId = localStorage.getItem('currentUserId');
  cart = JSON.parse(localStorage.getItem(getCartKey())) || [];
  updateCartCount();
  renderCartPage();
});
