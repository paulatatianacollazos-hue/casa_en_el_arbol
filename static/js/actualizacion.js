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

  // Eventos de menú
  menuPerfil.addEventListener('click', e => { e.preventDefault(); activarMenu('perfil'); });
  menuDirecciones.addEventListener('click', e => { e.preventDefault(); activarMenu('direcciones'); });

  // Mostrar modal de "dirección guardada"
  const params = new URLSearchParams(window.location.search);
  if (params.get("direccion_guardada") === "1") {
    const modal = new bootstrap.Modal(document.getElementById('modalGuardado'));
    modal.show();
    activarMenu('direcciones');
  }

  // Interceptar formularios de borrar
  const deleteForms = document.querySelectorAll('form[action*="borrar_direccion"]');
  deleteForms.forEach(form => {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      formPendienteBorrar = this;
      itemPendienteBorrar = this.closest('.list-group-item'); // Guardamos el item visual
      const modalConfirm = new bootstrap.Modal(document.getElementById('modalConfirmarBorrar'));
      modalConfirm.show();
    });
  });

  // Confirmar eliminación
  document.getElementById('btnConfirmarBorrar').addEventListener('click', function () {
    if (formPendienteBorrar) {
      // Animación de desaparición antes de enviar
      itemPendienteBorrar.classList.add('fade');
      itemPendienteBorrar.style.opacity = 0;

      setTimeout(() => {
        formPendienteBorrar.submit();
      }, 300);
    }
  });

  // Mostrar modal de eliminación exitosa si viene de backend
  if (params.get("direccion_eliminada") === "1") {
    activarMenu('direcciones');
    const modalEliminado = new bootstrap.Modal(document.getElementById('modalEliminado'));
    modalEliminado.show();
  }
});


document.addEventListener("DOMContentLoaded", function () {
  const modal = new bootstrap.Modal(document.getElementById('modalPerfilGuardado'));
  modal.show();
});

