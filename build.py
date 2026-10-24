#!/usr/bin/env python3
"""Generate the complete static MMGestoria website. Python standard library only."""
from pathlib import Path
from html import escape as esc
from urllib.parse import urlparse
from hashlib import sha256
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from content import SERVICES, HOME_FAQ

CONFIG = json.loads((ROOT / 'site.config.json').read_text(encoding='utf-8'))
OUT = ROOT / 'dist'
BASE = CONFIG.get('site_url', '').rstrip('/')
PUBLIC = CONFIG.get('public') is True
EMAIL = CONFIG.get('contact_email', '')
PHONE = CONFIG.get('contact_phone', '')
ACCESS_KEY = CONFIG.get('web3forms_access_key', '')
ENDPOINT = 'https://api.web3forms.com/submit' if ACCESS_KEY else ''
ASSET_VERSION = sha256((ROOT / 'src/assets/app.js').read_bytes()).hexdigest()[:12]
ICON_VERSION = sha256((ROOT / 'src/assets/favicon.svg').read_bytes()).hexdigest()[:12]
OWNER = CONFIG['owner']
BRAND = CONFIG['brand']
BY_SLUG = {s['slug']: s for s in SERVICES}

if BASE and (urlparse(BASE).scheme != 'https' or not urlparse(BASE).netloc or urlparse(BASE).query or urlparse(BASE).fragment):
    raise SystemExit('site_url must be a full HTTPS URL without query or fragment.')
if ACCESS_KEY and not re.fullmatch(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', ACCESS_KEY):
    raise SystemExit('web3forms_access_key must be the UUID supplied by Web3Forms.')
if EMAIL and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', EMAIL):
    raise SystemExit('contact_email is invalid.')
if PHONE and not re.fullmatch(r'\+?[0-9 ()-]{7,22}', PHONE):
    raise SystemExit('contact_phone is invalid.')
if PUBLIC:
    required = ['site_url', 'contact_email', 'web3forms_access_key', 'legal_nif', 'legal_address']
    missing = [k for k in required if not CONFIG.get(k)]
    if missing:
        raise SystemExit('Public release requires confirmed values: ' + ', '.join(missing))

ICONS = {
    'arrow': '<path d="M5 12h14m-6-6 6 6-6 6"/>',
    'diagonal': '<path d="M6 18 18 6M6 6h12v12"/>',
    'check': '<path d="m5 12 4 4L19 6"/>',
    'fiscal': '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3Z"/><path d="M9 7h6M9 11h6M9 15h3"/>',
    'contable': '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 7h8M8 11h2m4 0h2m-8 4h2m4 0h2m-8 3h2m4 0h2"/>',
    'laboral': '<circle cx="9" cy="7" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3m1-17a3 3 0 0 1 0 6m3 11v-3a6 6 0 0 0-2-4"/>',
    'empresa': '<path d="M4 21V5l8-3v19m0-14h8v14M2 21h20M7 7v1m0 3v1m0 3v1m9-5h1m-1 4h1"/>',
    'extranjeria': '<rect x="5" y="2" width="14" height="20" rx="2"/><circle cx="12" cy="10" r="4"/><path d="M8 10h8m-4-4a8 8 0 0 1 0 8 8 8 0 0 1 0-8ZM9 18h6"/>',
    'trafico': '<path d="m4 10 2-6h12l2 6M3 10h18v8H3v-8Zm2 8v3m14-3v3M6 14h2m8 0h2"/>',
    'comunidades': '<path d="M3 21V8l6-4 6 4v13m0-10 6-3v13M2 21h20M7 9h3m-3 4h3m-3 4h3m8-4h1m-1 4h1"/>',
    'gestiones': '<path d="M14 3H5v18h14V8l-5-5Zm0 0v5h5M8 12h8m-8 4h6"/>',
    'ayudas': '<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/><path d="M4 7h3m10 0h3"/>',
    'internacional': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a18 18 0 0 1 0 18 18 18 0 0 1 0-18Zm-8 5h16M4 16h16"/>',
    'shield': '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>',
    'menu': '<path d="M4 7h16M4 12h16M4 17h16"/>',
    'location': '<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 0 1 14 0Z"/><circle cx="12" cy="10" r="2"/>'
}

def icon(name, css=''):
    return f'<svg class="{esc(css)}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS.get(name, ICONS["gestiones"])}</svg>'

def prefix(slug):
    return '../' * len([p for p in slug.split('/') if p]) if slug else './'

def path_to(current, dest=''):
    return prefix(current) + (dest.strip('/') + '/' if dest else '')

def contact_link(current, service=''):
    from urllib.parse import quote
    return path_to(current, 'contacto') + ('?servicio=' + quote(service) if service else '') + '#presupuesto'

def button(text, href, style='primary'):
    return f'<a class="btn btn-{style}" href="{esc(href)}">{esc(text)}{icon("arrow")}</a>'

def textlink(text, href):
    return f'<a class="text-link" href="{esc(href)}">{esc(text)}{icon("arrow")}</a>'

def header(current):
    links = [('servicios','Servicios'),('fiscalidad','Fiscalidad'),('','Cómo trabajamos')]
    items = []
    for slug, text in links:
        href = path_to(current, slug) if slug else path_to(current) + '#como-trabajamos'
        active = ' aria-current="page"' if current == slug and slug else ''
        items.append(f'<a href="{href}"{active}>{text}</a>')
    return f'''<a class="skip-link" href="#contenido">Saltar al contenido</a>
    <header class="site-header"><div class="container header-inner">
      <a class="brand" href="{path_to(current)}" aria-label="MMGestoria · Inicio">
        <img src="{prefix(current)}assets/logo.svg" alt="MMG" width="100" height="29">
        <span class="brand-type"><strong>{BRAND}</strong><small>Gestión integral</small></span>
      </a>
      <button class="menu-toggle" type="button" data-menu-toggle aria-expanded="false" aria-controls="menu-principal" aria-label="Abrir menú">{icon('menu')}</button>
      <nav class="nav" id="menu-principal" aria-label="Navegación principal" data-navigation>{''.join(items)}{button('Pide tu presupuesto',contact_link(current))}</nav>
    </div></header>'''

def footer(current):
    return f'''<footer class="site-footer"><div class="container">
      <div class="footer-main"><div class="footer-brand">
        <a href="{path_to(current)}" aria-label="MMGestoria · Inicio"><img src="{prefix(current)}assets/logo-light.svg" width="150" height="43" alt="MMGestoria" loading="lazy"></a>
        <p>Gestión integral para autónomos, pymes y particulares.<br>Atención directa. Gestiones con criterio.</p>
      </div><nav class="footer-col" aria-label="Servicios en el pie"><strong>Cómo podemos ayudarte</strong>
        <a href="{path_to(current,'servicios/gestion-fiscal')}">Gestión fiscal y contable</a>
        <a href="{path_to(current,'servicios/gestion-laboral')}">Laboral y Seguridad Social</a>
        <a href="{path_to(current,'servicios/extranjeria-y-nacionalidad')}">Extranjería y nacionalidad</a>
        <a href="{path_to(current,'servicios/gestiones-internacionales')}">Gestiones internacionales</a>
        <a href="{path_to(current,'servicios')}">Todos los servicios</a>
      </nav><nav class="footer-col" aria-label="Conoce MMGestoria"><strong>Cerca de tu actividad</strong>
        <a href="{path_to(current,'fiscalidad')}">Régimen común y regímenes forales</a>
        <a href="{path_to(current)}#como-trabajamos">Cómo trabajamos</a>
        <a href="{contact_link(current)}">Pide tu presupuesto</a>
        <a href="{path_to(current)}#preguntas">Preguntas frecuentes</a>
      </nav></div>
      <div class="footer-bottom"><p>© 2026 MMGestoria · {esc(OWNER)}</p><div>
        <a href="{path_to(current,'aviso-legal')}">Aviso legal</a><a href="{path_to(current,'privacidad')}">Privacidad</a><a href="{path_to(current,'cookies')}">Cookies</a>
      </div></div>
    </div></footer>'''

def breadcrumbs(current, title, parent=None):
    links = f'<li><a href="{path_to(current)}">Inicio</a></li>'
    if parent:
        links += f'<li><a href="{path_to(current,parent[0])}">{esc(parent[1])}</a></li>'
    return f'<nav aria-label="Ruta de navegación"><ol class="breadcrumb">{links}<li aria-current="page">{esc(title)}</li></ol></nav>'

def faq(items, current, heading='Antes de empezar,<br>resolvemos tus dudas.'):
    rows = ''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q,a in items)
    return f'''<section class="section faq-section" id="preguntas" aria-labelledby="faq-title"><div class="container faq-layout"><div>
      <p class="eyebrow">Preguntas frecuentes</p><h2 id="faq-title">{heading}</h2><p>Cada caso tiene sus particularidades. Cuéntanos el tuyo y revisamos cómo podemos ayudarte.</p>
      {textlink('Consultar tu caso', contact_link(current))}</div><div class="faq-list">{rows}</div></div></section>'''

def service_card(s, current, i=1, filterable=False):
    attrs = f' data-audiences="{s["audiences"]}"' if filterable else ''
    return f'''<a class="service-card" href="{path_to(current,'servicios/'+s['slug'])}"{attrs}>
      <div class="service-card-top">{icon(s['icon'],'service-icon')}<span class="service-number">{i:02d}</span></div>
      <h3>{esc(s['short'])}</h3><p>{esc(s['card'])}</p><span class="card-link">Ver servicio<span class="sr-only"> de {esc(s['short'])}</span>{icon('diagonal')}</span></a>'''

def cta(current):
    return f'''<section class="wide-cta" aria-labelledby="cta-title"><div class="container"><div><h2 id="cta-title">Cuéntanos qué necesitas.<br>Empezamos por ahí.</h2><p>Una gestión puntual o el día a día de tu actividad. Lo revisamos juntos.</p></div>{button('Pide tu presupuesto',contact_link(current),'white')}</div></section>'''

def form(current, dedicated=False):
    options = ''.join(f'<option value="{esc(s["title"])}">{esc(s["title"])}</option>' for s in SERVICES)
    preview = '' if ENDPOINT else '<p class="preview-notice">Vista previa del formulario. El envío de solicitudes estará disponible próximamente.</p>'
    submit_text = 'Enviar solicitud de presupuesto' if ENDPOINT else 'Revisar solicitud'
    contact_items = ''
    if EMAIL:
        contact_items += f'<a href="mailto:{esc(EMAIL)}">{esc(EMAIL)}</a>'
    if PHONE:
        clean = re.sub(r'[^+0-9]', '', PHONE)
        contact_items += f'<a href="tel:{clean}">{esc(PHONE)}</a>'
    contacts = f'<div class="contact-links">{contact_items}</div>' if contact_items else ''
    privacy = f'<strong>Responsable:</strong> {esc(OWNER)}. <strong>Finalidad:</strong> atender tu consulta y preparar un presupuesto. <strong>Base:</strong> medidas precontractuales a tu petición. Consulta destinatarios, conservación y derechos en la <a href="{path_to(current,"privacidad")}">política de privacidad</a>.'
    return f'''<section class="section contact-section" id="presupuesto" aria-labelledby="contact-title"><div class="container contact-layout"><div class="contact-copy">
      <p class="eyebrow blue">Hablemos de tu caso</p><h2 id="contact-title">Pide tu presupuesto.<br><span class="accent">Con las cosas claras.</span></h2>
      <p>Explica qué necesitas y en qué punto estás. Revisaremos tu consulta para concretar el servicio, la documentación y el presupuesto.</p>
      <ul class="check-list"><li>{icon('check')}Atención directa y seguimiento del encargo</li><li>{icon('check')}Gestión puntual o servicio periódico</li><li>{icon('check')}Alcance y honorarios antes de empezar</li></ul>
      {contacts}<div class="contact-note">{icon('shield')}<span>En este primer contacto no envíes DNI, pasaportes, datos bancarios ni claves. Si hacen falta documentos, acordaremos cómo facilitarlos.</span></div>
    </div><div class="form-card">
      <form data-budget-form data-endpoint="{esc(ENDPOINT)}" method="post"{(' action="'+esc(ENDPOINT)+'"') if ENDPOINT else ''} aria-label="Solicitud de presupuesto">
      <input type="hidden" name="access_key" value="{esc(ACCESS_KEY)}">
      <input type="hidden" name="subject" value="Nueva consulta desde la web">
      <input type="hidden" name="from_name" value="Web MMGestoria">
      <div class="form-grid">
        <div class="field"><label for="nombre">Nombre *</label><input id="nombre" name="nombre" autocomplete="given-name" required maxlength="80" placeholder="Tu nombre"></div>
        <div class="field"><label for="apellidos">Apellidos *</label><input id="apellidos" name="apellidos" autocomplete="family-name" required maxlength="120" placeholder="Tus apellidos"></div>
        <div class="field"><label for="email">Correo electrónico *</label><input id="email" name="email" type="email" autocomplete="email" required maxlength="180" placeholder="nombre@correo.es"></div>
        <div class="field"><label for="telefono">Teléfono <span>(opcional)</span></label><input id="telefono" name="telefono" type="tel" autocomplete="tel" maxlength="30" placeholder="Para contactar contigo"></div>
        <div class="field"><label for="perfil">¿Cuál es tu situación? *</label><select id="perfil" name="situacion" required><option value="">Selecciona una opción</option><option>Autónomo/a</option><option>Empresa</option><option>Particular</option><option>Comunidad de propietarios</option><option>Voy a iniciar una actividad</option><option>Otro</option></select></div>
        <div class="field"><label for="servicio">¿Qué necesitas? *</label><select id="servicio" name="necesitas" required><option value="">Elige un servicio</option>{options}<option>Otro trámite / No lo tengo claro</option></select></div>
        <div class="field wide"><label for="ubicacion">Ciudad o país <span>(opcional)</span></label><input id="ubicacion" name="ciudad" autocomplete="address-level2" maxlength="120" placeholder="Especialmente útil para gestiones internacionales"></div>
        <div class="field wide"><label for="mensaje">Cuéntanos tu caso *</label><textarea id="mensaje" name="caso" required minlength="20" maxlength="4000" rows="4" placeholder="Qué necesitas gestionar, si hay algún plazo y qué te gustaría delegar. Mínimo 20 caracteres."></textarea></div>
      </div><div hidden aria-hidden="true"><label for="botcheck">Deja este campo vacío</label><input id="botcheck" name="botcheck" type="checkbox" tabindex="-1" autocomplete="off"></div>
      <label class="consent" for="privacidad"><input id="privacidad" name="privacidad" type="checkbox" value="He leído la política de privacidad" required><span>He leído la <a href="{path_to(current,'privacidad')}">política de privacidad</a> y solicito que se atienda mi consulta. *</span></label>
      <button class="btn btn-primary" type="submit">{submit_text}{icon('arrow')}</button>
      {preview}<p class="privacy-small">{privacy}</p><p class="form-status" data-form-status role="status" aria-live="polite" aria-atomic="true" tabindex="-1"></p>
      <noscript><p class="no-js-note">{'Puedes enviar el formulario con el botón anterior.' if ENDPOINT else 'El envío de este formulario todavía no está habilitado.'}</p></noscript>
      </form>
    </div></div></section>
    <dialog data-request-dialog aria-labelledby="request-title"><h2 id="request-title">Revisa tu solicitud</h2><p>Esta es una vista previa. No se ha enviado ningún dato. Puedes guardar un resumen en tu dispositivo.</p><div class="dialog-summary" data-request-summary></div><div class="dialog-actions"><button class="btn btn-primary" type="button" data-download-request>Descargar resumen{icon('arrow')}</button><button class="btn btn-secondary" type="button" data-close-dialog>Volver al formulario</button></div></dialog>'''

def globe():
    return '''<svg viewBox="0 0 400 200" fill="none" aria-hidden="true"><g class="globe-path"><ellipse cx="204" cy="100" rx="144" ry="78"/><ellipse cx="204" cy="100" rx="90" ry="78"/><ellipse cx="204" cy="100" rx="34" ry="78"/><path d="M60 100h288M80 61h248M80 139h248"/><path d="M51 150Q193-35 349 61" stroke-width="1.5" stroke-dasharray="4 5"/></g><circle cx="115" cy="88" r="5" fill="currentColor"/><circle cx="232" cy="69" r="5" fill="currentColor"/><circle cx="263" cy="117" r="5" fill="currentColor"/></svg>'''

def home():
    current = ''
    featured = [BY_SLUG[s] for s in ['gestion-fiscal','gestion-contable','gestion-laboral','extranjeria-y-nacionalidad','trafico-y-vehiculos','gestiones-internacionales']]
    cards = ''.join(service_card(s,current,i+1) for i,s in enumerate(featured))
    body = f'''<section class="hero"><div class="container"><div class="hero-grid"><div>
      <p class="eyebrow blue">Gestión fiscal, contable y laboral</p>
      <h1>Gestión integral. <span>Atención cercana.</span></h1>
      <p class="intro">Para autónomos, pymes, empresas y particulares que quieren dedicar tiempo a lo suyo. Nos encargamos de tus gestiones y te explicamos cada paso.</p>
      <div class="hero-actions">{button('Pide tu presupuesto',contact_link(current))}{textlink('Explora los servicios',path_to(current,'servicios'))}</div>
      <p class="hero-caption"><span class="avatar" aria-hidden="true">MMG</span>Atención directa y seguimiento de cada gestión</p>
    </div><div class="hero-art" role="img" aria-label="MMGestoria: gestión fiscal, contable y laboral para dedicar más tiempo a lo tuyo.">
      <div class="art-pattern"></div><span class="art-top">MMG · GESTIÓN INTEGRAL</span><p class="art-word">Más tiempo<br>para lo tuyo.</p>
      <div class="document-stack"><div class="paper-back"></div><div class="paper"><div class="paper-head"><img class="paper-logo" src="./assets/logo.svg" width="83" height="24" alt=""><span>CON TODO EN ORDEN</span></div>
      <div class="paper-line"><span>Fiscalidad</span>{icon('check')}</div><div class="paper-line"><span>Contabilidad</span>{icon('check')}</div><div class="paper-line"><span>Gestión laboral</span>{icon('check')}</div><div class="paper-footer">ATENCIÓN DIRECTA · GESTIÓN INTEGRAL</div></div></div>
      <div class="art-floating">{icon('internacional')}<span>Cerca, aunque estemos lejos.</span></div>
    </div></div><div class="hero-bottom"><p>Atención en el <strong>norte de España</strong> · <a href="./fiscalidad/"><strong>Régimen común · Navarra · País Vasco</strong></a></p><div class="audiences"><span>{icon('check')}Autónomos</span><span>{icon('check')}Pymes</span><span>{icon('check')}Empresas</span><span>{icon('check')}Particulares</span></div></div></div></section>
    <section class="section service-section" id="servicios" aria-labelledby="services-title"><div class="container"><div class="section-head"><div><p class="eyebrow">Cómo podemos ayudarte</p><h2 id="services-title">Tu día a día ya tiene<br>suficientes gestiones.</h2></div><p>Desde las cuentas de tu actividad hasta ese trámite que llevas tiempo aplazando. Encuentra el servicio que necesitas.</p></div><div class="service-grid">{cards}</div><article class="property-feature">{icon("comunidades","service-icon")}<div><h3>Gestión de inmuebles</h3><p>Alquileres, compraventas, Catastro, Registro y documentación de tu inmueble.</p></div>{textlink("Ver gestiones de inmuebles",path_to(current,"servicios/gestion-de-inmuebles"))}</article><div class="service-more"><p>También comunidades, alquileres, ayudas y otras gestiones administrativas.</p>{textlink('Ver todos los servicios','./servicios/')}</div></div></section>
    <section class="section territory" aria-labelledby="territory-title"><div class="container split"><div><p class="eyebrow">Cerca de donde estás</p><h2 id="territory-title">En el norte de España.<br>También entre países.</h2><p>Atención online para gestionar tu actividad estés donde estés. Trabajamos con fiscalidad de régimen común y con los regímenes forales de Navarra y del País Vasco. Si tu trámite conecta varios países, estudiamos la documentación y el alcance.</p>{textlink('Conoce las gestiones internacionales','./servicios/gestiones-internacionales/')}</div><div class="territory-art">{globe()}<div class="territory-label"><span>España</span><span>Unión Europea</span><span>Estados Unidos y otros destinos</span></div></div></div></section>
    <section class="section" id="como-trabajamos" aria-labelledby="steps-title"><div class="container"><div class="section-head"><div><p class="eyebrow">Cómo trabajamos</p><h2 id="steps-title">Primero, entenderte.<br>Después, gestionar.</h2></div><p>Un proceso sencillo para saber qué necesitas y qué vas a contratar.</p></div><div class="steps"><article class="step"><span class="step-num">01 /</span><h3>Nos cuentas tu caso</h3><p>Qué necesitas, en qué situación estás y si hay algún plazo que debamos revisar.</p></article><article class="step"><span class="step-num">02 /</span><h3>Concretamos el servicio</h3><p>Revisamos el alcance y te proponemos un presupuesto con las gestiones incluidas.</p></article><article class="step"><span class="step-num">03 /</span><h3>Nos ponemos con ello</h3><p>Organizamos la documentación, acordamos cómo trabajar y hacemos seguimiento del encargo.</p></article></div></div></section>
    {faq(HOME_FAQ,current)}{form(current)}'''
    return page(current,'Gestión fiscal, contable y laboral | MMGestoria','MMGestoria: gestión fiscal, contable y laboral para autónomos, pymes, empresas y particulares. Régimen común, Navarra y País Vasco. Atención online.',body)

def catalog():
    current='servicios'
    filters=''.join(f'<button type="button" class="filter-btn" data-filter="{v}" aria-pressed="{str(v=="todos").lower()}">{t}</button>' for v,t in [('todos','Todos los servicios'),('autonomos','Autónomos'),('empresas','Empresas'),('particulares','Particulares'),('internacional','Gestiones internacionales')])
    cards=''.join(service_card(s,current,i+1,True) for i,s in enumerate(SERVICES))
    body=f'''<section class="page-hero"><div class="container">{breadcrumbs(current,'Servicios')}<p class="eyebrow blue">Gestión integral</p><h1 class="catalog-title">Simplificamos tus trámites. <span class="accent">Te acompañamos en cada paso.</span></h1><p class="lead">Tu actividad, tu documentación o un trámite entre países. Encuentra el área de servicio y cuéntanos tu caso.</p></div></section><section class="section"><div class="container"><div class="filter-bar" role="group" aria-label="Filtrar servicios por situación">{filters}</div><p class="result-count" data-result-count aria-live="polite">{len(SERVICES)} áreas de servicio</p><div class="service-grid">{cards}</div><p class="scope-note">Los servicios internacionales y las gestiones que requieran una intervención específica se aceptan después de revisar el caso y concretar su alcance.</p></div></section>
    <section class="section service-section" aria-labelledby="sectors-title"><div class="container"><div class="section-head"><div><p class="eyebrow">Sectores y perfiles</p><h2 id="sectors-title">Gestión adaptada<br>a cada actividad.</h2></div><p>Las obligaciones cambian según lo que haces. Revisamos las de tu actividad antes de definir el servicio.</p></div><div class="info-grid">
    <article class="info-block"><h3>Transporte y logística</h3><p>Contabilidad, fiscalidad, plantilla y documentación administrativa vinculada a la actividad.</p></article><article class="info-block"><h3>Comercio y telecomunicaciones</h3><p>Gestión del día a día, facturación, obligaciones fiscales y contratación de personal.</p></article><article class="info-block"><h3>Hostelería y restauración</h3><p>Organización de facturas, cuentas, gestiones laborales y obligaciones periódicas.</p></article><article class="info-block"><h3>Profesionales y servicios</h3><p>Inicio de actividad, gestión fiscal y contable y apoyo administrativo.</p></article><article class="info-block"><h3>Propietarios y comunidades</h3><p>Documentación, cuentas, comunicaciones y gestiones relacionadas con alquileres.</p></article><article class="info-block"><h3>Personas y familias</h3><p>Extranjería, vehículos, certificados, documentación y gestiones internacionales.</p></article></div><p class="scope-note">También puedes consultar por comercio electrónico, oficios, servicios digitales y otras actividades. Se revisan sus necesidades antes de aceptar el encargo.</p></div></section>{cta(current)}'''
    return page(current,'Servicios de gestión integral | MMGestoria','Servicios de MMGestoria: fiscal, contable, laboral, autónomos, extranjería, vehículos, inmuebles, comunidades, subvenciones y gestiones internacionales.',body)

def service_page(s):
    current='servicios/'+s['slug']
    items=''.join(f'<article class="detail-item">{icon("check")}<div><h3>{esc(t)}</h3><p>{esc(d)}</p></div></article>' for t,d in s['items'])
    checklist=''.join(f'<li>{icon("check")}{esc(t)}</li>' for t in s['prepare'])
    scope=f'<p class="scope-note">{esc(s["scope"])}</p>' if s.get('scope') else ''
    related=''.join(f'<a class="related-card" href="{path_to(current,"servicios/"+slug)}">{esc(BY_SLUG[slug]["title"])}{icon("arrow")}</a>' for slug in s['related'])
    body=f'''<section class="page-hero"><div class="container">{breadcrumbs(current,s['title'],('servicios','Servicios'))}<div class="service-hero-grid"><div><p class="eyebrow blue">{esc(s['title'])}</p><h1>{esc(s['headline'])}</h1><p class="lead">{esc(s['lead'])}</p><div class="hero-actions">{button('Consultar este servicio',contact_link(current,s['title']))}</div></div><div class="detail-emblem" aria-hidden="true">{icon(s['icon'])}<span>MMGestoria · Gestión integral</span></div></div></div></section>
    <section class="section"><div class="container detail-layout"><div class="detail-copy"><p class="eyebrow">El servicio, al detalle</p><h2>Cómo podemos ayudarte.</h2><p>{esc(s['intro'])}</p><p>{esc(s['intro2'])}</p><div class="detail-list">{items}</div>{scope}</div><aside class="aside-card"><p class="eyebrow">Empecemos por tu caso</p><h3>Un presupuesto<br>con el alcance claro.</h3><p>Para la primera valoración, cuéntanos:</p><ul class="check-list">{checklist}</ul>{button('Pide tu presupuesto',contact_link(current,s['title']),'white')}<p>El envío de una consulta no implica contratar un servicio.</p></aside></div></section>
    {faq(s['faq'],current,'Sobre este servicio,<br>sin dudas pendientes.')}<section class="section related" aria-labelledby="related-title"><div class="container"><div class="section-head"><div><p class="eyebrow">Quizá también necesites</p><h2 id="related-title">Gestiones relacionadas.</h2></div></div><div class="related-grid">{related}</div></div></section>{cta(current)}'''
    return page(current,s['title']+' | MMGestoria',s['description'],body,service=s)

def fiscality():
    current='fiscalidad'
    regimes=[
        ('Régimen común','Gestión de obligaciones tributarias ante la Agencia Estatal de Administración Tributaria y otras administraciones competentes, según tu actividad.'),
        ('Navarra','Revisión y gestión de las obligaciones que correspondan ante la Hacienda Foral de Navarra.'),
        ('País Vasco','Gestión fiscal ante las haciendas forales de Álava, Bizkaia y Gipuzkoa, según la administración y las obligaciones aplicables a tu caso.')
    ]
    regime_cards=''.join(f'<article class="info-block"><h3>{esc(t)}</h3><p>{esc(d)}</p></article>' for t,d in regimes)
    blocks=[('Autónomos y profesionales','Organizamos ingresos y gastos, revisamos obligaciones y preparamos las declaraciones que correspondan a tu actividad.','gestion-fiscal'),('Pymes y empresas','Coordinamos la gestión fiscal y contable de la empresa y, cuando se contrate, la gestión laboral.','autonomos-y-pymes'),('Notificaciones y documentación','Revisamos las comunicaciones de la AEAT o de la hacienda foral correspondiente y la documentación necesaria para valorar una respuesta.','gestiones-administrativas'),('Cambio de gestoría','Identificamos declaraciones, registros y documentación pendiente para organizar el traspaso desde tu gestoría anterior.','gestion-contable')]
    cards=''.join(f'<article class="info-block"><h3>{t}</h3><p>{d}</p>{textlink("Ver servicio",path_to(current,"servicios/"+s))}</article>' for t,d,s in blocks)
    items=[('¿Trabajáis con régimen común, Navarra y País Vasco?', 'Sí. Trabajamos con fiscalidad de régimen común y con los regímenes forales de Navarra y del País Vasco. Revisamos la situación de cada cliente antes de concretar el servicio.'),('¿Cómo revisáis qué obligaciones corresponden a mi caso?', 'Estudiamos tu actividad, tu situación y la documentación disponible para identificar la administración y las gestiones que deban incluirse en el encargo.'),('¿Puedo contratar el servicio de gestión desde otra ciudad?', 'Sí. La atención online permite compartir la documentación y organizar el servicio a distancia. Si un trámite requiere una actuación presencial, concretamos cómo realizarla al estudiar el caso.')]
    body=f'''<section class="page-hero"><div class="container">{breadcrumbs(current,'Fiscalidad')}<p class="eyebrow blue">Régimen común · Navarra · País Vasco</p><h1>Gestión fiscal<br>en régimen común y foral.</h1><p class="lead">Para autónomos, pymes, empresas y particulares. Revisamos tus obligaciones y las particularidades del régimen fiscal que te corresponda.</p><div class="hero-actions">{button('Consultar tu caso',contact_link(current,'Gestión fiscal'))}</div></div></section><section class="section"><div class="container"><div class="catalog-intro"><p class="eyebrow">Fiscalidad adaptada a tu situación</p><h2>Revisamos dónde tributas<br>y qué necesitas gestionar.</h2><p>Antes de preparar las declaraciones, revisamos la situación de tu actividad, la administración competente y la documentación disponible. Concretamos el trabajo a partir de esas obligaciones, tanto si necesitas gestión habitual como una consulta puntual.</p><p>Trabajamos con fiscalidad en régimen común y en los regímenes forales de Navarra y del País Vasco. Organizamos la atención online para que puedas compartir tu documentación y consultar tus dudas a distancia.</p></div><div class="regime-grid">{regime_cards}</div></div></section><section class="section service-section" aria-labelledby="fiscal-services-title"><div class="container"><p class="eyebrow">Del régimen fiscal a la gestión diaria</p><h2 id="fiscal-services-title">Un servicio adaptado<br>a tu actividad.</h2><div class="info-grid">{cards}</div></div></section>{faq(items,current,'Sobre la gestión fiscal<br>de tu actividad.')}{cta(current)}'''
    return page(current,'Gestión fiscal: régimen común, Navarra y País Vasco | MMGestoria','Gestión fiscal para autónomos, pymes, empresas y particulares en régimen común y en los regímenes forales de Navarra y País Vasco. MMGestoria.',body)

def contact():
    current='contacto'
    body=f'''<section class="page-hero"><div class="container">{breadcrumbs(current,'Contacto')}<p class="eyebrow blue">Contacto · MMGestoria</p><h1>Empezamos por tu caso.</h1><p class="lead">Cuéntanos qué necesitas gestionar. Una consulta inicial para concretar el alcance del trabajo y preparar tu presupuesto.</p></div></section>{form(current,True)}'''
    return page(current,'Contacto y presupuesto de gestión | MMGestoria','Pide presupuesto a MMGestoria para gestión fiscal, contable, laboral o gestiones personales e internacionales. Atención directa y seguimiento del encargo.',body)

def legal(kind):
    title={'aviso-legal':'Aviso legal','privacidad':'Política de privacidad','cookies':'Política de cookies'}[kind]
    address=esc(CONFIG.get('legal_address') or 'Santa Eulalia Somera, La Rioja, España')
    nif=f'<p>NIF: {esc(CONFIG["legal_nif"])}</p>' if CONFIG.get('legal_nif') else ''
    email=f'<a href="mailto:{esc(EMAIL)}">{esc(EMAIL)}</a>' if EMAIL else f'<a href="{contact_link(kind)}">Formulario de contacto</a>'
    notice='' if PUBLIC else '<p class="scope-note">Esta web está en fase de preparación.' + (' El envío del formulario no está habilitado. Los datos que escribas en él no se transmiten a MMGestoria.' if not ENDPOINT else '') + '</p>'
    if kind=='aviso-legal':
        content=f'''<h2>Titular de la web</h2><p>Nombre comercial: {BRAND}. Titular: {esc(OWNER)}.</p>{nif}<p>Domicilio: {address}.</p><p>Contacto: {email}</p><h2>Objeto de la web</h2><p>La web presenta servicios de gestión administrativa para autónomos, empresas y particulares. La información describe áreas de trabajo y no sustituye el estudio individual de un expediente.</p><h2>Contratación de servicios</h2><p>Una consulta o una solicitud de presupuesto no implica la aceptación de un encargo. El trabajo, los honorarios, las tasas y los gastos de terceros se concretan antes de contratar. Las gestiones internacionales y las actuaciones que requieran una habilitación específica se valoran de forma individual.</p><h2>Uso de los contenidos</h2><p>Los contenidos y elementos de marca se facilitan para la consulta de esta web. Su uso no autoriza a presentar a terceros como representantes de MMGestoria.</p><h2>Enlaces y disponibilidad</h2><p>Los enlaces a otras webs, cuando existan, remiten a servicios con sus propias condiciones. Los trámites dependen de los requisitos, canales y decisiones de la administración u organismo correspondiente.</p>'''
    elif kind=='privacidad':
        processor=f'''<h2>Servicio de recepción del formulario</h2><p>Utilizamos Web3Forms, operado por Web3Creative, para recibir y entregar las consultas por correo. Su política informa de operaciones desde India y de infraestructura que puede tratar datos en varias regiones. El proveedor indica que aplica garantías para transferencias internacionales, incluidas cláusulas contractuales tipo, en su <a href="https://web3forms.com/dpa" target="_blank" rel="noopener noreferrer">acuerdo de tratamiento</a>. Su <a href="https://web3forms.com/privacy" target="_blank" rel="noopener noreferrer">política de privacidad</a> describe los proveedores de infraestructura y filtrado antispam, así como una conservación de solicitudes de hasta tres años, salvo plazos menores del plan o borrado anterior.</p>''' if ENDPOINT else '<h2>Formulario en esta versión</h2><p>El envío está deshabilitado. Los datos escritos permanecen en la página abierta; no se guardan en cookies ni en el almacenamiento local del navegador.</p>'

        content=f'''<h2>Responsable del tratamiento</h2><p>{esc(OWNER)}, titular de {BRAND}. Domicilio: {address}.</p><p>Contacto para cuestiones de privacidad: {email}</p><h2>Finalidad y datos solicitados</h2><p>Utilizamos tus datos de identificación y contacto y el contenido de tu consulta para atenderla y preparar el presupuesto solicitado. El teléfono y la ubicación son opcionales. No se solicitan documentos de identidad, datos bancarios ni credenciales.</p><h2>Base del tratamiento</h2><p>La atención de una solicitud de presupuesto se basa en la adopción de medidas precontractuales a petición de la persona interesada, de acuerdo con el artículo 6.1.b del Reglamento General de Protección de Datos. Tus datos no se incorporan a campañas de publicidad por enviar una consulta.</p><h2>Destinatarios</h2><p>Los datos se dirigen al titular de MMGestoria. Web3Forms y los proveedores necesarios para la recepción y entrega de la consulta intervienen en su tratamiento para prestar el servicio. No se ceden datos para que terceros realicen publicidad.</p>{processor}<h2>Conservación</h2><p>Las consultas se conservan durante el tiempo necesario para atender la solicitud y gestionar el presupuesto. Si se contrata un servicio, su documentación se conserva conforme a las obligaciones aplicables al encargo. Las consultas que no den lugar a contratación se suprimen cuando dejan de ser necesarias, sin perjuicio de las responsabilidades legales que puedan resultar.</p><h2>Tus derechos</h2><p>Puedes solicitar acceso, rectificación, supresión, oposición, limitación o portabilidad cuando correspondan, a través del contacto del responsable. También puedes presentar una reclamación ante la <a href="https://www.aepd.es/" target="_blank" rel="noopener noreferrer">Agencia Española de Protección de Datos</a>.</p><h2>Navegación</h2><p>Este sitio no incorpora analítica, píxeles publicitarios, mapas incrustados ni fuentes de terceros. El proveedor de alojamiento puede tratar registros técnicos de acceso para prestar y proteger el servicio.</p>'''
    else:
        content='''<h2>Cookies en este sitio</h2><p>El código de esta web no instala cookies propias de analítica, publicidad o seguimiento. Tampoco utiliza almacenamiento local para registrar la navegación o las consultas.</p><h2>Recursos de terceros</h2><p>Los elementos gráficos, iconos y estilos se sirven con la propia web. No se cargan mapas, vídeos, fuentes o herramientas de medición de terceros al visitar las páginas.</p><h2>Alojamiento y formulario</h2><p>El alojamiento puede emplear mecanismos técnicos para seguridad o control de acceso. En la versión de revisión privada, el acceso puede estar sujeto a las condiciones del proveedor de alojamiento. La comunicación con Web3Forms se produce al solicitar el envío del formulario. No se cargan sus herramientas de analítica o su panel en esta web.</p><h2>Cambios en la web</h2><p>Si se incorporan herramientas que utilicen cookies o tecnologías de seguimiento, esta información y las opciones de consentimiento deberán adaptarse antes de su activación.</p><h2>Más información</h2><p>Puedes consultar la <a href="https://www.aepd.es/guias/guia-cookies.pdf" target="_blank" rel="noopener noreferrer">guía sobre cookies de la AEPD</a> y las opciones de privacidad de tu navegador.</p>'''
    body=f'<section class="page-hero"><div class="container">{breadcrumbs(kind,title)}<p class="eyebrow blue">Información del sitio</p><h1>{title}</h1></div></section><div class="container"><article class="legal-body">{notice}{content}</article></div>'
    return page(kind,title+' | MMGestoria','Información de MMGestoria sobre '+title.lower()+'. Titular, condiciones de uso y tratamiento de datos.',body,noindex=True)

PAGES=[]

def page(slug,title,description,body,service=None,noindex=False):
    pfx=prefix(slug)
    robots='index,follow' if PUBLIC and not noindex else 'noindex,follow'
    absurl=BASE+('/'+slug+'/' if slug else '/') if BASE else ''
    canonical=f'<link rel="canonical" href="{esc(absurl)}"><meta property="og:url" content="{esc(absurl)}">' if absurl else ''
    ogimage=f'<meta property="og:image" content="{esc(BASE)}/assets/social-card.png"><meta name="twitter:image" content="{esc(BASE)}/assets/social-card.png">' if BASE else ''
    verification=f'<meta name="google-site-verification" content="{esc(CONFIG["google_verification"])}">' if CONFIG.get('google_verification') else ''
    schema={'@context':'https://schema.org','@graph':[{'@type':'Organization','name':BRAND,'founder':{'@type':'Person','name':OWNER},'areaServed':{'@type':'Country','name':'España'}}]}
    org=schema['@graph'][0]
    if BASE:
        org.update({'@id':BASE+'/#organization','url':BASE+'/','logo':BASE+'/assets/logo.svg'})
        schema['@graph'].append({'@type':'WebSite','@id':BASE+'/#website','name':BRAND,'url':BASE+'/','inLanguage':'es-ES'})
    if EMAIL:org['email']=EMAIL
    if PHONE:org['telephone']=PHONE
    if service:
        node={'@type':'Service','name':service['title'],'description':service['description'],'provider':{'@id':BASE+'/#organization'} if BASE else {'@type':'Organization','name':BRAND},'inLanguage':'es-ES'}
        if absurl:node['url']=absurl
        schema['@graph'].append(node)
    if slug and BASE:
        crumb=[{'@type':'ListItem','position':1,'name':'Inicio','item':BASE+'/'}]
        if slug.startswith('servicios/'):
            crumb.append({'@type':'ListItem','position':2,'name':'Servicios','item':BASE+'/servicios/'})
        crumb.append({'@type':'ListItem','position':len(crumb)+1,'name':service['title'] if service else title.split(' | ')[0],'item':absurl})
        schema['@graph'].append({'@type':'BreadcrumbList','itemListElement':crumb})
    jsonld=json.dumps(schema,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    html=f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="robots" content="{robots}">
<meta name="theme-color" content="#153f9e"><meta name="color-scheme" content="light"><meta name="referrer" content="strict-origin-when-cross-origin">
<meta property="og:type" content="website"><meta property="og:locale" content="es_ES"><meta property="og:site_name" content="{BRAND}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta name="twitter:card" content="summary_large_image">{canonical}{ogimage}{verification}
<link rel="icon" href="{pfx}assets/favicon.svg?v={ICON_VERSION}" type="image/svg+xml"><link rel="icon" href="{pfx}assets/favicon.ico?v={ICON_VERSION}" sizes="any"><link rel="apple-touch-icon" href="{pfx}assets/apple-touch-icon.png?v={ICON_VERSION}"><link rel="manifest" href="{pfx}site.webmanifest"><link rel="stylesheet" href="{pfx}assets/styles.css">
<script type="application/ld+json">{jsonld}</script><script src="{pfx}assets/app.js?v={ASSET_VERSION}" defer></script></head><body>{header(slug)}<main id="contenido">{body}</main>{footer(slug)}</body></html>'''
    PAGES.append((slug,html,not noindex))
    return html

def not_found():
    body=f'<section class="not-found"><div class="container"><p class="eyebrow blue">Error 404</p><h1>Esta página no está aquí.</h1><p>Puedes volver al inicio o consultar los servicios para encontrar la gestión que necesitas.</p>{button("Volver al inicio","./")}</div></section>'
    html=page('','Página no encontrada | MMGestoria','La página solicitada no existe. Consulta los servicios de MMGestoria o vuelve al inicio.',body,noindex=True)
    PAGES.pop()
    # A 404 can be served for any missing URL. Root-relative paths must include a GitHub project prefix.
    basepath=urlparse(BASE).path.rstrip('/')+'/' if BASE else '/'
    html=html.replace('href="./','href="'+basepath).replace('src="./','src="'+basepath)
    return html

def build():
    OUT.mkdir(exist_ok=True)
    # Remove generated output only; preserve source and user-supplied assets.
    for p in OUT.iterdir():
        if p.is_dir():shutil.rmtree(p)
        else:p.unlink()
    shutil.copytree(ROOT/'src'/'assets',OUT/'assets')
    home();catalog()
    for s in SERVICES:service_page(s)
    fiscality();contact()
    for kind in ['aviso-legal','privacidad','cookies']:legal(kind)
    for slug,html,indexable in PAGES:
        directory=OUT/slug
        directory.mkdir(exist_ok=True,parents=True)
        (directory/'index.html').write_text(html,encoding='utf-8')
    (OUT/'404.html').write_text(not_found(),encoding='utf-8')
    (OUT/'.nojekyll').touch()
    if PUBLIC:
        ns='http://www.sitemaps.org/schemas/sitemap/0.9'
        ET.register_namespace('',ns)
        urlset=ET.Element('{'+ns+'}urlset')
        for slug,html,indexable in PAGES:
            if indexable:
                u=ET.SubElement(urlset,'{'+ns+'}url')
                ET.SubElement(u,'{'+ns+'}loc').text=BASE+('/'+slug+'/' if slug else '/')
        ET.ElementTree(urlset).write(OUT/'sitemap.xml',encoding='utf-8',xml_declaration=True)
        robots='User-agent: *\nAllow: /\nSitemap: '+BASE+'/sitemap.xml\n'
        domain=urlparse(BASE).netloc
        if not domain.endswith('.github.io') and not domain.endswith('.chatgpt.site'):
            (OUT/'CNAME').write_text(domain+'\n')
    else:
        robots='User-agent: *\nDisallow: /\n'
    (OUT/'robots.txt').write_text(robots,encoding='utf-8')
    manifest={'name':BRAND+' · Gestión integral','short_name':BRAND,'lang':'es','start_url':'./','scope':'./','display':'browser','background_color':'#fafaf8','theme_color':'#153f9e','icons':[{'src':'assets/icon-192.png','sizes':'192x192','type':'image/png'},{'src':'assets/icon-512.png','sizes':'512x512','type':'image/png'}]}
    (OUT/'site.webmanifest').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Built {len(PAGES)+1} HTML pages · mode: '+('PUBLIC' if PUBLIC else 'PRIVATE PREVIEW'))

if __name__=='__main__':build()
