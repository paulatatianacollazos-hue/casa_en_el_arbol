document.addEventListener("DOMContentLoaded", () => {
  const btnGen = document.getElementById("btnGen");
  const pieCanvas = document.getElementById("pie");
  const barsCanvas = document.getElementById("bars");
  const negTable = document.getElementById("negTable");
  const txtTotal = document.getElementById("txtTotal");

  let pieChart, barChart;

  btnGen.addEventListener("click", generarEstadisticas);

  function generarEstadisticas() {
    // 🔹 Cargar reseñas del localStorage (cada usuario tiene su clave)
    const userId = window.FLASK_USER_ID || "anonimo";
    const key = "reseñas_pedidos_" + userId;
    const reseñas = JSON.parse(localStorage.getItem(key) || "[]");

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

    // 🔹 Calcular estadísticas básicas
    const total = filtradas.length;
    const positivas = filtradas.filter(r => r.estrellas >= 4).length;
    const neutras = filtradas.filter(r => r.estrellas === 3).length;
    const negativas = filtradas.filter(r => r.estrellas <= 2).length;
    const promedio =
      filtradas.reduce((s, r) => s + Number(r.estrellas), 0) / total;

    txtTotal.textContent = `Total reseñas: ${total} | Promedio general: ${promedio.toFixed(2)} ⭐`;

    // 🔹 Generar gráfico circular (positivas / neutras / negativas)
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
      }
    });

    // 🔹 Generar gráfico de barras por mes
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
            label: "Promedio de estrellas por mes",
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

    // 🔹 Mostrar tabla de comentarios negativos
    const negativos = filtradas.filter(r => r.estrellas <= 2);
    negTable.innerHTML = negativos.length
      ? negativos
          .map(
            r =>
              `<tr><td>${r.idPedido || "Pedido N/A"}</td><td>${r.comentario}</td></tr>`
          )
          .join("")
      : "<tr><td colspan='2'>No hay comentarios negativos.</td></tr>";
  }

  function agruparPorMes(reseñas) {
    const meses = [
      "Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"
    ];
    const agrupado = {};
    reseñas.forEach(r => {
      const f = new Date(r.fecha);
      const key = meses[f.getMonth()] + " " + f.getFullYear();
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
