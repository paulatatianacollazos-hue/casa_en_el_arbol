document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btnGen");
  const promedioGeneral = document.getElementById("promedioGeneral");
  const txtTotal = document.getElementById("txtTotal");
  const negTable = document.getElementById("negTable");
  const tipoChartContainer = document.getElementById("tipoChartContainer");

  let pieChart, barChart, tipoChart;

  // 🔹 Función principal para cargar estadísticas
  async function cargarEstadisticas() {
    try {
      const resp = await fetch("/admin/estadisticas_reseñas");
      const data = await resp.json();

      actualizarResumen(data);
      generarGraficoPie(data.por_estrellas);
      generarGraficoBarras(data.por_mes);
      generarGraficoTipo(data.por_tipo);
      llenarTablaNegativos(data.negativos);
    } catch (err) {
      console.error("Error al cargar estadísticas:", err);
      alert("Ocurrió un error al generar las estadísticas.");
    }
  }

  // 🔹 Ejecutar al hacer clic en el botón
  btn.addEventListener("click", cargarEstadisticas);

  // 🔹 También cargar automáticamente al abrir la página
  cargarEstadisticas();

  // ------------------------------
  // Funciones auxiliares de render
  // ------------------------------

  function actualizarResumen(data) {
    promedioGeneral.textContent = data.promedio_general.toFixed(2);
    txtTotal.textContent = `Basado en ${data.total} reseña(s) registradas.`;
  }

  function generarGraficoPie(por_estrellas) {
    const ctx = document.getElementById("pie");
    if (pieChart) pieChart.destroy();

    pieChart = new Chart(ctx, {
      type: "pie",
      data: {
        labels: ["1 ⭐", "2 ⭐", "3 ⭐", "4 ⭐", "5 ⭐"],
        datasets: [{
          data: por_estrellas,
          backgroundColor: [
            "#dc3545", "#fd7e14", "#ffc107", "#0d6efd", "#198754"
          ]
        }]
      },
      options: {
        plugins: {
          legend: { position: "bottom" },
          title: { display: true, text: "Distribución de estrellas" }
        }
      }
    });
  }

  function generarGraficoBarras(por_mes) {
    const ctx = document.getElementById("bars");
    if (barChart) barChart.destroy();

    barChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: por_mes.map(m => m.mes),
        datasets: [{
          label: "Promedio de estrellas",
          data: por_mes.map(m => m.promedio),
          backgroundColor: "#0d6efd"
        }]
      },
      options: {
        scales: { y: { beginAtZero: true, max: 5 } },
        plugins: { legend: { display: false } }
      }
    });
  }

  function generarGraficoTipo(por_tipo) {
    const ctxId = "tipoChart";
    tipoChartContainer.innerHTML = `<canvas id="${ctxId}" style="max-height: 300px;"></canvas>`;
    const ctx = document.getElementById(ctxId);
    if (tipoChart) tipoChart.destroy();

    const total = por_tipo.producto + por_tipo.pedido;
    const pctProductos = total ? ((por_tipo.producto / total) * 100).toFixed(1) : 0;
    const pctPedidos = total ? ((por_tipo.pedido / total) * 100).toFixed(1) : 0;

    tipoChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: [`Productos (${pctProductos}%)`, `Pedidos (${pctPedidos}%)`],
        datasets: [{
          data: [por_tipo.producto, por_tipo.pedido],
          backgroundColor: ["#198754", "#0d6efd"]
        }]
      },
      options: {
        plugins: {
          legend: { position: "bottom" },
          title: { display: true, text: "Comparativa de reseñas por tipo" }
        }
      }
    });
  }

  function llenarTablaNegativos(negativos) {
    if (!negativos || negativos.length === 0) {
      negTable.innerHTML = `<tr><td colspan="2" class="text-center text-muted">Aún no hay datos</td></tr>`;
      return;
    }

    negTable.innerHTML = negativos
      .map(n => `
        <tr>
          <td>#${n.pedido}</td>
          <td>${n.comentario}</td>
        </tr>
      `)
      .join("");
  }
});
