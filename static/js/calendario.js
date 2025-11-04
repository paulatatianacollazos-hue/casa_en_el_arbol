// =============================================================
// 📅 CALENDARIO ADMINISTRADOR (Gestiona reuniones y eventos)
// =============================================================

const grid = document.getElementById("calendar-grid");
const mesTitulo = document.getElementById("titulo-mes");
const btnHoy = document.getElementById("btn-hoy");
const btnMes = document.getElementById("btn-mes");
const btnAño = document.getElementById("btn-año");
const selectorUsuario = document.getElementById("selectorUsuario");

let fechaActual = new Date();
let programaciones = [];
let usuarios = [];
let usuarioSeleccionado = "mi"; // Valor por defecto: Mi calendario

// =============================================================
// 🔹 Cargar empleados desde el backend (solo transportistas e instaladores)
// =============================================================
async function cargarUsuarios() {
  try {
    const resp = await fetch("/admin/usuarios_calendario");
    usuarios = await resp.json();

    // Opción “Mi calendario”
    const optMi = document.createElement("option");
    optMi.value = "mi";
    optMi.textContent = "🗓️ Mi calendario";
    selectorUsuario.appendChild(optMi);

    // Agregar empleados
    usuarios.forEach(u => {
      const opt = document.createElement("option");
      opt.value = u.id;
      opt.textContent = `${u.nombre} (${u.rol})`;
      selectorUsuario.appendChild(opt);
    });
  } catch (err) {
    console.error("❌ Error al cargar usuarios:", err);
  }
}

// =============================================================
// 🔹 Cargar programaciones desde el servidor
// =============================================================
async function cargarProgramaciones() {
  try {
    const resp = await fetch("/empleado/programaciones_todas");
    programaciones = await resp.json();
    renderCalendario(fechaActual);
  } catch (err) {
    console.error("❌ Error al cargar programaciones:", err);
  }
}

// =============================================================
// 🔹 Renderizar calendario
// =============================================================
function renderCalendario(fecha) {
  grid.innerHTML = "";

  const año = fecha.getFullYear();
  const mes = fecha.getMonth();
  const primerDia = new Date(año, mes, 1);
  const ultimoDia = new Date(año, mes + 1, 0);
  const primerDiaSemana = primerDia.getDay() === 0 ? 6 : primerDia.getDay() - 1;

  mesTitulo.textContent = fecha.toLocaleDateString("es-ES", {
    month: "long",
    year: "numeric"
  });

  // Celdas vacías
  for (let i = 0; i < primerDiaSemana; i++) {
    const celdaVacia = document.createElement("div");
    celdaVacia.classList.add("day", "empty");
    grid.appendChild(celdaVacia);
  }

  let eventosFiltrados = [...programaciones];
  if (usuarioSeleccionado !== "mi") {
    eventosFiltrados = eventosFiltrados.filter(ev => ev.Empleado_ID == usuarioSeleccionado);
  }

  for (let dia = 1; dia <= ultimoDia.getDate(); dia++) {
    const fechaDia = new Date(año, mes, dia);
    const fechaStr = fechaDia.toISOString().split("T")[0];
    const celda = document.createElement("div");

    celda.classList.add("day");
    celda.dataset.fecha = fechaStr;
    celda.innerHTML = `<div class="day-header">${dia}</div>`;

    const eventosDelDia = eventosFiltrados.filter(ev => ev.Fecha === fechaStr);

    if (eventosDelDia.length > 0) {
      const tipos = [...new Set(eventosDelDia.map(ev => ev.Tipo))];
      const colores = {
        "Entrega": "bg-success",
        "Instalación": "bg-primary",
        "Reunión interna": "bg-danger",
        "Evento": "bg-warning",
        "Global": "bg-success",
        "Personal": "bg-secondary"
      };

      const etiquetas = tipos.map(t => {
        const color = colores[t] || "bg-secondary";
        return `<span class="badge ${color} me-1">${t}</span>`;
      }).join("");

      celda.innerHTML += `<div class="event-tags mt-1">${etiquetas}</div>`;
    }

    const hoy = new Date();
    if (
      fechaDia.getDate() === hoy.getDate() &&
      fechaDia.getMonth() === hoy.getMonth() &&
      fechaDia.getFullYear() === hoy.getFullYear()
    ) {
      celda.classList.add("hoy");
    }

    // Abrir modal al hacer click en la celda
    celda.addEventListener("click", () => {
      abrirMiModalConFecha(fechaStr);
    });

    grid.appendChild(celda);
  }
}

// Función para abrir modal con eventos del día
function abrirMiModalConFecha(fecha) {
  const modal = document.getElementById('modalPedidosDia');
  const contenido = document.getElementById('contenidoPedidosDia');

  const eventosDelDia = programaciones.filter(ev => ev.Fecha === fecha);
  
  if (eventosDelDia.length === 0) {
    contenido.innerHTML = "<p>No hay eventos programados para este día.</p>";
  } else {
    contenido.innerHTML = eventosDelDia.map(ev => 
      `<div>
         <strong>${ev.Tipo}</strong>: ${ev.Empleado_Nombre || 'Sin asignar'}<br>
         Ubicación: ${ev.Ubicacion}<br>
         Hora: ${ev.Hora}
       </div><hr>`).join("");
  }

  abrirMiModal();
}

// Modal base
function abrirMiModal() {
  const modal = document.getElementById('modalPedidosDia');
  modal.classList.add('show');
  modal.style.display = 'block';
  document.body.classList.add('modal-open');

  const backdrop = document.createElement('div');
  backdrop.className = 'modal-backdrop fade show';
  backdrop.id = 'customBackdrop';
  document.body.appendChild(backdrop);
}

function cerrarMiModal() {
  const modal = document.getElementById('modalPedidosDia');
  modal.classList.remove('show');
  modal.style.display = 'none';
  document.body.classList.remove('modal-open');

  const backdrops = document.querySelectorAll('.modal-backdrop');
  backdrops.forEach(b => b.remove());
}


// =============================================================
// 🔹 Botones de control
// =============================================================
btnHoy.addEventListener("click", () => {
  fechaActual = new Date();
  renderCalendario(fechaActual);
});

btnMes.addEventListener("click", () => {
  const selectorMes = document.createElement("input");
  selectorMes.type = "month";
  selectorMes.style.position = "absolute";
  selectorMes.style.opacity = "0";
  document.body.appendChild(selectorMes);

  const año = fechaActual.getFullYear();
  const mes = String(fechaActual.getMonth() + 1).padStart(2, "0");
  selectorMes.value = `${año}-${mes}`;

  selectorMes.addEventListener("change", (e) => {
    const [nuevoAño, nuevoMes] = e.target.value.split("-");
    fechaActual = new Date(parseInt(nuevoAño), parseInt(nuevoMes) - 1, 1);
    renderCalendario(fechaActual);
    document.body.removeChild(selectorMes);
  });

  selectorMes.showPicker?.();
  selectorMes.click();
});

btnAño.addEventListener("click", () => {
  const añoActual = fechaActual.getFullYear();
  const nuevoAño = prompt("Ingrese un año:", añoActual);
  if (nuevoAño && !isNaN(nuevoAño)) {
    fechaActual = new Date(parseInt(nuevoAño), fechaActual.getMonth(), 1);
    renderCalendario(fechaActual);
  }
});

// =============================================================
// 🔹 Cambio de usuario
// =============================================================
selectorUsuario.addEventListener("change", (e) => {
  usuarioSeleccionado = e.target.value;
  renderCalendario(fechaActual);
});

// =============================================================
// 🔹 Inicialización
// =============================================================
document.addEventListener("DOMContentLoaded", async () => {
  await cargarUsuarios();
  await cargarProgramaciones();
});

// =============================================================
// 🔹 Crear evento o reunión (Personal o Global)
// =============================================================
document.getElementById("formNuevoEvento").addEventListener("submit", async (e) => {
  e.preventDefault();

  const form = e.target;
  const data = {
    Tipo: form.Tipo.value,
    Fecha: form.Fecha.value,
    Hora: form.Hora.value,
    Ubicacion: form.Ubicacion.value,
    Visibilidad: form.Visibilidad.value // Nuevo campo
  };

  try {
    const resp = await fetch("/admin/admin/calendario/nuevo_evento", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    const result = await resp.json();

    if (!resp.ok || !result.ok) {
      alert(result.error || "Error al crear evento");
      return;
    }

    alert("✅ Evento creado correctamente");
    const modal = bootstrap.Modal.getInstance(document.getElementById("modalNuevoEvento"));
    modal.hide();
    await cargarProgramaciones();

  } catch (err) {
    console.error("❌ Error al enviar evento:", err);
    alert("Error al crear el evento");
  }

  celda.addEventListener("click", () => {
    const fecha = celda.dataset.fecha;
    abrirMiModalConFecha(fecha); // Creamos una función que cargue los eventos de ese día
});


function abrirMiModalConFecha(fecha) {
    const modal = document.getElementById('modalPedidosDia');
    const contenido = document.getElementById('contenidoPedidosDia');

    // Filtrar eventos del día
    const eventosDelDia = programaciones.filter(ev => ev.Fecha === fecha);
    
    if (eventosDelDia.length === 0) {
        contenido.innerHTML = "<p>No hay eventos programados para este día.</p>";
    } else {
        contenido.innerHTML = eventosDelDia.map(ev => 
            `<div>
                <strong>${ev.Tipo}</strong>: ${ev.Empleado_Nombre || 'Sin asignar'}<br>
                Ubicación: ${ev.Ubicacion}<br>
                Hora: ${ev.Hora}
            </div><hr>`).join("");
    }

    // Abrir modal
    abrirMiModal();
}



});
