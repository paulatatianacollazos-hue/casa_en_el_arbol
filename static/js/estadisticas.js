document.addEventListener("DOMContentLoaded", () => {
  const btnGen = document.getElementById("btnGen");
  const pieCanvas = document.getElementById("pie");
  const barsCanvas = document.getElementById("bars");
  const negTable = document.getElementById("negTable");
  const txtTotal = document.getElementById("txtTotal");
  const promedioGeneral = document.getElementById("promedioGeneral");

  let pieChart, barChart;

  btnGen.addEventListener("click", generarEstadisticas);

  function generarEstadisticas() {
    // 🔹 Cargar todas las reseñas del localStorage
    const reseñas = JSON.parse(localStorage.getItem("reseñas") || "[]");

    if (reseñas.length === 0) {
      alert("No hay reseñas registradas todavía.");
      return;
    }

    // 🔹 Filtrar por fechas si se seleccionaron
    const desde = document.querySelector("[name='desde']").value
      ? new Date(document.querySelector("[name='desde']").value)
      : null;
    const hasta = document.querySelector("[name='hasta']").value
      ? new Date(document.querySelector("[name='hasta']").value)
      : null;

    const filtradas = reseñas.filter(r => {
      const fecha = new Date(r.fecha);
      if (desde && fecha < desde) return false;
      if (hasta && fecha > hasta) return false;
      return true;
    });

    if (filtradas.length === 0) {
      alert("No hay reseñas dentro del rango de fechas seleccionado.");
      return;
    }

    // 🔹 Calcular estadísticas
    const total = filtradas.length;
    const positivas = filtradas.filter(r => Number(r.estrellas) >= 4).length;
    const neutras = filtradas.filter(r => Number(r.estrellas) === 3).length;
    const negativas = filtradas.filter(r => Number(r.estrellas) <= 2).length;
    const promedio =
      filtradas.reduce((s, r) => s + Number(r.estrellas), 0) / total;

    txtTotal.textContent = `Total reseñas: ${total}`;
    promedioGeneral.textContent = `${promedio.toFixed(2)} ⭐`;

    // 🔹 Gráfico circular (Positivas / Neutras / Negativas)
    if (pieChart) pieChart.destroy();
    pieChart = new Chart(pieCanvas, {
      type: "pie",
      data: {
        labels: ["Positivas", "Neutras", "Negativas"],
        datasets: [
          {
            data: [positivas, neutras, negativas],
            backgroundColor: ["#4caf50", "#ffca28", "#f44336"]
          }
        ]
      },
      options: {
        plugins: {
          legend: { position: "bottom" }
        }
      }
    });

    // 🔹 Gráfico de barras (promedio por mes)
    const agrupadas = agruparPorMes(filtradas);
    const meses = Object.keys(agrupadas);
    const valores = Object.values(agrupadas);

    if (barChart) barChart.destroy();
    barChart = new Chart(barsCanvas, {
      type: "bar",
      data: {
        labels: meses,
        datasets: [
          {
            label: "Promedio de estrellas",
            data: valores,
            backgroundColor: "#42a5f5"
          }
        ]
      },
      options: {
        scales: {
          y: { beginAtZero: true, max: 5 }
        }
      }
    });

    // 🔹 Tabla de comentarios negativos
    const negativos = filtradas.filter(r => Number(r.estrellas) <= 2);
    negTable.innerHTML = negativos.length
      ? negativos
          .map(
            r =>
              `<tr><td>${r.idProducto || "Pedido N/A"}</td><td>${r.comentario}</td></tr>`
          )
          .join("")
      : "<tr><td colspan='2' class='text-center text-muted'>No hay comentarios negativos.</td></tr>";
  }

  function agruparPorMes(reseñas) {
    const mesesNombre = [
      "Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"
    ];
    const agrupado = {};

    reseñas.forEach(r => {
      const f = new Date(r.fecha);
      const key = mesesNombre[f.getMonth()] + " " + f.getFullYear();
      if (!agrupado[key]) agrupado[key] = { suma: 0, n: 0 };
      agrupado[key].suma += Number(r.estrellas);
      agrupado[key].n++;
    });

    const resultado = {};
    for (const k in agrupado) {
      resultado[k] = (agrupado[k].suma / agrupado[k].n).toFixed(2);
    }
    return resultado;
  }
});
