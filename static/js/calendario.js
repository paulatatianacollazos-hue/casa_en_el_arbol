// =============================================================
// 📅 CALENDARIO DINÁMICO - EMPLEADO (CORREGIDO)
// =============================================================

// 🔸 Elementos del DOM
const grid = document.getElementById("calendar-grid");
const mesTitulo = document.getElementById("titulo-mes");
const btnHoy = document.getElementById("btn-hoy");
const btnMes = document.getElementById("btn-mes");
const btnDia = document.getElementById("btn-dia");

let fechaActual = new Date();
let vistaActual = "mes";

// =============================================================
// 🔹 Función: Renderizar calendario del mes
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
  }).toUpperCase();

  // Espacios vacíos antes del primer día
  for (let i = 0; i < primerDiaSemana; i++) {
    const celdaVacia = document.createElement("div");
    celdaVacia.classList.add("day", "empty");
    grid.appendChild(celdaVacia);
  }

  // Días del mes
  for (let dia = 1; dia <= ultimoDia.getDate(); dia++) {
    const fechaDia = new Date(año, mes, dia);
    const fechaISO = fechaDia.toISOString().split("T")[0];
    const celda = document.createElement("div");
    celda.classList.add("day");
    celda.dataset.fecha = fechaISO;
    celda.innerHTML = `
      <div class="day-header">${dia}</div>
      <div class="event-container"></div>
    `;
    grid.appendChild(celda);
  }
}

// =============================================================
// 🔹 Botones de navegación
// =============================================================
btnHoy.addEventListener("click", () => {
  fechaActual = new Date();
  renderCalendario(fechaActual);
});

btnMes.addEventListener("click", () => {
  vistaActual = "mes";
  renderCalendario(fechaActual);
});

btnDia.addEventListener("click", () => {
  vistaActual = "dia";
  renderCalendario(fechaActual);
});

// =============================================================
// 🔹 Mostrar pedidos del día (al hacer clic en una celda)
// =============================================================
grid.addEventListener("click", async (e) => {
  const celda = e.target.closest(".day");
  if (!celda || celda.classList.contains("empty")) return;

  const fechaSeleccionada = celda.dataset.fecha;
  const modal = new bootstrap.Modal(document.getElementById("modalPedidosDia"));
  const contenido = document.getElementById("contenidoPedidosDia");

  contenido.innerHTML = `
    <div class="text-center text-muted py-3">
      <div class="spinner-border text-success" role="status"></div>
      <p class="mt-3 mb-0">Cargando pedidos...</p>
    </div>
  `;

  try {
    const respuesta = await fetch(`/empleado/pedidos/${fechaSeleccionada}`);
    const pedidos = await respuesta.json();

    if (!pedidos || pedidos.length === 0) {
      contenido.innerHTML = `
        <div class="d-flex flex-column align-items-center justify-content-center py-4">
          <i class="bi bi-calendar-x text-secondary" style="font-size: 3rem;"></i>
          <p class="mt-3 mb-0 fs-5 text-muted">No tienes nada programado hoy.</p>
        </div>`;
    } else {
      contenido.innerHTML = pedidos.map(p => `
        <div class="card mb-3 border-success shadow-sm">
          <div class="card-body">
            <h6 class="card-title mb-1 fw-bold">Pedido #${p.ID_Pedido}</h6>
            <p class="mb-1"><strong>Ubicación:</strong> ${p.Ubicacion}</p>
            <p class="mb-1"><strong>Hora:</strong> ${p.Hora}</p>
            <p class="mb-0"><strong>Tipo:</strong> ${p.Tipo}</p>
          </div>
        </div>
      `).join("");
    }
  } catch (error) {
    console.error("Error al cargar pedidos:", error);
    contenido.innerHTML = `
      <div class="alert alert-danger text-center">
        Error al cargar los pedidos del día.
      </div>`;
  }

  modal.show();
});

// =============================================================
// 🔹 Inicializar calendario
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
  renderCalendario(fechaActual);
});
