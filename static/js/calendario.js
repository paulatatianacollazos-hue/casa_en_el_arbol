// =============================================================
// 📅 CALENDARIO ADMINISTRADOR
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
let usuarioSeleccionado = "mi";

// =============================================================
// 🔹 Cargar usuarios
// =============================================================
async function cargarUsuarios() {
  try {
    const resp = await fetch("/admin/usuarios_calendario");
    usuarios = await resp.json();

    // Mi calendario
    const optMi = document.createElement("option");
    optMi.value = "mi";
    optMi.textContent = "🗓️ Mi calendario";
    selectorUsuario.appendChild(optMi);

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
// 🔹 Cargar programaciones
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
// 🔹 Filtrar eventos según usuario
// =============================================================
function filtrarEventosParaUsuario(eventos) {
  if (usuarioSeleccionado === "mi") {
    // Mi calendario: incluir mis eventos + globales si soy empleado
    const usuario = usuarios.find(u => u.id == "mi") || { rol: "empleado" };
    return eventos.filter(ev =>
      ev.Empleado_ID == "mi" || ev.Tipo.toLowerCase() === "global"
    );
  } else {
    const usuario = usuarios.find(u => u.id == usuarioSeleccionado);
    if (!usuario) return [];
    const rol = usuario.rol.toLowerCase();
    if (rol === "empleado") {
      return eventos.filter(ev =>
        ev.Empleado_ID == usuario.id || ev.Tipo.toLowerCase() === "global"
      );
    } else {
      // Otros roles solo ven sus eventos
      return eventos.filter(ev => ev.Empleado_ID == usuario.id);
    }
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

  mesTitulo.textContent = fecha.toLocaleDateString("es-ES", { month: "long", year: "numeric" });

  // Celdas vacías
  for (let i = 0; i < primerDiaSemana; i++) {
    const celdaVacia = document.createElement("div");
    celdaVacia.classList.add("day", "empty");
    grid.appendChild(celdaVacia);
  }

  const eventosFiltrados = filtrarEventosParaUsuario(programaciones);

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
        "entrega": "bg-success",
        "instalación": "bg-primary",
        "reunión interna": "bg-danger",
        "evento": "bg-warning",
        "global": "bg-success",
        "personal": "bg-secondary"
      };

      const etiquetas = tipos.map(t => {
        const color = colores[t.toLowerCase()] || "bg-secondary";
        return `<span class="badge ${color} me-1">${t}</span>`;
      }).join("");

      celda.innerHTML += `<div class="event-tags mt-1">${etiquetas}</div>`;
    }

    const hoy = new Date();
    if (fechaDia.toDateString() === hoy.toDateString()) {
      celda.classList.add("hoy");
    }

    celda.addEventListener("click", () => abrirMiModalConFecha(fechaStr));
    grid.appendChild(celda);
  }
}

// =============================================================
// 🔹 Modal eventos día
// =============================================================
function abrirMiModalConFecha(fecha) {
  const modalEl = document.getElementById('modalPedidosDia');
  const contenido = document.getElementById('contenidoPedidosDia');

  const eventosFiltrados = filtrarEventosParaUsuario(programaciones);
  const eventosDelDia = eventosFiltrados.filter(ev => ev.Fecha === fecha);

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

  const modal = new bootstrap.Modal(modalEl);
  modal.show();
}

// =============================================================
// 🔹 Botones y controles
// =============================================================
btnHoy.addEventListener("click", () => { fechaActual = new Date(); renderCalendario(fechaActual); });

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
  const nuevoAño = prompt("Ingrese un año:", fechaActual.getFullYear());
  if (nuevoAño && !isNaN(nuevoAño)) {
    fechaActual = new Date(parseInt(nuevoAño), fechaActual.getMonth(), 1);
    renderCalendario(fechaActual);
  }
});

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
// 🔹 Crear nuevo evento
// =============================================================
document.getElementById("formNuevoEvento").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const data = {
    Tipo: form.Tipo.value,
    Fecha: form.Fecha.value,
    Hora: form.Hora.value,
    Ubicacion: form.Ubicacion.value,
    Visibilidad: form.Visibilidad.value
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
});
