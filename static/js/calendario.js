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
let usuarioActualId = null; // ID real del usuario logueado

// =============================================================
// 🔹 Cargar empleados desde el backend
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

    // Guardar ID del usuario logueado si existe input hidden
    const inputUsuario = document.getElementById("usuarioId");
    if (inputUsuario) usuarioActualId = inputUsuario.value;

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
// 🔹 Filtrar eventos por usuario
// =============================================================
function filtrarEventosParaUsuario(eventos, usuarioId) {
  const usuario = usuarios.find(u => u.id == usuarioId);

  if (!usuario && usuarioId !== "mi") return [];

  // Empleado: propios eventos + globales
  if (usuarioId === "mi" || (usuario && usuario.rol.toLowerCase() === "empleado")) {
    const id = usuarioId === "mi" ? usuarioActualId : usuario.id;
    return eventos.filter(ev => ev.ID_Usuario == id || ev.Tipo.toLowerCase() === "global");
  }

  // Otros roles
  if (usuario) return eventos.filter(ev => ev.ID_Usuario == usuario.id);

  return [];
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

  // Días del mes
  for (let dia = 1; dia <= ultimoDia.getDate(); dia++) {
    const fechaDia = new Date(año, mes, dia);
    const fechaStr = fechaDia.toISOString().split("T")[0];
    const celda = document.createElement("div");
    celda.classList.add("day");
    celda.dataset.fecha = fechaStr;
    celda.innerHTML = `<div class="day-header">${dia}</div>`;

    const eventosDelDia = filtrarEventosParaUsuario(
      programaciones.filter(ev => ev.Fecha === fechaStr),
      usuarioSeleccionado
    );

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

    // Día actual
    const hoy = new Date();
    if (
      fechaDia.getDate() === hoy.getDate() &&
      fechaDia.getMonth() === hoy.getMonth() &&
      fechaDia.getFullYear() === hoy.getFullYear()
    ) {
      celda.classList.add("hoy");
    }

    celda.addEventListener("click", () => abrirMiModalConFecha(fechaStr, usuarioSeleccionado));
    grid.appendChild(celda);
  }
}

// =============================================================
// 🔹 Modal con eventos del día
// =============================================================
window.abrirMiModalConFecha = async function(fecha, usuarioId) {
  const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('modalPedidosDia'));
  const contenido = document.getElementById('contenidoPedidosDia');

  console.log("Programaciones:", programaciones);
  const eventosDelDia = filtrarEventosParaUsuario(
    
    programaciones.filter(ev => ev.Fecha === fecha),
    usuarioId
  );

  if (eventosDelDia.length === 0) {
    contenido.innerHTML = "<p>No hay eventos programados para este día.</p>";
    modal.show();
    return;
  }

  // Si el evento es una entrega o instalación, cargar detalles del pedido
  const esEntregaOInstalacion = eventosDelDia.some(ev =>
    ev.Tipo.toLowerCase().includes("entrega") || ev.Tipo.toLowerCase().includes("instalacion")
  );

  if (esEntregaOInstalacion) {
    contenido.innerHTML = `<p class="text-muted text-center">Cargando detalles del pedido...</p>`;
    modal.show();

    const evento = eventosDelDia.find(ev => ev.ID_Pedido);
    if (!evento) {
      contenido.innerHTML = "<p>No se encontró información del pedido asociado.</p>";
      return;
    }

    try {
      const res = await fetch(`/cliente/detalle_pedido/${evento.ID_Pedido}`);
      const data = await res.json();

      if (data.error) {
        contenido.innerHTML = `<p class="text-danger text-center">${data.error}</p>`;
        return;
      }

      const info = data[0];
      const productos = data.map(p => `
        <tr>
          <td>${p.NombreProducto}</td>
          <td>${p.Cantidad}</td>
          <td>$${p.PrecioUnidad.toFixed(2)}</td>
        </tr>
      `).join("");

      contenido.innerHTML = `
        <h5 class="fw-bold text-center text-primary mb-3">
          ${info.TipoPedido === 'Instalación' ? '🧰 Instalación' : '🚚 Entrega'}
        </h5>
        <p><strong>Cliente:</strong> ${info.ClienteNombre} ${info.ClienteApellido}</p>
        <p><strong>Dirección:</strong> ${info.DireccionEntrega}</p>
        <p><strong>Fecha:</strong> ${info.FechaPedido}</p>

        <h6 class="mt-3">Productos:</h6>
        <table class="table table-bordered table-sm">
          <thead class="table-light">
            <tr><th>Producto</th><th>Cantidad</th><th>Precio</th></tr>
          </thead>
          <tbody>${productos}</tbody>
        </table>

        <div class="text-end">
          <a href="/cliente/factura/pdf/${info.ID_Pedido}" target="_blank" class="btn btn-danger">
            <i class="bi bi-file-earmark-pdf"></i> Descargar factura PDF
          </a>
        </div>
      `;
    } catch (err) {
      contenido.innerHTML = `<p class="text-danger text-center">Error al cargar detalles del pedido.</p>`;
      console.error(err);
    }

  } else {
    // Otros tipos de evento
    contenido.innerHTML = eventosDelDia.map(ev =>
      `<div>
         <strong>${ev.Tipo}</strong>: ${ev.Empleado_Nombre || 'Sin asignar'}<br>
         Ubicación: ${ev.Ubicacion}<br>
         Hora: ${ev.Hora}
       </div><hr>`
    ).join("");
    modal.show();
  }
}

// =============================================================
// 🔹 Controles del calendario
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
// 🔹 Crear evento o reunión
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
