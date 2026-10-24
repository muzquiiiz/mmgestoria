import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

// Execute the actual submission handler against the Web3Forms response contract.
// No real requests are made by these tests.
const app = readFileSync(fileURLToPath(new URL('../src/assets/app.js', import.meta.url)), 'utf8');
const expectedFields = {
  access_key: '00000000-0000-4000-8000-000000000000',
  subject: 'Nueva consulta desde la web',
  from_name: 'Web MMGestoria',
  nombre: 'Prueba', apellidos: 'De integración', email: 'prueba@example.com',
  telefono: '', situacion: 'Particular', necesitas: 'Gestión de inmuebles',
  ciudad: '', caso: 'Consulta de prueba para comprobar el formulario.',
  privacidad: 'He leído la política de privacidad'
};

async function exercise(fetchImplementation, { checked = false } = {}) {
  const listeners = {};
  const status = { textContent: '', className: '', focus() {} };
  const submit = { disabled: false, innerHTML: 'Enviar solicitud', textContent: '' };
  const state = { resets: 0, calls: 0, request: null };
  const service = { value: expectedFields.necesitas, options: [{ value: expectedFields.necesitas }] };
  const form = {
    dataset: { endpoint: 'https://api.web3forms.com/submit' },
    querySelector(selector) {
      return {
        '[name="necesitas"]': service,
        '[name="botcheck"]': { checked },
        '[data-form-status]': status,
        'button[type="submit"]': submit
      }[selector] ?? null;
    },
    querySelectorAll() { return []; },
    addEventListener(name, handler) { listeners[name] = handler; },
    setAttribute() {}, removeAttribute() {},
    reset() { state.resets++; }
  };
  class TestFormData extends Map {
    constructor() { super(Object.entries(expectedFields)); }
  }
  const context = vm.createContext({
    document: {
      querySelector: selector => selector === '[data-budget-form]' ? form : null,
      querySelectorAll: () => []
    },
    window: { location: { search: '' } }, URLSearchParams, FormData: TestFormData,
    AbortController, setTimeout, clearTimeout,
    fetch: async (url, request) => {
      state.calls++; state.request = { url, ...request };
      return fetchImplementation();
    }
  });
  vm.runInContext(app, context);
  await listeners.submit({ preventDefault() {} });
  assert.equal(submit.disabled, false, 'submit button must be released');
  return { ...state, status };
}

const accepted = await exercise(async () => ({ ok: true, status: 200, json: async () => ({ success: true }) }));
assert.equal(accepted.resets, 1);
assert.match(accepted.status.className, /success/);
assert.equal(accepted.request.url, 'https://api.web3forms.com/submit');
assert.equal(accepted.request.method, 'POST');
assert.equal(accepted.request.headers['Content-Type'], 'application/json');
assert.deepEqual(JSON.parse(accepted.request.body), expectedFields);

const refused = await exercise(async () => ({ ok: true, status: 200, json: async () => ({ success: false }) }));
assert.equal(refused.resets, 0, 'a rejected request must keep the form contents');
assert.match(refused.status.className, /error/);

const httpError = await exercise(async () => ({ ok: false, status: 422 }));
assert.equal(httpError.resets, 0);
assert.match(httpError.status.className, /error/);

const invalidJson = await exercise(async () => ({ ok: true, status: 200, json: async () => { throw new SyntaxError('Invalid JSON'); } }));
assert.equal(invalidJson.resets, 0);
assert.match(invalidJson.status.className, /error/);

const networkError = await exercise(async () => { throw new TypeError('Failed to fetch'); });
assert.equal(networkError.resets, 0);
assert.match(networkError.status.className, /error/);

const bot = await exercise(async () => { throw new Error('must not be called'); }, { checked: true });
assert.equal(bot.calls, 0, 'the honeypot must prevent the request');

console.log('PASS: Web3Forms payload, accepted/rejected responses, HTTP failure, malformed JSON, network failure and honeypot.');
