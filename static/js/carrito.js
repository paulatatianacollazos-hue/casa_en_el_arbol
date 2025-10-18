// =========================
//   CARRITO LATERAL
// =========================

// Cargar carrito del localStorage (si existe)
let cart = JSON.parse(localStorage.getItem('cart')) || [];

// Mostrar / ocultar panel lateral
function toggleCart() {
  document.getElementById('cart-panel').classList.toggle('active');
}

// Añadir producto al carrito
function addToCart(product) {
  const exists = cart.find(p => p.id === product.id);
  if (exists) {
    alert("⚠️ Este producto ya está en tu carrito.");
    return;
  }

  cart.push(product);
  localStorage.setItem('cart', JSON.stringify(cart));
  updateCartUI();
}

// Actualizar contador e interfaz del carrito
function updateCartUI() {
  const count = document.getElementById('cart-count');
  const itemsContainer = document.getElementById('cart-items');

  count.textContent = cart.length;

  if (cart.length === 0) {
    itemsContainer.innerHTML = `<p class="text-muted text-center">Tu carrito está vacío</p>`;
    return;
  }

  itemsContainer.innerHTML = cart.map(p => `
    <div class="cart-item d-flex align-items-center border-bottom py-2" onclick="showProductDetail(${p.id})">
      <img src="${p.image}" alt="${p.name}" class="me-2" style="width:60px; height:60px; object-fit:cover; border-radius:8px;">
      <div class="flex-grow-1">
        <strong>${p.name}</strong><br>
        <span class="text-muted">$${p.price}</span>
      </div>
      <button class="btn btn-sm btn-outline-danger ms-2" onclick="removeFromCart(${p.id}); event.stopPropagation();">
        <i class="bi bi-trash"></i>
      </button>
    </div>
  `).join('');
}

// Eliminar producto del carrito
function removeFromCart(id) {
  cart = cart.filter(p => p.id !== id);
  localStorage.setItem('cart', JSON.stringify(cart));
  updateCartUI();
}

// Mostrar detalle del producto (puedes abrir modal o redirigir)
function showProductDetail(id) {
  const product = cart.find(p => p.id === id);
  if (!product) return;

  alert(`📦 ${product.name}\n💲${product.price}\n🪵 Material: ${product.material}`);
}

// Simular checkout
function checkoutCart() {
  if (cart.length === 0) {
    alert("Tu carrito está vacío.");
    return;
  }
  alert("🛒 Procesando compra...");
}

document.addEventListener('DOMContentLoaded', updateCartUI);
