(() => {
  'use strict';
  const menuButton = document.querySelector('[data-menu-toggle]');
  const menu = document.querySelector('[data-navigation]');
  const closeMenu = () => {
    if (!menuButton || !menu) return;
    menuButton.setAttribute('aria-expanded', 'false');
    menuButton.setAttribute('aria-label', 'Abrir menú');
    menu.classList.remove('is-open');
  };
  if (menuButton && menu) {
    menuButton.addEventListener('click', () => {
      const open = menuButton.getAttribute('aria-expanded') !== 'true';
      menuButton.setAttribute('aria-expanded', String(open));
      menuButton.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
      menu.classList.toggle('is-open', open);
    });
    menu.querySelectorAll('a').forEach(a => a.addEventListener('click', closeMenu));
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') {
        closeMenu(); menuButton.focus();
      }
    });
    document.addEventListener('click', e => {
      if (!e.target.closest('.site-header')) closeMenu();
    });
    window.matchMedia('(min-width: 721px)').addEventListener('change', e => {
      if (e.matches) closeMenu();
    });
  }

  const filterButtons = document.querySelectorAll('[data-filter]');
  const serviceCards = document.querySelectorAll('[data-audiences]');
  const count = document.querySelector('[data-result-count]');
  filterButtons.forEach(button => button.addEventListener('click', () => {
    const filter = button.dataset.filter;
    filterButtons.forEach(other => other.setAttribute('aria-pressed', String(other === button)));
    let visible = 0;
    serviceCards.forEach(card => {
      const show = filter === 'todos' || card.dataset.audiences.split(' ').includes(filter);
      card.hidden = !show;
      if (show) visible++;
    });
    if (count) count.textContent = `${visible} áreas de servicio`;
  }));

  const form = document.querySelector('[data-budget-form]');
  if (!form) return;
  form.noValidate = true;
  const service = form.querySelector('[name="necesitas"]');
  const queryService = new URLSearchParams(window.location.search).get('servicio');
  if (service && queryService && [...service.options].some(o => o.value === queryService)) {
    service.value = queryService;
  }
  const status = form.querySelector('[data-form-status]');
  const submit = form.querySelector('button[type="submit"]');
  const dialog = document.querySelector('[data-request-dialog]');
  const summary = dialog?.querySelector('[data-request-summary]');
  let requestText = '';
  const setStatus = (message, kind = '') => {
    status.textContent = message;
    status.className = `form-status ${kind}`;
  };
  form.addEventListener('input', e => {
    if (e.target.matches('input,select,textarea')) e.target.removeAttribute('aria-invalid');
  });
  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (submit.disabled || form.querySelector('[name="botcheck"]').checked) return;
    const inputs = [...form.querySelectorAll('input,select,textarea')].filter(i => i.willValidate);
    const firstInvalid = inputs.find(i => !i.checkValidity());
    if (firstInvalid) {
      inputs.forEach(i => {
        if (!i.checkValidity()) i.setAttribute('aria-invalid', 'true');
        else i.removeAttribute('aria-invalid');
      });
      setStatus('Revisa los campos obligatorios y el formato del correo electrónico.', 'error');
      firstInvalid.focus();
      firstInvalid.reportValidity();
      return;
    }
    const data = new FormData(form);
    const endpoint = form.dataset.endpoint;
    if (!endpoint) {
      const fields = [['nombre','Nombre'],['apellidos','Apellidos'],['email','Correo'],['telefono','Teléfono'],['situacion','Situación'],['necesitas','Servicio'],['ciudad','Ciudad o país'],['caso','Consulta']];
      requestText = 'Solicitud de presupuesto · MMGestoria\n\n' + fields.map(([name,label]) => `${label}: ${data.get(name) || 'No indicado'}`).join('\n') + '\n\nVista previa. Esta solicitud no se ha enviado.\n';
      if (dialog && typeof dialog.showModal === 'function') {
        summary.textContent = requestText;
        dialog.showModal();
      } else {
        setStatus('Esta es una vista previa. El envío aún no está habilitado; no se ha enviado ningún dato.');
      }
      return;
    }
    submit.disabled = true;
    const previous = submit.innerHTML;
    submit.textContent = 'Enviando solicitud…';
    form.setAttribute('aria-busy', 'true');
    setStatus('');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch(endpoint, {
        method: 'POST', body: JSON.stringify(Object.fromEntries(data)),
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        credentials: 'omit', signal: controller.signal
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      if (result.success !== true) throw new Error('Web3Forms did not accept the submission');
      form.reset();
      setStatus('Tu solicitud se ha enviado. Nos pondremos en contacto contigo a través de los datos que has indicado.', 'success');
      status.focus();
    } catch (error) {
      setStatus(error.name === 'AbortError'
        ? 'El servicio no ha confirmado la recepción. Tus datos siguen en el formulario. Comprueba la conexión antes de volver a intentarlo.'
        : 'No se ha podido confirmar el envío. Tus datos siguen en el formulario para que puedas volver a intentarlo.', 'error');
    } finally {
      clearTimeout(timeout);
      submit.disabled = false;
      submit.innerHTML = previous;
      form.removeAttribute('aria-busy');
    }
  });
  dialog?.querySelector('[data-close-dialog]').addEventListener('click', () => dialog.close());
  dialog?.querySelector('[data-download-request]').addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([requestText], { type: 'text/plain;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url; link.download = 'solicitud-MMGestoria.txt';
    document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
})();
