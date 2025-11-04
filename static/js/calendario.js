// =============================================================
// 📅 CALENDARIO DINÁMICO DE EMPLEADOS (Transportistas e Instaladores)
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
    // 🔸 Ruta corregida (sin /empleado/)
    const resp = await fetch("/admin/usuarios_calendario");
    usuarios = await resp.json();

    // Agregar opción "Mi calendario"
    const optMi = document.createElement("option");
    optMi.value = "mi";
    optMi.textContent = "🗓️ Mi calendario";
    selectorUsuario.appendChild(optMi);

    // Agregar transportistas e instaladores
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
    const resp = await fetch("/empleado/programaciones_todas"); // ruta de tus eventos
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

  // 🔹 Filtrar eventos por usuario seleccionado
  let eventosFiltrados = [...programaciones];
  if (usuarioSeleccionado !== "mi") {
    eventosFiltrados = eventosFiltrados.filter(ev => ev.Empleado_ID == usuarioSeleccionado);
  }

  // 📅 Renderizar días
  for (let dia = 1; dia <= ultimoDia.getDate(); dia++) {
    const fechaDia = new Date(año, mes, dia);
    const fechaStr = fechaDia.toISOString().split("T")[0];
    const celda = document.createElement("div");

    celda.classList.add("day");
    celda.dataset.fecha = fechaStr;
    celda.innerHTML = `<div class="day-header">${dia}</div>`;

    // Eventos de ese día
    const eventosDelDia = eventosFiltrados.filter(ev => ev.Fecha === fechaStr);

    // 🎨 Colores por tipo
    if (eventosDelDia.length > 0) {
      const tipos = [...new Set(eventosDelDia.map(ev => ev.Tipo))];
      const colores = {
        "Entrega": "bg-success",           // 🟩 Verde
        "Entregas": "bg-success",
        "Instalación": "bg-primary",       // 🟦 Azul
        "Instalaciones": "bg-primary",
        "Reunión interna": "bg-danger",    // 🔴 Rojo
        "Reuniones internas": "bg-danger",
        "Evento": "bg-danger",
        "Eventos": "bg-danger"
      };

      const etiquetas = tipos.map(t => {
        const color = colores[t] || "bg-secondary";
        return `<span class="badge ${color} me-1">${t}</span>`;
      }).join("");

      const nombres = [...new Set(eventosDelDia.map(ev => ev.Empleado))];
      const listaNombres = nombres.length > 0 ? `<small>${nombres.join(", ")}</small>` : "";

      celda.innerHTML += `
        <div class="event-tags mt-1">${etiquetas}</div>
        ${listaNombres}
      `;
    }

    // 🟢 Día actual
    const hoy = new Date();
    if (
      fechaDia.getDate() === hoy.getDate() &&
      fechaDia.getMonth() === hoy.getMonth() &&
      fechaDia.getFullYear() === hoy.getFullYear()
    ) {
      celda.classList.add("hoy");
    }

    grid.appendChild(celda);
  }
}

// =============================================================
// 🔹 Botón "Hoy"
// =============================================================
btnHoy.addEventListener("click", () => {
  fechaActual = new Date();
  renderCalendario(fechaActual);

  const hoyCelda = document.querySelector(".day.hoy");
  if (hoyCelda) {
    hoyCelda.scrollIntoView({ behavior: "smooth", block: "center" });
    hoyCelda.classList.add("highlight-today");
    setTimeout(() => hoyCelda.classList.remove("highlight-today"), 2000);
  }
});

// =============================================================
// 🔹 Botón "Mes"
// =============================================================
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

// =============================================================
// 🔹 Botón "Año"
// =============================================================
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
// 🔹 Click en día → Modal
// =============================================================
grid.addEventListener("click", (e) => {
  const celda = e.target.closest(".day");
  if (!celda || celda.classList.contains("empty")) return;

  const fechaSeleccionada = celda.dataset.fecha;
  const modal = new bootstrap.Modal(document.getElementById("modalPedidosDia"));
  const contenido = document.getElementById("contenidoPedidosDia");
  document.getElementById("modalPedidosDiaLabel").textContent =
    "Programaciones del " + new Date(fechaSeleccionada).toLocaleDateString("es-ES");

  const eventos = programaciones.filter(ev => ev.Fecha === fechaSeleccionada);

  if (eventos.length === 0) {
    contenido.innerHTML = `
      <div class="d-flex flex-column align-items-center justify-content-center py-4">
        <i class="bi bi-calendar-x text-secondary" style="font-size: 3rem;"></i>
        <p class="mt-3 mb-0 fs-5 text-muted">No hay eventos programados.</p>
      </div>`;
  } else {
    const grupos = {};
    eventos.forEach(ev => {
      if (!grupos[ev.Tipo]) grupos[ev.Tipo] = [];
      grupos[ev.Tipo].push(ev);
    });

    contenido.innerHTML = Object.entries(grupos)
      .map(([tipo, lista]) => `
        <div class="mb-4">
          <h6 class="fw-bold text-success text-uppercase border-bottom pb-1 mb-2">${tipo}</h6>
          ${lista.map(ev => `
            <div class="card mb-2 border-success">
              <div class="card-body text-start">
                <h6 class="card-title mb-1 fw-bold">#${ev.ID_Pedido || ev.ID_Calendario}</h6>
                <p class="mb-0"><strong>Ubicación:</strong> ${ev.Ubicacion || "Sin especificar"}</p>
                <p class="mb-0"><strong>Hora:</strong> ${ev.Hora || "No definida"}</p>
                <p class="mb-0"><strong>Empleado:</strong> ${ev.Empleado || "Sin asignar"}</p>
              </div>
            </div>
          `).join("")}
        </div>
      `).join("");
  }

  modal.show();
});

// =============================================================
// 🔹 Inicialización
// =============================================================
document.addEventListener("DOMContentLoaded", async () => {
  await cargarUsuarios();
  await cargarProgramaciones();
});

// =============================================================
// 🔹 Enviar formulario de nuevo evento o reunión
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("formNuevoEvento");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const datos = {
      Tipo: form.Tipo.value,
      Fecha: form.Fecha.value,
      Hora: form.Hora.value,
      Ubicacion: form.Ubicacion.value
    };

    try {
      const resp = await fetch("/admin/calendario/nuevo_evento", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos)
      });

      const result = await resp.json();

      if (!resp.ok) {
        alert(result.error || "Error al registrar evento");
        return;
      }

      alert(result.mensaje || "Evento registrado correctamente ✅");

      // Cerrar modal y refrescar calendario
      const modal = bootstrap.Modal.getInstance(document.getElementById("modalNuevoEvento"));
      modal.hide();
      await cargarProgramaciones(); // vuelve a cargar el calendario

    } catch (err) {
      console.error("❌ Error al enviar evento:", err);
      alert("No se pudo registrar el evento");
    }
  });
});
