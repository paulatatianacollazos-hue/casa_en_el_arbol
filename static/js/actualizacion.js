document.addEventListener('DOMContentLoaded', function () {
  const menuPerfil = document.getElementById('menu-perfil');
  const menuDirecciones = document.getElementById('menu-direcciones');
  const seccionPerfil = document.getElementById('seccion-perfil');
  const seccionDirecciones = document.getElementById('seccion-direcciones');
  let formPendienteBorrar = null;
  let itemPendienteBorrar = null;

  function activarMenu(seccion) {
    if (seccion === 'perfil') {
      seccionPerfil.style.display = 'block';
      seccionDirecciones.style.display = 'none';
      menuPerfil.classList.add('active');
      menuDirecciones.classList.remove('active');
    } else {
      seccionPerfil.style.display = 'none';
      seccionDirecciones.style.display = 'block';
      menuPerfil.classList.remove('active');
      menuDirecciones.classList.add('active');
    }
  }

  // --- Eventos de menú ---
  menuPerfil.addEventListener('click', e => { e.preventDefault(); activarMenu('perfil'); });
  menuDirecciones.addEventListener('click', e => { e.preventDefault(); activarMenu('direcciones'); });

  // --- Analizar parámetros de la URL ---
  const params = new URLSearchParams(window.location.search);

  // Si se guardó dirección -> mostrar modal y abrir direcciones
  if (params.get("direccion_guardada") === "1") {
    const modal = new bootstrap.Modal(document.getElementById('modalGuardado'));
    modal.show();
    activarMenu('direcciones');
  }

  // Si se eliminó dirección -> mostrar modal y abrir direcciones
  if (params.get("direccion_eliminada") === "1") {
    const modalEliminado = new bootstrap.Modal(document.getElementById('modalEliminado'));
    modalEliminado.show();
    activarMenu('direcciones');
  }

  // Si se guardó perfil -> mostrar modal y abrir perfil
  if (params.get("perfil_guardado") === "1") {
    const modal = new bootstrap.Modal(document.getElementById('modalPerfilGuardado'));
    modal.show();
    activarMenu('perfil');
  }

  // --- Interceptar formularios de borrar dirección ---
  const deleteForms = document.querySelectorAll('form[action*="borrar_direccion"]');
  deleteForms.forEach(form => {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      formPendienteBorrar = this;
      itemPendienteBorrar = this.closest('.list-group-item');

      const modalConfirm = new bootstrap.Modal(document.getElementById('modalConfirmarBorrar'));
      modalConfirm.show();
    });
  });

  // --- Confirmar eliminación ---
  document.getElementById('btnConfirmarBorrar').addEventListener('click', function () {
    if (formPendienteBorrar) {
      // Animación visual antes de enviar
      itemPendienteBorrar.classList.add('fade');
      itemPendienteBorrar.style.opacity = 0;

      setTimeout(() => {
        formPendienteBorrar.submit();
      }, 300);
    }
  });
});

