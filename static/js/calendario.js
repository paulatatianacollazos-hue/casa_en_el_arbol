// =============================================================
// 📅 CALENDARIO ADMINISTRADOR (Gestiona reuniones y pedidos)
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
let usuarioActualId = null;

// =============================================================
// 🔹 Cargar empleados desde el backend
// =============================================================
async function cargarUsuarios() {
  try {
    const resp = await fetch("/admin/usuarios_calendario");
    const data = await resp.json();
    usuarios = data.usuarios || [];
    selectorUsuario.innerHTML = "";

    const optMi = document.createElement("option");
    optMi.value = "mi";
    optMi.textContent = "🗓️ Mi calendario";
    selectorUsuario.appendChild(optMi);

    usuarios.forEach(u => {
      const opt = document.createElement("option");
      opt.value = u.id;
      opt.textContent = u.nombre;
      selectorUsuario.appendChild(opt);
    });

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
  if (usuarioId === "mi") return eventos;
  return eventos.filter(ev => ev.Empleado_ID == usuarioId || ev.Tipo?.toLowerCase() === "global");
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

  for (let i = 0; i < primerDiaSemana; i++) {
    const celdaVacia = document.createElement("div");
    celdaVacia.classList.add("day", "empty");
    grid.appendChild(celdaVacia);
  }

  for (let dia = 1; dia <= ultimoDia.getDate(); dia++) {
    const fechaDia = new Date(año, mes, dia);
    const fechaStr = fechaDia.toISOString().split("T")[0];
    const celda = document.createElement("div");
    celda.classList.add("day");
    celda.dataset.fecha = fechaStr;
    celda.innerHTML = `<div class="day-header">${dia}</div>`;

    const eventosDelDia = filtrarEventosParaUsuario(programaciones.filter(ev => ev.Fecha === fechaStr), usuarioSeleccionado);

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
      const etiquetas = tipos.map(t => `<span class="badge ${colores[t] || 'bg-secondary'} me-1">${t}</span>`).join("");
      celda.innerHTML += `<div class="event-tags mt-1">${etiquetas}</div>`;
    }

    const hoy = new Date();
    if (fechaDia.toDateString() === hoy.toDateString()) celda.classList.add("hoy");

    celda.addEventListener("click", () => abrirMiModalConFecha(fechaStr, usuarioSeleccionado));
    grid.appendChild(celda);
  }
}

// =============================================================
// 🔹 Modal con eventos del día y productos con checkbox
// =============================================================
window.abrirMiModalConFecha = async function(fecha, usuarioId) {
  const modalEl = document.getElementById('modalPedidosDia');
  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
  const contenido = document.getElementById('contenidoPedidosDia');

  const eventosDelDia = filtrarEventosParaUsuario(programaciones.filter(ev => ev.Fecha === fecha), usuarioId);

  if (!eventosDelDia || eventosDelDia.length === 0) {
    contenido.innerHTML = "<p class='text-center text-muted'>No hay eventos programados para este día.</p>";
    modal.show();
    return;
  }

  const pedidosDelDia = eventosDelDia.filter(ev => ev.ID_Pedido);
  if (!pedidosDelDia.length) {
    contenido.innerHTML = "<p class='text-center text-danger'>No se encontraron pedidos asociados para este día.</p>";
    modal.show();
    return;
  }

  const resultados = await Promise.all(
    pedidosDelDia.map(async (evento) => {
      try {
        const res = await fetch(`/empleado/detalle_pedido/${evento.ID_Pedido}`);
        const data = await res.json();
        if (data.error) return `<div class='alert alert-danger'>Error en pedido #${evento.ID_Pedido}: ${data.error}</div>`;

        const info = data[0];

        const productosHTML = data.map(p => `
          <tr>
            <td>${p.NombreProducto}</td>
            <td><input type="checkbox" class="chk-producto" data-id="${p.ID_Producto}" ${p.marcado ? 'checked' : ''}></td>
            <td class="estado-producto">${p.marcado ? 'Recogido' : 'No recogido'}</td>
          </tr>
        `).join("");

        return `
          <div class='card mb-3 shadow-sm border-0'>
            <div class='card-header ${info.TipoPedido === 'Instalación' ? 'bg-primary' : 'bg-success'} text-white'>
              <strong>${info.TipoPedido === 'Instalación' ? '🧰 Instalación' : '🚚 Entrega'} #${info.ID_Pedido}</strong>
            </div>
            <div class='card-body'>
              <p><strong>Cliente:</strong> ${info.ClienteNombre} ${info.ClienteApellido}</p>
              <p><strong>Dirección:</strong> ${info.DireccionEntrega}</p>
              <p><strong>Fecha:</strong> ${info.FechaPedido}</p>
              <p><strong>Estado:</strong> ${info.Estado}</p>

              <form id="formProductosPedido-${info.ID_Pedido}">
                <table class='table table-bordered table-sm'>
                  <thead class='table-light'>
                    <tr><th>Producto</th><th>Seleccionar</th><th>Estado</th></tr>
                  </thead>
                  <tbody>
                    ${productosHTML}
                  </tbody>
                </table>
                <div class="d-flex justify-content-between">
                  <button type="submit" class="btn btn-sm btn-primary">Guardar selección</button>
                  <a href="/empleado/registro_entrega/${info.ID_Pedido}" class="btn btn-outline-success btn-sm">
                    <i class="bi bi-journal-text"></i> Registro de Entrega
                  </a>
                </div>
              </form>
            </div>
          </div>
        `;
      } catch (err) {
        console.error("❌ Error cargando pedido:", err);
        return `<div class='alert alert-danger'>Error cargando el pedido #${evento.ID_Pedido}</div>`;
      }
    })
  );

  contenido.innerHTML = resultados.join("");
  modal.show();

  // 🔹 Listeners para checkboxes
  document.querySelectorAll(".chk-producto").forEach(chk => {
    chk.addEventListener("change", (e) => {
      const row = e.target.closest("tr");
      const estadoCelda = row.querySelector(".estado-producto");
      estadoCelda.textContent = e.target.checked ? "Recogido" : "No recogido";
    });
  });

  // 🔹 Listeners para guardar productos
  pedidosDelDia.forEach(evento => {
    const form = document.getElementById(`formProductosPedido-${evento.ID_Pedido}`);
    if (!form) return;
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const checkboxes = form.querySelectorAll(".chk-producto");
      const productosMarcados = Array.from(checkboxes)
        .filter(chk => chk.checked)
        .map(chk => chk.dataset.id);

      try {
        const resp = await fetch(`/empleado/actualizar_productos/${evento.ID_Pedido}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ productos: productosMarcados })
        });
        const result = await resp.json();
        if (resp.ok && result.success) alert("✅ Selección de productos guardada correctamente");
        else alert("❌ Error al guardar selección");
      } catch (err) {
        console.error("❌ Error al enviar productos:", err);
        alert("Error al guardar la selección");
      }
    });
  });
};

// =============================================================
// 🔹 ABRIR MODAL DE REGISTRO DE ENTREGA
// =============================================================
window.abrirModalEntrega = function(pedidoId) {
  const input = document.getElementById("pedidoEntregaId");
  if (!input) { alert("⚠️ No se encontró el campo oculto del pedido en el modal."); return; }
  input.value = pedidoId;
  const modal = new bootstrap.Modal(document.getElementById("modalRegistroEntrega"));
  modal.show();
};

// =============================================================
// 🔹 Controles del calendario
// =============================================================
btnHoy.addEventListener("click", () => { fechaActual = new Date(); renderCalendario(fechaActual); });
btnMes.addEventListener("click", () => {
  const selectorMes = document.createElement("input");
  selectorMes.type = "month";
  selectorMes.style.position = "absolute"; selectorMes.style.opacity = "0";
  document.body.appendChild(selectorMes);
  const año = fechaActual.getFullYear();
  const mes = String(fechaActual.getMonth() + 1).padStart(2, "0");
  selectorMes.value = `${año}-${mes}`;
  selectorMes.addEventListener("change", e => {
    const [nuevoAño, nuevoMes] = e.target.value.split("-");
    fechaActual = new Date(parseInt(nuevoAño), parseInt(nuevoMes)-1, 1);
    renderCalendario(fechaActual);
    document.body.removeChild(selectorMes);
  });
  selectorMes.showPicker?.(); selectorMes.click();
});
btnAño.addEventListener("click", () => {
  const añoActual = fechaActual.getFullYear();
  const nuevoAño = prompt("Ingrese un año:", añoActual);
  if (nuevoAño && !isNaN(nuevoAño)) fechaActual = new Date(parseInt(nuevoAño), fechaActual.getMonth(), 1);
  renderCalendario(fechaActual);
});
selectorUsuario.addEventListener("change", (e) => { usuarioSeleccionado = e.target.value; renderCalendario(fechaActual); });

// =============================================================
// 🔹 Inicialización
// =============================================================
document.addEventListener("DOMContentLoaded", async () => {
  await cargarUsuarios();
  await cargarProgramaciones();
});
