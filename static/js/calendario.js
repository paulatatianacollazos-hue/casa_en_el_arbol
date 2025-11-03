// =============================================================
// 📅 CALENDARIO DINÁMICO - EMPLEADO
// =============================================================

// Selección de elementos del DOM
const grid = document.getElementById("calendarioGrid");
const mesTitulo = document.getElementById("mesTitulo");
const btnHoy = document.getElementById("btnHoy");
const btnMes = document.getElementById("btnMes");
const btnDia = document.getElementById("btnDia");

let fechaActual = new Date();
let vistaActual = "mes";

// =============================================================
// 🔹 Función principal: Renderizar calendario
// =============================================================
function renderCalendario(fecha) {
  grid.innerHTML = ""; // Limpia el calendario

  const año = fecha.getFullYear();
  const mes = fecha.getMonth();
  const primerDia = new Date(año, mes, 1);
  const ultimoDia = new Date(año, mes + 1, 0);
  const primerDiaSemana = primerDia.getDay() === 0 ? 6 : primerDia.getDay() - 1;

  mesTitulo.textContent = fecha.toLocaleDateString("es-ES", {
    month: "long",
    year: "numeric"
  });

  // Espacios vacíos antes del primer día
  for (let i = 0; i < primerDiaSemana; i++) {
    const celdaVacia = document.createElement("div");
    celdaVacia.classList.add("day", "empty");
    grid.appendChild(celdaVacia);
  }

  // Días del mes
  for (let dia = 1; dia <= ultimoDia.getDate(); dia++) {
    const fechaDia = new Date(año, mes, dia);
    const celda = document.createElement("div");
    celda.classList.add("day", "border", "rounded", "p-2");
    celda.dataset.fecha = fechaDia.toISOString().split("T")[0];
    celda.innerHTML = `<span class="fw-bold">${dia}</span>`;
    grid.appendChild(celda);
  }
}

// =============================================================
// 🔹 Eventos de navegación
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
// 🔹 Al hacer clic en un día → Mostrar pedidos en modal
// =============================================================
grid.addEventListener("click", async (e) => {
  const celda = e.target.closest(".day");
  if (!celda || celda.classList.contains("empty")) return;

  const fechaSeleccionada = celda.dataset.fecha;
  const modal = new bootstrap.Modal(document.getElementById("modalPedidosDia"));
  const contenido = document.getElementById("contenidoPedidosDia");

  contenido.innerHTML = "<div class='text-muted'>Cargando pedidos...</div>";

  try {
    const resp = await fetch(`/empleado/pedidos/${fechaSeleccionada}`);
    const data = await resp.json();

    if (!data || data.length === 0) {
      contenido.innerHTML = `
        <div class="d-flex flex-column align-items-center justify-content-center py-4">
          <i class="bi bi-calendar-x text-secondary" style="font-size: 3rem;"></i>
          <p class="mt-3 mb-0 fs-5 text-muted">No tienes nada programado hoy.</p>
        </div>`;
    } else {
      contenido.innerHTML = data.map(p => `
        <div class="card mb-3 shadow-sm border-success">
          <div class="card-body text-start">
            <h6 class="card-title mb-1 fw-bold">Pedido #${p.ID_Pedido}</h6>
            <p class="mb-0"><strong>Ubicación:</strong> ${p.Ubicacion}</p>
            <p class="mb-0"><strong>Hora:</strong> ${p.Hora}</p>
            <p class="mb-0"><strong>Tipo:</strong> ${p.Tipo}</p>
          </div>
        </div>
      `).join("");
    }
  } catch (err) {
    console.error("Error al obtener pedidos:", err);
    contenido.innerHTML = `<div class="alert alert-danger">Error al cargar pedidos.</div>`;
  }

  modal.show();
});

// =============================================================
// 🔹 Inicializar calendario al cargar
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
  renderCalendario(fechaActual);
});
