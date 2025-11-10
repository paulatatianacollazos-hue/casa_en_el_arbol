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
    const userId = window.FLASK_USER_ID || "anonimo";
    const key = "reseñas_pedidos_" + userId;
    const reseñas = JSON.parse(localStorage.getItem(key) || "[]");

    if (!reseñas.length) {
      alert("No hay reseñas registradas todavía.");
      return;
    }

    const desdeInput = document.querySelector("[name='desde']").value;
    const hastaInput = document.querySelector("[name='hasta']").value;

    const desde = desdeInput ? new Date(desdeInput) : null;
    const hasta = hastaInput ? new Date(hastaInput) : null;

    const filtradas = reseñas.filter(r => {
      const fecha = new Date(r.fecha);
      if (desde && fecha < desde) return false;
      if (hasta && fecha > hasta) return false;
      return true;
    });

    if (!filtradas.length) {
      alert("No hay reseñas dentro del rango de fechas seleccionado.");
      return;
    }

    const total = filtradas.length;
    const positivas = filtradas.filter(r => Number(r.estrellas) >= 4).length;
    const neutras = filtradas.filter(r => Number(r.estrellas) === 3).length;
    const negativas = filtradas.filter(r => Number(r.estrellas) <= 2).length;
    const promedio = filtradas.reduce((s, r) => s + Number(r.estrellas), 0) / total;

    txtTotal.textContent = `Total reseñas: ${total}`;
    promedioGeneral.textContent = `${promedio.toFixed(2)} ⭐`;

    // Pie chart
    if (pieChart) pieChart.destroy();
    pieChart = new Chart(pieCanvas, {
      type: "pie",
      data: {
        labels: ["Positivas", "Neutras", "Negativas"],
        datasets: [{ data: [positivas, neutras, negativas], backgroundColor: ["#4caf50", "#ffca28", "#f44336"] }]
      },
      options: { plugins: { legend: { position: "bottom" } } }
    });

    // Bar chart
    const agrupadas = agruparPorMes(filtradas);
    if (barChart) barChart.destroy();
    barChart = new Chart(barsCanvas, {
      type: "bar",
      data: { labels: Object.keys(agrupadas), datasets: [{ label: "Promedio de estrellas", data: Object.values(agrupadas), backgroundColor: "#42a5f5" }] },
      options: { scales: { y: { beginAtZero: true, max: 5 } } }
    });

    // Tabla negativos
    const negativos = filtradas.filter(r => Number(r.estrellas) <= 2);
    negTable.innerHTML = negativos.length
      ? negativos.map(r => `<tr><td>${r.idProducto || "Pedido N/A"}</td><td>${r.comentario}</td></tr>`).join("")
      : "<tr><td colspan='2' class='text-center text-muted'>No hay comentarios negativos.</td></tr>";
  }

  function agruparPorMes(reseñas) {
    const meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"];
    const res = {};

    reseñas.forEach(r => {
      const f = new Date(r.fecha);
      const key = meses[f.getMonth()] + " " + f.getFullYear();
      if (!res[key]) res[key] = { suma: 0, n: 0 };
      res[key].suma += Number(r.estrellas);
      res[key].n++;
    });

    const resultado = {};
    for (const k in res) resultado[k] = +(res[k].suma / res[k].n).toFixed(2);
    return resultado;
  }
});
