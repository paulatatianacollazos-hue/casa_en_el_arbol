(async function() {
  const fechas = await fetch('/api/available_dates').then(r => r.json());
  const cal = document.getElementById('calendar');
  const seleccion = { fecha: null, productos: [] };

  fechas.rango.forEach(d => {
    const btn = document.createElement('button');
    btn.textContent = new Date(d).getDate();
    btn.dataset.fecha = d;
    btn.addEventListener('click', () => {
      document.querySelectorAll('#calendar button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      seleccion.fecha = d;
    });
    cal.appendChild(btn);
  });

  const productos = await fetch(`/api/user_products/${USER_ID}`).then(r => r.json());
  const cont = document.getElementById('productsList');
  cont.innerHTML = '';
  productos.forEach(p => {
    const div = document.createElement('div');
    div.className = 'producto';
    div.innerHTML = `
      <input type="checkbox" value="${p.id}">
      <img src="${p.imagen}">
      <span>${p.nombre} (x${p.cantidad}) - $${p.precio}</span>
    `;
    const chk = div.querySelector('input');
    chk.addEventListener('change', e => {
      if (e.target.checked) seleccion.productos.push(p.id);
      else seleccion.productos = seleccion.productos.filter(id => id !== p.id);
    });
    cont.appendChild(div);
  });

  document.getElementById('confirmBtn').addEventListener('click', () => {
    if (!seleccion.fecha) return alert('Selecciona una fecha');
    if (seleccion.productos.length === 0) return alert('Selecciona al menos un producto');
    const servicio = document.getElementById('serviceSelect').value;
    alert(`✅ Datos seleccionados:\nFecha: ${seleccion.fecha}\nServicio: ${servicio}\nProductos: ${seleccion.productos.join(', ')}`);
  });
})();
