// =============================================================
// 📅 CALENDARIO DINÁMICO - EMPLEADO (Pedidos + otros eventos)
// =============================================================

const grid = document.getElementById("calendar-grid");
const mesTitulo = document.getElementById("titulo-mes");
const btnHoy = document.getElementById("btn-hoy");
const btnMes = document.getElementById("btn-mes");
const btnAño = document.getElementById("btn-año");
const btnDia = document.getElementById("btn-dia");

let fechaActual = new Date();
let vistaActual = "mes";

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

  for (let i = 0; i < primerDiaSemana; i++) {
    const celdaVacia = document.createElement("div");
    celdaVacia.classList.add("day", "empty");
    grid.appendChild(celdaVacia);
  }

  for (let dia = 1; dia <= ultimoDia.getDate(); dia++) {
    const fechaDia = new Date(año, mes, dia);
    const celda = document.createElement("div");
    celda.classList.add("day");
    celda.dataset.fecha = fechaDia.toISOString().split("T")[0];
    celda.innerHTML = `<div class="day-header">${dia}</div>`;

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
// 🔹 Botón "Mes" → Seleccionar mes y año
// =============================================================
btnMes.addEventListener("click", () => {
  const selectorMes = document.createElement("input");
  selectorMes.type = "month";
  selectorMes.classList.add("form-control");
  selectorMes.style.position = "absolute";
  selectorMes.style.opacity = "0";
  selectorMes.style.pointerEvents = "none";
  document.body.appendChild(selectorMes);

  // Valor inicial
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
// 🔹 Botón "Año" → Seleccionar año (manteniendo el mes actual)
// =============================================================
btnAño.addEventListener("click", () => {
  const selectorAño = document.createElement("input");
  selectorAño.type = "number";
  selectorAño.min = "1900";
  selectorAño.max = "2100";
  selectorAño.value = fechaActual.getFullYear();
  selectorAño.classList.add("form-control");
  selectorAño.style.position = "absolute";
  selectorAño.style.opacity = "0";
  selectorAño.style.pointerEvents = "none";
  document.body.appendChild(selectorAño);

  selectorAño.addEventListener("change", (e) => {
    const nuevoAño = parseInt(e.target.value);
    const mes = fechaActual.getMonth();
    fechaActual = new Date(nuevoAño, mes, 1);
    renderCalendario(fechaActual);
    document.body.removeChild(selectorAño);
  });

  selectorAño.showPicker?.();
  selectorAño.click();
});

// =============================================================
// 🔹 Clic en día → mostrar modal con programaciones
// =============================================================
grid.addEventListener("click", async (e) => {
  const celda = e.target.closest(".day");
  if (!celda || celda.classList.contains("empty")) return;

  const fechaSeleccionada = celda.dataset.fecha;
  const modal = new bootstrap.Modal(document.getElementById("modalPedidosDia"));
  const contenido = document.getElementById("contenidoPedidosDia");
  document.getElementById("modalPedidosDiaLabel").textContent =
    "Programaciones del " + new Date(fechaSeleccionada).toLocaleDateString("es-ES");

  contenido.innerHTML = "<div class='text-muted'>Cargando programaciones...</div>";

  try {
    const resp = await fetch(`/empleado/programaciones/${fechaSeleccionada}`);
    const data = await resp.json();

    if (!data || data.length === 0) {
      contenido.innerHTML = `
        <div class="d-flex flex-column align-items-center justify-content-center py-4">
          <i class="bi bi-calendar-x text-secondary" style="font-size: 3rem;"></i>
          <p class="mt-3 mb-0 fs-5 text-muted">No tienes nada programado hoy.</p>
        </div>`;
    } else {
      // Agrupar por tipo
      const grupos = {};
      data.forEach(item => {
        if (!grupos[item.Tipo]) grupos[item.Tipo] = [];
        grupos[item.Tipo].push(item);
      });

      contenido.innerHTML = Object.entries(grupos)
        .map(([tipo, eventos]) => `
          <div class="mb-4">
            <h6 class="fw-bold text-success text-uppercase border-bottom pb-1 mb-2">${tipo}</h6>
            ${eventos.map(ev => `
              <div class="card mb-2 border-success">
                <div class="card-body text-start">
                  <h6 class="card-title mb-1 fw-bold">#${ev.ID_Pedido || ev.ID_Calendario}</h6>
                  <p class="mb-0"><strong>Ubicación:</strong> ${ev.Ubicacion || "Sin especificar"}</p>
                  <p class="mb-0"><strong>Hora:</strong> ${ev.Hora || "No definida"}</p>
                  <p class="mb-0"><strong>Descripción:</strong> ${ev.Descripcion || "Sin detalles"}</p>
                </div>
              </div>
            `).join("")}
          </div>
        `).join("");
    }
  } catch (err) {
    console.error("Error al obtener programaciones:", err);
    contenido.innerHTML = `<div class="alert alert-danger">Error al cargar programaciones.</div>`;
  }

  modal.show();
});

// =============================================================
// 🔹 Inicializar al cargar
// =============================================================
document.addEventListener("DOMContentLoaded", () => {
  renderCalendario(fechaActual);
});
