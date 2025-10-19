// ============================================================
// 🛒 MÓDULO DE CARRITO - CASA EN EL ÁRBOL
// ============================================================

// Recuperar carrito del localStorage
let cart = JSON.parse(localStorage.getItem('cart')) || [];

// ------------------------------------------------------------
// Renderizar página del carrito
// ------------------------------------------------------------
function renderCartPage() {
  const itemsContainer = document.getElementById('cart-items');
  const totalEl = document.getElementById('cart-total');

  if (!itemsContainer || !totalEl) return; // Evita errores en otras páginas

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
  itemsContainer.innerHTML = cart.map(p => {
    const price = parseFloat(p.price) || 0;
    total += price;

    return `
      <div class="list-group-item d-flex justify-content-between align-items-center">
        <div class="d-flex align-items-center">
          <img src="${p.image}" alt="${p.name}" 
               style="width:80px; height:80px; object-fit:cover; border-radius:10px; margin-right:10px;">
          <div>
            <h5 class="mb-1">${p.name}</h5>
            <p class="mb-0 text-muted">Material: ${p.material}</p>
          </div>
        </div>
        <div>
          <span class="fw-bold text-success">$${price.toFixed(2)}</span>
          <button class="btn btn-sm btn-outline-danger ms-3" onclick="removeFromCart(${p.id})">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
    `;
  }).join('');

  totalEl.textContent = "$" + total.toFixed(2);
}

// ------------------------------------------------------------
// Agregar producto al carrito
// ------------------------------------------------------------
function addToCart(product) {
  const exists = cart.find(p => p.id === product.id);
  if (exists) {
    alert("⚠️ Este producto ya está en tu carrito.");
    return;
  }

  cart.push(product);
  localStorage.setItem('cart', JSON.stringify(cart));
  updateCartCount();
  alert("✅ Producto añadido al carrito");
}

// ------------------------------------------------------------
// Eliminar producto
// ------------------------------------------------------------
function removeFromCart(id) {
  cart = cart.filter(p => p.id != id);
  localStorage.setItem('cart', JSON.stringify(cart));
  renderCartPage();
  updateCartCount();
}

// ------------------------------------------------------------
// Finalizar compra
// ------------------------------------------------------------
function checkoutCart() {
  if (cart.length === 0) {
    alert("Tu carrito está vacío.");
    return;
  }
  alert("✅ Compra procesada correctamente.");
  localStorage.removeItem('cart');
  cart = [];
  renderCartPage();
  updateCartCount();
}

// ------------------------------------------------------------
// Añadir producto desde botón (HTML data attributes)
// ------------------------------------------------------------
function addToCartFromButton(button) {
  const product = {
    id: button.getAttribute("data-id"),
    name: button.getAttribute("data-name"),
    price: parseFloat(button.getAttribute("data-price")) || 0,
    image: button.getAttribute("data-image"),
    material: button.getAttribute("data-material")
  };
  addToCart(product);
}

// ------------------------------------------------------------
// Actualizar contador del carrito globalmente
// ------------------------------------------------------------
function updateCartCount() {
  const countElement = document.getElementById('cart-count');
  const currentCart = JSON.parse(localStorage.getItem('cart')) || [];
  if (countElement) countElement.textContent = currentCart.length;
}

// ------------------------------------------------------------
// Inicialización
// ------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  updateCartCount();
  renderCartPage(); // Solo se ejecutará si existe el contenedor del carrito
});
