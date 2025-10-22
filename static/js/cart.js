// ===================== CONFIGURACIÓN DEL CARRITO ===================== //

// ID del usuario autenticado (inyectado desde Flask en el HTML)
let currentUserId = null;

// Genera una clave única para el carrito según el usuario actual
function getCartKey() {
  return `cart_${currentUserId || 'guest'}`;
}

// Carga el carrito desde localStorage
function loadCart() {
  const cartData = localStorage.getItem(getCartKey());
  return cartData ? JSON.parse(cartData) : [];
}

// Guarda el carrito en localStorage
function saveCart(cart) {
  localStorage.setItem(getCartKey(), JSON.stringify(cart));
  updateCartCount();
}

// Actualiza el contador del carrito en el ícono
function updateCartCount() {
  const cartCountElement = document.getElementById("cart-count");
  const cart = loadCart();
  const totalItems = cart.reduce((sum, item) => sum + (item.quantity || 1), 0);

  if (cartCountElement) {
    cartCountElement.textContent = totalItems;
  }
}

// Agrega un producto al carrito
function addToCart(product) {
  if (!product || !product.id) {
    console.error("❌ Producto inválido:", product);
    return;
  }

  let cart = loadCart();
  const existingItem = cart.find(item => item.id === product.id);

  if (existingItem) {
    existingItem.quantity = (existingItem.quantity || 1) + 1;
  } else {
    cart.push({ ...product, quantity: 1 });
  }

  saveCart(cart);
  alert(`✅ ${product.nombre || "Producto"} añadido al carrito`);
}

// Elimina un producto del carrito
function removeFromCart(productId) {
  let cart = loadCart();
  cart = cart.filter(item => item.id !== productId);
  saveCart(cart);
}

// Limpia todo el carrito
function clearCart() {
  localStorage.removeItem(getCartKey());
  updateCartCount();
}

// ===================== INICIALIZACIÓN ===================== //
document.addEventListener("DOMContentLoaded", () => {
  // Captura el ID del usuario desde Flask o desde localStorage
  currentUserId = window.FLASK_USER_ID || localStorage.getItem("currentUserId");

  // Guarda el ID para futuras sesiones
  if (currentUserId) {
    localStorage.setItem("currentUserId", currentUserId);
  }

  // Actualiza el número del carrito en pantalla
  updateCartCount();
});

// ===================== EXPORTAR FUNCIONES (opcional) ===================== //
// Si usas módulos ES6 o import/export, puedes descomentar esto:
// export { addToCart, removeFromCart, clearCart, updateCartCount, loadCart };
