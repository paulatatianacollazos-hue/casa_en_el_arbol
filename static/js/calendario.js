// =============================================================
// 📅 CALENDARIO DINÁMICO - EMPLEADO (Pedidos + otros eventos)
// =============================================================

const grid = document.getElementById("calendar-grid");
const mesTitulo = document.getElementById("titulo-mes");
const btnHoy = document.getElementById("btn-hoy");
const btnMes = document.getElementById("btn-mes");
const btnAño = document.getElementById("btn-año");

let fechaActual = new Date();
let programaciones = []; // Guardará todos los eventos obtenidos desde Flask

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

  // Celdas vacías al inicio
  for (let i = 0; i < primerDiaSemana; i++) {
    const celdaVacia = document.createElement("div");
    celdaVacia.classList.add("day", "empty");
    grid.appendChild(celdaVacia);
  }

  // Días del mes
  for (let dia = 1; dia <= ultimoDia.getDate(); dia++) {
    const fechaDia = new Date(año, mes, dia);
    const celda = document.createElement("div");
    celda.classList.add("day");
    celda.dataset.fecha = fechaDia.toISOString().split("T")[0];
    celda.innerHTML = `<div class="day-header">${dia}</div>`;

    // 🔸 Buscar programaciones de ese día
    const eventosDelDia = programaciones.filter(ev => ev.Fecha === celda.dataset.fecha);

    // 🔹 Etiquetas de colores según el tipo
    if (eventosDelDia.length > 0) {
      const tipos = [...new Set(eventosDelDia.map(ev => ev.Tipo))];
      const colores = {
        "Entregas": "bg-success",
        "Instalaciones": "bg-primary",
        "Reuniones internas": "bg-danger",
        "Eventos": "bg-danger"
      };

      const etiquetas = tipos.map(t => {
        const color = colores[t] || "bg-secondary";
        return `<span class="badge ${color} me-1">${t}</span>`;
      }).join("");

      celda.innerHTML += `<div class="event-tags mt-1">${etiquetas}</div>`;
    }

    // 🔸 Resaltar día actual
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
// 🔹 Botón "Mes" → Selector de mes/año
// =============================================================
btnMes.addEventListener("click", () => {
  const selectorMes = document.createElement("input");
  selectorMes.type = "month";
  selectorMes.style.position = "absolute";
  selectorMes.style.opacity = "0";
  selectorMes.style.pointerEvents = "none";
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
// 🔹 Botón "Año" → Cambiar año manteniendo el mes actual
// =============================================================
btnAño.addEventListener("click", () => {
  const añoActual = fechaActual.getFullYear();
  const nuevoAño = prompt("Ingrese un año:", añoActual);

  if (nuevoAño && !isNaN(nuevoAño)) {
    const mes = fechaActual.getMonth();
    fechaActual = new Date(parseInt(nuevoAño), mes, 1);
    renderCalendario(fechaActual);
  }
});

// =============================================================
// 🔹 Clic en un día → Mostrar modal con programaciones
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
        <p class="mt-3 mb-0 fs-5 text-muted">No tienes nada programado hoy.</p>
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
              </div>
            </div>
          `).join("")}
        </div>
      `).join("");
  }

  modal.show();
});

// =============================================================
// 🔹 Inicializar
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
  cargarProgramaciones();
});
