// Datos simulados
const DATA = (() => {
  const prods = ['Producto A','Producto B','Producto C'];
  const out = [];
  for(let i=0; i<160; i++){
    const d = new Date();
    d.setDate(d.getDate() - Math.floor(Math.random()*210));
    out.push({
      product: prods[Math.floor(Math.random()*prods.length)],
      rating: 1 + Math.floor(Math.random()*5),
      date: d.toISOString().slice(0,10)
    });
  }
  return out;
})();

function filterData(from,to){
  const f = from ? new Date(from) : null;
  const t = to ? new Date(to) : null;
  return DATA.filter(r => {
    const d = new Date(r.date);
    if(f && d < f) return false;
    if(t && d > t) return false;
    return true;
  });
}

function genStats(){
  const desde = document.querySelector('[name=desde]').value;
  const hasta = document.querySelector('[name=hasta]').value;
  const subset = filterData(desde,hasta);

  const total = subset.length;
  const positives = subset.filter(x=>x.rating>=4).length;
  const negatives = subset.filter(x=>x.rating<=2).length;
  const neutrals  = subset.filter(x=>x.rating===3).length;

  document.getElementById('txtTotal').textContent = `Total respuestas: ${total}`;

  // Pie chart en tonos verdes
  const pieCtx = document.getElementById('pie').getContext('2d');
  if(window._pie) window._pie.destroy();
  window._pie = new Chart(pieCtx, {
    type:'pie',
    data:{
      labels:['Positivas','Neutrales','Negativas'],
      datasets:[{
        data:[positives, neutrals, negatives],
        backgroundColor: [
          'rgba(0,128,0,0.8)',    // verde fuerte
          'rgba(60,179,113,0.8)', // verde medio
          'rgba(144,238,144,0.8)' // verde claro
        ],
        borderColor: [
          'rgba(0,100,0,1)',
          'rgba(46,139,87,1)',
          'rgba(34,139,34,1)'
        ],
        borderWidth: 1
      }]
    }
  });

  // Barras por mes en verde
  const months = {};
  subset.forEach(r => {
    const ym = r.date.slice(0,7); // YYYY-MM
    months[ym] = (months[ym]||0) + 1;
  });
  const labels = Object.keys(months).sort();
  const vals = labels.map(l=>months[l]);
  const barsCtx = document.getElementById('bars').getContext('2d');
  if(window._bars) window._bars.destroy();
  window._bars = new Chart(barsCtx, {
    type:'bar',
    data:{
      labels,
      datasets:[{
        label:'Respuestas',
        data:vals,
        backgroundColor:'rgba(0,128,0,0.7)',
        borderColor:'rgba(0,100,0,1)',
        borderWidth:1
      }]
    },
    options:{
      scales:{
        y:{ beginAtZero:true }
      }
    }
  });

  // Negativos por producto
  const neg = {};
  subset.forEach(r => { if(r.rating<=2) neg[r.product] = (neg[r.product]||0)+1; });
  const tbody = document.getElementById('negTable');
  tbody.innerHTML = Object.keys(neg).length
    ? Object.keys(neg).map(k=>`<tr><td>${k}</td><td>${neg[k]}</td></tr>`).join('')
    : '<tr><td colspan="2" class="text-muted">Sin datos</td></tr>';
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('btnGen').addEventListener('click', genStats);
  genStats();
});
