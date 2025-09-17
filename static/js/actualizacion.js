document.addEventListener("DOMContentLoaded", function () {
  // --- Menús ---
  const menuPerfil = document.getElementById("menu-perfil");
  const menuDirecciones = document.getElementById("menu-direcciones");
  const menuFavoritos = document.getElementById("menu-favoritos");
  const iconoFavoritos = document.getElementById("icono-favoritos");

  // --- Secciones ---
  const seccionPerfil = document.getElementById("seccion-perfil");
  const seccionDirecciones = document.getElementById("seccion-direcciones");
  const seccionFavoritos = document.getElementById("seccion-favoritos");

  // --- Variables para confirmación de borrado ---
  let formPendienteBorrar = null;
  let itemPendienteBorrar = null;

  // --- Mostrar secciones ---
  function mostrarSeccion(seccion) {
    // Ocultar todas
    seccionPerfil.style.display = "none";
    seccionDirecciones.style.display = "none";
    seccionFavoritos.style.display = "none";

    // Mostrar la seleccionada
    seccion.style.display = "block";

    // Quitar "active" de todos los menús
    [menuPerfil, menuDirecciones, menuFavoritos].forEach(m => m.classList.remove("active"));

    // Agregar "active" al que corresponda
    if (seccion === seccionPerfil) menuPerfil.classList.add("active");
    if (seccion === seccionDirecciones) menuDirecciones.classList.add("active");
    if (seccion === seccionFavoritos) menuFavoritos.classList.add("active");
  }

  // --- Eventos de menú ---
  menuPerfil?.addEventListener("click", e => { e.preventDefault(); mostrarSeccion(seccionPerfil); });
  menuDirecciones?.addEventListener("click", e => { e.preventDefault(); mostrarSeccion(seccionDirecciones); });
  menuFavoritos?.addEventListener("click", e => { e.preventDefault(); mostrarSeccion(seccionFavoritos); });
  iconoFavoritos?.addEventListener("click", e => { e.preventDefault(); mostrarSeccion(seccionFavoritos); });

  // --- Analizar parámetros de la URL ---
  const params = new URLSearchParams(window.location.search);

  if (params.get("direccion_guardada") === "1") {
    const modal = new bootstrap.Modal(document.getElementById("modalGuardado"));
    modal.show();
    mostrarSeccion(seccionDirecciones);
  }

  if (params.get("direccion_eliminada") === "1") {
    const modalEliminado = new bootstrap.Modal(document.getElementById("modalEliminado"));
    modalEliminado.show();
    mostrarSeccion(seccionDirecciones);
  }

  if (params.get("perfil_guardado") === "1") {
    const modal = new bootstrap.Modal(document.getElementById("modalPerfilGuardado"));
    modal.show();
    mostrarSeccion(seccionPerfil);
  }

  // --- Interceptar formularios de borrar dirección ---
  const deleteForms = document.querySelectorAll('form[action*="borrar_direccion"]');
  deleteForms.forEach(form => {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      formPendienteBorrar = this;
      itemPendienteBorrar = this.closest(".list-group-item");

      const modalConfirm = new bootstrap.Modal(document.getElementById("modalConfirmarBorrar"));
      modalConfirm.show();
    });
  });

  // --- Confirmar eliminación ---
  document.getElementById("btnConfirmarBorrar")?.addEventListener("click", function () {
    if (formPendienteBorrar) {
      // Animación visual antes de enviar
      itemPendienteBorrar.classList.add("fade");
      itemPendienteBorrar.style.opacity = 0;

      setTimeout(() => {
        formPendienteBorrar.submit();
      }, 300);
    }
  });
});
