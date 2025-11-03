document.addEventListener('DOMContentLoaded', function() {
  const calendarEl = document.getElementById('calendar');

  const calendar = new FullCalendar.Calendar(calendarEl, {
    locale: 'es',
    initialView: 'dayGridMonth',
    headerToolbar: {
      left: 'today,dayGridMonth,timeGridDay',
      center: 'title',
      right: ''
    },
    buttonText: { today: 'Hoy', month: 'Mes', day: 'Día' },
    height: 'auto',
    events: '/calendario/eventos',
    eventClick: function(info) {
      const detalle = `
        <h6>${info.event.title}</h6>
        <p><b>Tipo:</b> ${info.event.extendedProps.tipo}</p>
        <p><b>Ubicación:</b> ${info.event.extendedProps.ubicacion}</p>
        <p><b>Pedido:</b> ${info.event.extendedProps.id_pedido}</p>
        <p><b>Fecha:</b> ${info.event.start.toLocaleDateString()}</p>
        <p><b>Hora:</b> ${info.event.start.toLocaleTimeString()}</p>
        <button id="editar" class="btn btn-warning btn-sm">Editar</button>
        <button id="eliminar" class="btn btn-danger btn-sm">Eliminar</button>
      `;
      document.getElementById('detalle-tarea').innerHTML = detalle;

      document.getElementById('eliminar').onclick = async () => {
        if (confirm("¿Eliminar este evento?")) {
          await fetch(`/calendario/eventos/${info.event.id}`, { method: 'DELETE' });
          calendar.refetchEvents();
        }
      };
    }
  });

  calendar.render();

  // Botón subir tarea
  document.querySelector('.btn-success').addEventListener('click', async () => {
    const nueva = {
      Fecha: prompt("Fecha (YYYY-MM-DD):"),
      Hora: prompt("Hora (HH:MM):"),
      Ubicacion: prompt("Ubicación:"),
      ID_Usuario: 1,
      ID_Pedido: prompt("ID Pedido:"),
      Tipo: prompt("Tipo (Entrega / Reunión / Instalación):")
    };
    await fetch('/calendario/eventos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(nueva)
    });
    calendar.refetchEvents();
  });
});
