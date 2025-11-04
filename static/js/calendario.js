// =============================================================
// 📅 CALENDARIO DINÁMICO CON SELECCIÓN DE USUARIO
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
let usuarioSeleccionado = "mi"; // por defecto "Mi calendario"

// =============================================================
// 🔹 Cargar usuarios (transportistas e instaladores)
// =============================================================
async function cargarUsuarios() {
  try {
    const resp = await fetch("/empleado/usuarios_calendario");
    usuarios = await resp.json();

    // Insertar opciones dinámicamente
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

  // Celdas vacías al inicio
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

  // Días del mes
  for (let dia = 1; dia <= ultimoDia.getDate(); dia++) {
    const fechaDia = new Date(año, mes, dia);
    const fechaStr = fechaDia.toISOString().split("T")[0];

    const celda = document.createElement("div");
    celda.classList.add("day");
    celda.dataset.fecha = fechaStr;
    celda.innerHTML = `<div class="day-header">${dia}</div>`;

    // Filtrar eventos de ese día
    const eventosDelDia = eventosFiltrados.filter(ev => ev.Fecha === fechaStr);

    if (eventosDelDia.length > 0) {
      const tipos = [...new Set(eventosDelDia.map(ev => ev.Tipo))];
      const colores = {
        "Entregas": "bg-success",
        "Instalaciones": "bg-primary",
        "Reunion": "bg-warning",
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

    // Día actual
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
// 🔹 Eventos de control
// =============================================================

selectorUsuario.addEventListener("change", (e) => {
  usuarioSeleccionado = e.target.value;
  renderCalendario(fechaActual);
});

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

async function cargarUsuarios() {
  try {
    const resp = await fetch("/empleado/usuarios_calendario");
    usuarios = await resp.json();

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
// 🔹 Inicialización
// =============================================================
document.addEventListener("DOMContentLoaded", async () => {
  await cargarUsuarios();
  await cargarProgramaciones();
});
